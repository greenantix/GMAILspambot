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

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

# Initialize logger
logger = logging.getLogger(__name__)

# Cache for label ID to name mapping to reduce API calls
_label_id_to_name_cache = {}


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
        label = service.users().labels().get(userId='me', id=label_id).execute()
        label_name = label.get('name')
        if label_name:
            _label_id_to_name_cache[label_id] = label_name
        return label_name
    except HttpError as e:
        logger.error(f"Failed to retrieve name for label ID {label_id}: {e}")
        return None


def _parse_criteria(criteria: Dict[str, Any]) -> str:
    """
    Converts a filter's criteria object into a Gmail search query string.

    Handles various fields like 'from', 'to', 'subject', 'hasTheWord', etc.

    Args:
        criteria (Dict[str, Any]): The criteria part of a Gmail filter resource.

    Returns:
        str: A string formatted as a Gmail search query.
    """
    query_parts = []
    for key, value in criteria.items():
        if key == "hasTheWord":
            key = ""  # The value itself is the query
        elif key == "doesNotHaveTheWord":
            key = "-"
        
        if isinstance(value, str) and ' ' in value:
            query_parts.append(f'{key}:"{value}"')
        else:
            query_parts.append(f'{key}:{value}')
            
    return ' '.join(query_parts)


def _parse_action(service: Resource, action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a filter's action object to extract label modifications and other actions.

    Args:
        service (Resource): The authenticated Gmail API service object.
        action (Dict[str, Any]): The action part of a Gmail filter resource.

    Returns:
        Dict[str, Any]: A structured dictionary of actions.
    """
    parsed = {
        "add_labels": [],
        "remove_labels": [],
        "mark_as_spam": "spam" in action.get("addLabelIds", []),
    }

    if "addLabelIds" in action:
        parsed["add_labels"] = [
            _get_label_name_from_id(service, label_id)
            for label_id in action["addLabelIds"]
            if _get_label_name_from_id(service, label_id)
        ]

    if "removeLabelIds" in action:
        parsed["remove_labels"] = [
            _get_label_name_from_id(service, label_id)
            for label_id in action["removeLabelIds"]
            if _get_label_name_from_id(service, label_id)
        ]

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
        results = service.users().settings().filters().list(userId='me').execute()
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

            query = _parse_criteria(criteria)
            parsed_action = _parse_action(service, action)

            structured_filters.append({
                "id": filter_id,
                "query": query,
                "action": parsed_action,
                "raw_criteria": criteria,
                "raw_action": action,
            })
        
        logger.info(f"Successfully parsed {len(structured_filters)} filters.")

    except HttpError as e:
        logger.error(f"An error occurred while fetching Gmail filters: {e}")
    
    return structured_filters

if __name__ == '__main__':
    """
    Example usage:
    - Authenticates using existing utility.
    - Fetches and prints all structured filters.
    """
    from gmail_api_utils import get_gmail_service
    import json

    logging.basicConfig(level=logging.INFO)
    
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