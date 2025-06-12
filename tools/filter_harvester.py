"""
filter_harvester.py

This module is responsible for extracting, parsing, and structuring Gmail filters.

It connects to the Gmail API, fetches all user-defined filters, and converts them
into a structured format that can be used for analysis or bulk processing. This is
a key component of the filter-first strategy, allowing the system to understand
and replicate user-defined email routing before applying LLM-based analysis.

Key Functions:
-   fetch_and_parse_filters: Extracts filters via the Gmail API.
-   _parse_criteria: Converts filter criteria into a Gmail search query string.
-   _parse_action: Extracts actions like adding/removing labels or marking as spam.
-   _get_label_name_from_id: Maps label IDs to human-readable label names.

Dependencies:
-   google-api-python-client
-   google-auth-oauthlib
-   A valid config/credentials.json and config/token.json from the Google Cloud project.

Usage:
    from tools.filter_harvester import fetch_and_parse_filters
    from gmail_api_utils import get_gmail_service

    service = get_gmail_service()
    if service:
        structured_filters = fetch_and_parse_filters(service)
        # Further processing...
"""

import logging
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path to import log_config and exceptions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_config import get_logger
from exceptions import GmailAPIError, FilterProcessingError, wrap_gmail_api_call

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

# Initialize logger using standardized config
logger = get_logger(__name__)

# Cache for label ID to name mapping to reduce API calls
_label_id_to_name_cache = {}
# Cache for label name to ID mapping for reverse lookups
_label_name_to_id_cache = {}


# Global cache for filters to avoid repeated API calls within a single run
_filter_cache = None


