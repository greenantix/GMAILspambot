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


def apply_existing_filters_to_backlog(service: Resource, email_ids: List[str], 
                                    progress_callback=None) -> Dict[str, Any]:
    """
    Applies existing Gmail filters to a batch of emails to pre-process them
    before LLM analysis.
    
    Args:
        service (Resource): The authenticated Gmail API service object.
        email_ids (List[str]): List of email IDs to process.
        progress_callback: Optional callback function for progress updates.
    
    Returns:
        Dict[str, Any]: Statistics about filter applications including:
            - processed_count: Number of emails processed by filters
            - remaining_ids: Email IDs that still need LLM processing
            - filter_stats: Dictionary of filter ID -> count applied
    """
    if not email_ids:
        return {
            "processed_count": 0,
            "remaining_ids": [],
            "filter_stats": {}
        }
    
    # Fetch all existing filters
    structured_filters = fetch_and_parse_filters(service)
    if not structured_filters:
        logger.info("No filters found, all emails will need LLM processing")
        return {
            "processed_count": 0,
            "remaining_ids": email_ids,
            "filter_stats": {}
        }
    
    processed_emails = set()
    filter_stats = {}
    remaining_ids = []
    
    logger.info(f"Applying {len(structured_filters)} filters to {len(email_ids)} emails")
    
    try:
        # Process emails in batches to avoid API limits
        batch_size = 50
        for i in range(0, len(email_ids), batch_size):
            batch_ids = email_ids[i:i + batch_size]
            
            # Get email metadata for this batch
            try:
                # Use batch request for efficiency
                batch_emails = []
                for email_id in batch_ids:
                    email = service.users().messages().get(
                        userId='me', 
                        id=email_id,
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject']
                    ).execute()
                    batch_emails.append((email_id, email))
                
            except HttpError as e:
                logger.error(f"Failed to fetch email batch: {e}")
                remaining_ids.extend(batch_ids)
                continue
            
            # Apply filters to each email in the batch
            for email_id, email_data in batch_emails:
                if email_id in processed_emails:
                    continue
                    
                # Extract email fields for filter matching
                headers = {h['name'].lower(): h['value'] 
                          for h in email_data.get('payload', {}).get('headers', [])}
                
                email_fields = {
                    'from': headers.get('from', ''),
                    'to': headers.get('to', ''),
                    'subject': headers.get('subject', ''),
                }
                
                # Check each filter against this email
                filter_applied = False
                for filter_data in structured_filters:
                    if _email_matches_filter(email_fields, filter_data):
                        # Apply the filter action
                        if _apply_filter_action(service, email_id, filter_data['action']):
                            processed_emails.add(email_id)
                            filter_stats[filter_data['id']] = filter_stats.get(filter_data['id'], 0) + 1
                            filter_applied = True
                            logger.debug(f"Applied filter {filter_data['id']} to email {email_id}")
                            break  # Only apply first matching filter
                
                if not filter_applied:
                    remaining_ids.append(email_id)
            
            # Update progress
            if progress_callback:
                progress = min(100, ((i + batch_size) / len(email_ids)) * 100)
                progress_callback(f"Applied filters to {min(i + batch_size, len(email_ids))} emails", progress)
    
    except Exception as e:
        logger.error(f"Error applying filters to backlog: {e}")
        # Return remaining emails for LLM processing
        remaining_ids.extend([eid for eid in email_ids if eid not in processed_emails])
    
    result = {
        "processed_count": len(processed_emails),
        "remaining_ids": remaining_ids,
        "filter_stats": filter_stats
    }
    
    logger.info(f"Filter processing complete: {len(processed_emails)} processed by filters, "
                f"{len(remaining_ids)} remaining for LLM")
    
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