def get_and_cache_filters(service: Resource, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches filters and caches them globally to prevent redundant API calls.

    Args:
        service (Resource): The authenticated Gmail API service object.
        force_refresh (bool): If True, fetches filters from the API even if cached.

    Returns:
        List[Dict[str, Any]]: A list of structured filter data.
    """
    global _filter_cache
    if _filter_cache is None or force_refresh:
        logger.info("Fetching and caching filters from Gmail API...")
        _filter_cache = fetch_and_parse_filters(service)
    else:
        logger.info("Using cached filters.")
    return _filter_cache


def _get_label_name_from_id(service: Resource, label_id: str) -> Optional[str]:
    """
    Retrieves the name of a label from its ID, using a cache to avoid redundant API calls.

    Args:
        service (Resource): The authenticated Gmail API service object.
        label_id (str): The ID of the label to look up.

    Returns:
        Optional[str]: The name of the label, or None if an error occurs or the label is not found.
    """
    if label_id in _label_id_to_name_cache:
        return _label_id_to_name_cache[label_id]

    # Handle system labels which don't need an API call
    system_labels = {
        "INBOX": "INBOX",
        "SPAM": "SPAM",
        "TRASH": "TRASH",
        "UNREAD": "UNREAD",
        "STARRED": "STARRED",
        "IMPORTANT": "IMPORTANT",
        "SENT": "SENT",
        "DRAFT": "DRAFT",
        "CATEGORY_PERSONAL": "CATEGORY_PERSONAL",
        "CATEGORY_SOCIAL": "CATEGORY_SOCIAL",
        "CATEGORY_PROMOTIONS": "CATEGORY_PROMOTIONS",
        "CATEGORY_UPDATES": "CATEGORY_UPDATES",
        "CATEGORY_FORUMS": "CATEGORY_FORUMS",
    }
    if label_id in system_labels:
        return system_labels[label_id]

    try:
        label = wrap_gmail_api_call(
            service.users().labels().get(userId='me', id=label_id).execute,
            operation=f"get label name for ID {label_id}"
        )
        label_name = label.get('name')
        if label_name:
            _label_id_to_name_cache[label_id] = label_name
        return label_name
    except GmailAPIError as e:
        e.log_error(logger)
        return None


def _get_label_id_from_name(service: Resource, label_name: str) -> Optional[str]:
    """
    Retrieves the ID of a label from its name, using a cache to avoid redundant API calls.

    Args:
        service (Resource): The authenticated Gmail API service object.
        label_name (str): The name of the label to look up.

    Returns:
        Optional[str]: The ID of the label, or None if an error occurs or the label is not found.
    """
    if label_name in _label_name_to_id_cache:
        return _label_name_to_id_cache[label_name]

    # Handle system labels which have known IDs
    system_labels = {
        "INBOX": "INBOX",
        "SPAM": "SPAM", 
        "TRASH": "TRASH",
        "UNREAD": "UNREAD",
        "STARRED": "STARRED",
        "IMPORTANT": "IMPORTANT",
        "SENT": "SENT",
        "DRAFT": "DRAFT",
        "CATEGORY_PERSONAL": "CATEGORY_PERSONAL",
        "CATEGORY_SOCIAL": "CATEGORY_SOCIAL", 
        "CATEGORY_PROMOTIONS": "CATEGORY_PROMOTIONS",
        "CATEGORY_UPDATES": "CATEGORY_UPDATES",
        "CATEGORY_FORUMS": "CATEGORY_FORUMS",
    }
    if label_name in system_labels:
        return system_labels[label_name]

    try:
        # Get all labels and find the one with matching name
        labels_result = wrap_gmail_api_call(
            service.users().labels().list(userId='me').execute,
            operation="list labels for name lookup"
        )
        
        for label in labels_result.get('labels', []):
            if label.get('name') == label_name:
                label_id = label.get('id')
                if label_id:
                    _label_name_to_id_cache[label_name] = label_id
                    # Also cache the reverse mapping
                    _label_id_to_name_cache[label_id] = label_name
                return label_id
        
        logger.warning(f"Label '{label_name}' not found")
        return None
        
    except GmailAPIError as e:
        e.log_error(logger)
        return None


def _parse_criteria(criteria: Dict[str, Any]) -> str:
    """
    Converts a filter's criteria object into a Gmail search query string.

    Handles various fields including complex Gmail search operators like size,
    date ranges, AND/OR conditions, attachments, and other advanced operators.

    Args:
        criteria (Dict[str, Any]): The criteria part of a Gmail filter resource.

    Returns:
        str: A string formatted as a Gmail search query.
    """
    query_parts = []
    
    # Map Gmail API criteria fields to search operators
    field_mappings = {
        'from': 'from',
        'to': 'to',
        'subject': 'subject',
        'hasTheWord': '',  # Direct query text
        'doesNotHaveTheWord': '-',  # Negation prefix
        'size': 'size',
        'sizeComparison': '',  # Used with size
        'hasAttachment': 'has',
        'excludeChats': '',  # Special handling
        'query': ''  # Raw query string
    }
    
    # Handle size with comparison operators
    if 'size' in criteria and 'sizeComparison' in criteria:
        size_val = criteria['size']
        comparison = criteria['sizeComparison']
        if comparison == 'larger':
            query_parts.append(f'larger:{size_val}')
        elif comparison == 'smaller':
            query_parts.append(f'smaller:{size_val}')
        else:
            query_parts.append(f'size:{size_val}')
    elif 'size' in criteria:
        query_parts.append(f'size:{criteria["size"]}')
    
    # Handle attachment criteria
    if 'hasAttachment' in criteria:
        if criteria['hasAttachment']:
            query_parts.append('has:attachment')
        else:
            query_parts.append('-has:attachment')
    
    # Handle exclude chats
    if 'excludeChats' in criteria and criteria['excludeChats']:
        query_parts.append('-in:chats')
    
    # Process other standard fields
    for key, value in criteria.items():
        if key in ['size', 'sizeComparison', 'hasAttachment', 'excludeChats']:
            continue  # Already handled above
            
        if key in field_mappings:
            prefix = field_mappings[key]
            
            if key == 'hasTheWord':
                # Direct query text, may contain complex operators
                if isinstance(value, str):
                    # Handle parentheses for OR conditions
                    if '(' in value or ')' in value or ' OR ' in value.upper():
                        query_parts.append(f'({value})')
                    else:
                        query_parts.append(value)
            elif key == 'doesNotHaveTheWord':
                # Negation - wrap complex queries in parentheses
                if isinstance(value, str):
                    if ' ' in value or '(' in value:
                        query_parts.append(f'-({value})')
                    else:
                        query_parts.append(f'-{value}')
            elif key == 'query':
                # Raw query string - use as-is
                query_parts.append(str(value))
            else:
                # Standard field:value format
                formatted_value = str(value)
                if ' ' in formatted_value or '"' in formatted_value:
                    # Escape quotes and wrap in quotes
                    escaped_value = formatted_value.replace('"', '\\"')
                    query_parts.append(f'{prefix}:"{escaped_value}"')
                else:
                    query_parts.append(f'{prefix}:{formatted_value}')
    
    return ' '.join(query_parts)


def _parse_action(service: Resource, action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a filter's action object to extract label modifications and other actions.

    Handles all Gmail filter actions including labels, archiving, marking as read/important,
    forwarding, and deletion.

    Args:
        service (Resource): The authenticated Gmail API service object.
        action (Dict[str, Any]): The action part of a Gmail filter resource.

    Returns:
        Dict[str, Any]: A structured dictionary of actions.
    """
    parsed = {
        "add_labels": [],
        "remove_labels": [],
        "mark_as_spam": False,
        "mark_as_read": action.get("markAsRead", False),
        "mark_as_important": action.get("markAsImportant", False),
        "never_spam": action.get("neverSpam", False),
        "archive": False,
        "delete": action.get("delete", False),
        "forward": action.get("forward", ""),
    }

    # Handle label additions
    if "addLabelIds" in action:
        add_label_ids = action["addLabelIds"]
        parsed["add_labels"] = []
        
        for label_id in add_label_ids:
            if label_id == "SPAM":
                parsed["mark_as_spam"] = True
            else:
                label_name = _get_label_name_from_id(service, label_id)
                if label_name:
                    parsed["add_labels"].append(label_name)

    # Handle label removals  
    if "removeLabelIds" in action:
        remove_label_ids = action["removeLabelIds"]
        parsed["remove_labels"] = []
        
        for label_id in remove_label_ids:
            if label_id == "INBOX":
                parsed["archive"] = True
            else:
                label_name = _get_label_name_from_id(service, label_id)
                if label_name:
                    parsed["remove_labels"].append(label_name)

    # Clean up empty lists for cleaner output
    if not parsed["add_labels"]:
        del parsed["add_labels"]
    if not parsed["remove_labels"]:
        del parsed["remove_labels"]
    if not parsed["forward"]:
        del parsed["forward"]

    return parsed


def fetch_and_parse_filters(service: Resource) -> List[Dict[str, Any]]:
    """
    Fetches all Gmail filters and parses them into a structured list.

    Each item in the list contains the filter's ID, its search query,
    and the actions it performs.

    Args:
        service (Resource): The authenticated Gmail API service object.

    Returns:
        List[Dict[str, Any]]: A list of structured filter data.
    """
    structured_filters = []
    try:
        results = wrap_gmail_api_call(
            service.users().settings().filters().list(userId='me').execute,
            operation="fetch Gmail filters"
        )
        filters = results.get('filter', [])

        if not filters:
            logger.info("No user-defined filters found.")
            return []

        logger.info(f"Found {len(filters)} filters. Parsing...")

        for f in filters:
            filter_id = f.get("id")
            criteria = f.get("criteria", {})
            action = f.get("action", {})

            if not criteria:
                logger.warning(f"Filter {filter_id} has no criteria, skipping.")
                continue

            try:
                query = _parse_criteria(criteria)
                parsed_action = _parse_action(service, action)

                structured_filters.append({
                    "id": filter_id,
                    "query": query,
                    "action": parsed_action,
                    "raw_criteria": criteria,
                    "raw_action": action,
                })
            except Exception as e:
                raise FilterProcessingError(
                    f"Failed to parse filter {filter_id}",
                    filter_id=filter_id,
                    filter_criteria=str(criteria),
                    operation="parse_filter"
                ) from e
        
        logger.info(f"Successfully parsed {len(structured_filters)} filters.")

    except GmailAPIError as e:
        e.log_error(logger)
    except FilterProcessingError as e:
        e.log_error(logger)
    
    return structured_filters


def apply_existing_filters_to_backlog(service: Resource, email_ids: List[str] = None,
                                    progress_callback=None, use_server_side=True) -> Dict[str, Any]:
    """
    Applies existing Gmail filters using server-side batch operations for maximum efficiency.
    This is a complete refactor for server-side processing as per the remediation plan.

    Args:
        service (Resource): The authenticated Gmail API service object.
        email_ids (List[str], optional): Legacy parameter, now ignored for server-side processing.
        progress_callback: Optional callback function for progress updates.
        use_server_side (bool): If False, this function does nothing.

    Returns:
        Dict[str, Any]: Statistics about filter applications including:
            - processed_count: Total number of messages processed across all filters.
            - filter_stats: Dictionary of filter ID -> count of messages it affected.
            - server_side_processed: Same as processed_count.
            - remaining_ids: Always empty, as this function processes the entire backlog.
    """
    if not use_server_side:
        logger.warning("Server-side processing is disabled. Skipping filter application.")
        return {"processed_count": 0, "filter_stats": {}, "server_side_processed": 0, "remaining_ids": []}

    logger.info("Starting server-side filter application for the entire backlog.")

    # Use the cached filter fetcher
    structured_filters = get_and_cache_filters(service)
    if not structured_filters:
        logger.info("No user-defined filters found. No server-side processing will occur.")
        return {"processed_count": 0, "filter_stats": {}, "server_side_processed": 0, "remaining_ids": []}

    total_processed_count = 0
    filter_stats = {}

    for i, filter_data in enumerate(structured_filters):
        filter_id = filter_data['id']
        query = filter_data['query']
        action = filter_data['action']
        
        if not query:
            logger.warning(f"Filter {filter_id} has an empty query. Skipping.")
            continue

        if progress_callback:
            progress = (i / len(structured_filters)) * 100
            progress_callback(f"Processing filter {i+1}/{len(structured_filters)}: '{query}'", progress)

        try:
            logger.info(f"Executing query for filter '{filter_id}': {query}")
            
            # 1. Find all matching message IDs for the filter's query
            message_ids = []
            page_token = None
            while True:
                response = wrap_gmail_api_call(
                    service.users().messages().list(userId='me', q=query, pageToken=page_token).execute,
                    operation=f"list messages for filter '{query}'"
                )
                messages = response.get('messages', [])
                if messages:
                    message_ids.extend([msg['id'] for msg in messages])
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            if not message_ids:
                logger.info(f"Filter '{filter_id}' did not match any messages.")
                continue

            logger.info(f"Filter '{filter_id}' matched {len(message_ids)} messages. Applying actions...")

            # 2. Determine actions (convert label names to IDs)
            add_label_ids = [_get_label_id_from_name(service, name) for name in action.get('add_labels', [])]
            remove_label_ids = [_get_label_id_from_name(service, name) for name in action.get('remove_labels', [])]
            
            # Handle special actions
            if action.get('archive'):
                remove_label_ids.append('INBOX')
            if action.get('mark_as_read'):
                remove_label_ids.append('UNREAD')
            if action.get('mark_as_spam'):
                add_label_ids.append('SPAM')

            # Filter out None values from failed lookups
            add_label_ids = [lid for lid in add_label_ids if lid]
            remove_label_ids = [lid for lid in remove_label_ids if lid]

            # 3. Apply actions using batchModify
            if add_label_ids or remove_label_ids:
                message_count = len(message_ids)
                logger.info(f"Applying actions to {message_count} messages in batches of 1000...")

                # Batch the message IDs into chunks of 1000
                for j in range(0, message_count, 1000):
                    batch_ids = message_ids[j:j + 1000]
                    logger.debug(f"Processing batch {j//1000 + 1} with {len(batch_ids)} messages.")
                    
                    batch_modify_body = {
                        'ids': batch_ids,
                        'addLabelIds': list(set(add_label_ids)),
                        'removeLabelIds': list(set(remove_label_ids))
                    }
                    
                    try:
                        wrap_gmail_api_call(
                            service.users().messages().batchModify(userId='me', body=batch_modify_body).execute,
                            operation=f"batch modify for filter '{filter_id}'"
                        )
                        logger.debug(f"Successfully applied filter '{filter_id}' to batch of {len(batch_ids)} messages.")
                    except GmailAPIError as e:
                        e.log_error(logger)
                        logger.error(f"Failed to apply batch for filter {filter_id}. Continuing...")
                        continue
                
                # 4. Collect stats
                count = len(message_ids)
                total_processed_count += count
                filter_stats[filter_id] = count
                logger.info(f"Successfully applied filter '{filter_id}' to {count} messages.")

        except GmailAPIError as e:
            e.log_error(logger)
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing filter {filter_id}: {e}")

    if progress_callback:
        progress_callback("Server-side filtering complete.", 100)

    result = {
        "processed_count": total_processed_count,
        "filter_stats": filter_stats,
        "server_side_processed": total_processed_count,
        "remaining_ids": [] # Legacy, no longer relevant
    }

    logger.info(f"Server-side filtering complete. Total messages processed: {total_processed_count}")
    return result


def _email_matches_filter(email_fields: Dict[str, str], filter_data: Dict[str, Any]) -> bool:
    """
    Check if an email matches a filter's criteria.
    
    Args:
        email_fields: Dictionary with 'from', 'to', 'subject' fields
        filter_data: Structured filter data from fetch_and_parse_filters
    
    Returns:
        bool: True if email matches the filter criteria
    """
    criteria = filter_data.get('raw_criteria', {})
    
    # Check each criteria field
    for key, value in criteria.items():
        if key == 'from' and value.lower() not in email_fields['from'].lower():
            return False
        elif key == 'to' and value.lower() not in email_fields['to'].lower():
            return False
        elif key == 'subject' and value.lower() not in email_fields['subject'].lower():
            return False
        elif key == 'hasTheWord':
            # Simple keyword matching - could be enhanced for complex queries
            search_text = f"{email_fields['from']} {email_fields['to']} {email_fields['subject']}".lower()
            if value.lower() not in search_text:
                return False
        elif key == 'doesNotHaveTheWord':
            search_text = f"{email_fields['from']} {email_fields['to']} {email_fields['subject']}".lower()
            if value.lower() in search_text:
                return False
    
    return True


def _apply_filter_action(service: Resource, email_id: str, action_data: Dict[str, Any]) -> bool:
    """
    Apply a filter action to an email.
    
    Args:
        service: Gmail API service object
        email_id: ID of the email to modify
        action_data: Parsed action data from _parse_action
    
    Returns:
        bool: True if action was applied successfully
    """
    try:
        modifications = {}
        
        # Prepare label modifications
        if action_data.get('add_labels'):
            # Convert label names back to IDs
            add_label_ids = []
            for label_name in action_data['add_labels']:
                label_id = _get_label_id_from_name(service, label_name)
                if label_id:
                    add_label_ids.append(label_id)
                else:
                    logger.warning(f"Could not find label ID for '{label_name}', skipping")
            
            if add_label_ids:
                modifications['addLabelIds'] = modifications.get('addLabelIds', []) + add_label_ids
        
        if action_data.get('archive'):
            modifications['removeLabelIds'] = ['INBOX']
        
        if action_data.get('mark_as_read'):
            modifications['removeLabelIds'] = modifications.get('removeLabelIds', []) + ['UNREAD']
        
        if action_data.get('mark_as_spam'):
            modifications['addLabelIds'] = ['SPAM']
            modifications['removeLabelIds'] = modifications.get('removeLabelIds', []) + ['INBOX']
        
        # Apply modifications if any
        if modifications:
            logger.debug(f"Applying modifications to email {email_id}: {modifications}")
            wrap_gmail_api_call(
                service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body=modifications
                ).execute,
                operation=f"apply filter action to email {email_id}"
            )
            logger.debug(f"Successfully applied filter action to email {email_id}")
            return True
        else:
            logger.debug(f"No modifications to apply to email {email_id}")
            return True
            
    except GmailAPIError as e:
        e.log_error(logger)
        return False
    except Exception as e:
        logger.error(f"Unexpected error applying filter action to email {email_id}: {e}")
        return False


if __name__ == '__main__':
    """
    Example usage:
    - Authenticates using existing utility.
    - Fetches and prints all structured filters.
    """
    from gmail_api_utils import get_gmail_service
    from log_config import init_logging
    import json

    # Initialize standardized logging
    init_logging(log_level=logging.INFO)
    
    # It's assumed that credentials.json and token.json are in the config directory.
    # Adjust the path if your structure is different.
    creds_path = '../config/credentials.json'
    token_path = '../config/token.json'

    gmail_service = get_gmail_service(credentials_path=creds_path, token_path=token_path)

    if gmail_service:
        all_filters = fetch_and_parse_filters(gmail_service)
        if all_filters:
            print("Successfully Extracted and Parsed Gmail Filters:")
            print(json.dumps(all_filters, indent=2))
        else:
            print("Could not extract any filters or no filters are defined.")