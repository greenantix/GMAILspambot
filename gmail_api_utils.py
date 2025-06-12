"""
gmail_api_utils.py

Reusable utilities for interacting with the Gmail API, including label management,
email operations, batch processing, and robust error handling/logging.

Designed for import by other scripts (e.g., audit tool, config updater, runners).

Requirements:
- OAuth2 authentication (see `get_gmail_service` stub below)
- Logging via log_config.get_logger
- No CLI/main entry point

Dependencies:
- google-api-python-client
- google-auth, google-auth-oauthlib, google-auth-httplib2

See README.md for setup instructions.
"""

import logging
import os.path
from typing import Optional, List, Dict, Any, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
import time
import random

from log_config import get_logger

logger = get_logger(__name__)

# If modifying these scopes, delete the file config/token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.send'
]

# =========================
# Utility Functions
# =========================

def exponential_backoff_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    
    Returns:
        Result of the function call
    
    Raises:
        The last exception if all retries are exhausted
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except HttpError as e:
            # Check if this is a retryable error
            if e.resp.status in [429, 500, 502, 503, 504]:
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for API call")
                    raise
                
                # Calculate delay with jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"API rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(delay)
            else:
                # Non-retryable error, raise immediately
                raise
        except Exception as e:
            # Non-HTTP errors are generally not retryable
            logger.error(f"Non-retryable error in API call: {e}")
            raise


# =========================
# OAuth2 Authentication
# =========================

def get_gmail_service(credentials_path: str = "config/credentials.json", token_path: str = "config/token.json"):
    """
    Obtain an authenticated Gmail API service object using OAuth2.

    Args:
        credentials_path (str): Path to OAuth2 client credentials JSON.
        token_path (str): Path to store/retrieve user token.

    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail API service.

    Usage Example:
        service = get_gmail_service()
        manager = GmailLabelManager(service)
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully obtained Gmail API service.")
        return service
    except HttpError as err:
        logger.error(f"An error occurred while building Gmail service: {err}")
        return None

# =========================
# Label Management
# =========================

class GmailLabelManager:
    """
    Utility class for managing Gmail labels.

    Args:
        service: Authenticated Gmail API service object.

    Usage Example:
        manager = GmailLabelManager(service)
        manager.refresh_label_cache()
        label_id = manager.create_label("IMPORTANT")
    """

    def __init__(self, service):
        self.service = service
        self._label_cache: Dict[str, str] = {}
        self.logger = get_logger(self.__class__.__name__)

    def refresh_label_cache(self):
        """
        Cache existing labels to avoid repeated API calls.
        """
        def _fetch_labels():
            results = self.service.users().labels().list(userId='me').execute()
            return {label['name']: label['id'] for label in results.get('labels', [])}
        
        try:
            self._label_cache = exponential_backoff_retry(_fetch_labels)
            self.logger.debug(f"Label cache refreshed: {self._label_cache}")
        except Exception as e:
            self.logger.error(f"Failed to refresh label cache after retries: {e}")
            self._label_cache = {}

    def create_label(self, label_name: str, label_color: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Create a Gmail label with optional color.

        Args:
            label_name (str): Name of the label.
            label_color (dict, optional): Color dict, e.g. {'backgroundColor': '#fb4c2f', 'textColor': '#ffffff'}

        Returns:
            str or None: Label ID if created or exists, else None.

        Usage Example:
            label_id = manager.create_label("BILLS", {"backgroundColor": "#fb4c2f", "textColor": "#ffffff"})
        """
        if label_name in self._label_cache:
            return self._label_cache[label_name]

        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        if label_color:
            label_object['color'] = label_color

        def _create_label():
            return self.service.users().labels().create(userId='me', body=label_object).execute()
        
        try:
            created = exponential_backoff_retry(_create_label)
            self._label_cache[label_name] = created['id']
            self.logger.info(f"Created label '{label_name}'")
            return created['id']
        except HttpError as e:
            if hasattr(e, 'resp') and getattr(e.resp, 'status', None) == 409:
                # Already exists
                self.logger.warning(f"Label '{label_name}' already exists. Refreshing cache.")
                self.refresh_label_cache()
                return self._label_cache.get(label_name)
            self.logger.error(f"Failed to create label '{label_name}' after retries: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to create label '{label_name}' after retries: {e}")
            return None

    def delete_label(self, label_name: str) -> bool:
        """
        Delete a Gmail label by name.

        Args:
            label_name (str): Name of the label to delete.

        Returns:
            bool: True if deleted, False otherwise.

        Usage Example:
            manager.delete_label("NEWSLETTERS")
        """
        label_id = self._label_cache.get(label_name)
        if not label_id:
            self.logger.warning(f"Label '{label_name}' not found in cache.")
            return False

        try:
            self.service.users().labels().delete(
                userId='me', id=label_id).execute()
            del self._label_cache[label_name]
            self.logger.info(f"Deleted label '{label_name}'")
            return True
        except HttpError as e:
            self.logger.error(f"Failed to delete label '{label_name}': {e}")
            return False

    def rename_label(self, old_name: str, new_name: str) -> bool:
        """
        Rename a label by creating a new label, reassigning messages, and deleting the old label.

        Args:
            old_name (str): Existing label name.
            new_name (str): New label name.

        Returns:
            bool: True if renamed, False otherwise.

        Usage Example:
            manager.rename_label("OLD", "NEW")
        """
        old_id = self._label_cache.get(old_name)
        if not old_id:
            self.logger.warning(f"Label '{old_name}' not found for renaming.")
            return False

        # Find affected emails
        try:
            results = self.service.users().messages().list(
                userId='me', labelIds=[old_id]).execute()
            message_ids = [m['id'] for m in results.get('messages', [])]
        except HttpError as e:
            self.logger.error(f"Failed to list messages for label '{old_name}': {e}")
            return False

        # Create new label
        new_id = self.create_label(new_name)
        if not new_id:
            self.logger.error(f"Failed to create new label '{new_name}' during rename.")
            return False

        # Batch update messages
        for msg_id in message_ids:
            try:
                self.service.users().messages().modify(
                    userId='me', id=msg_id,
                    body={'addLabelIds': [new_id], 'removeLabelIds': [old_id]}
                ).execute()
            except HttpError as e:
                self.logger.error(f"Failed to reassign message {msg_id}: {e}")

        # Delete old label
        return self.delete_label(old_name)

    def list_labels(self) -> Dict[str, str]:
        """
        List all labels (name to ID mapping).

        Returns:
            dict: Mapping of label names to IDs.

        Usage Example:
            labels = manager.list_labels()
        """
        if not self._label_cache:
            self.refresh_label_cache()
        return dict(self._label_cache)

# =========================
# Email Operations
# =========================

class GmailEmailManager:
    """
    Utility class for Gmail email operations.

    Args:
        service: Authenticated Gmail API service object.

    Usage Example:
        email_mgr = GmailEmailManager(service)
        emails = email_mgr.list_emails(label_ids=['INBOX'], max_results=10)
    """

    def __init__(self, service):
        self.service = service
        self.logger = get_logger(self.__class__.__name__)

    def list_emails(self, label_ids: Optional[List[str]] = None, query: Optional[str] = None,
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List emails matching label(s) or query.

        Args:
            label_ids (list, optional): List of label IDs to filter.
            query (str, optional): Gmail search query.
            max_results (int): Max emails to return.

        Returns:
            list: List of message dicts.

        Usage Example:
            emails = email_mgr.list_emails(label_ids=['INBOX'], max_results=5)
        """
        def _list_emails():
            return self.service.users().messages().list(
                userId='me',
                labelIds=label_ids,
                q=query,
                maxResults=max_results
            ).execute()
        
        try:
            response = exponential_backoff_retry(_list_emails)
            messages = response.get('messages', [])
            self.logger.info(f"Listed {len(messages)} emails.")
            return messages
        except Exception as e:
            self.logger.error(f"Failed to list emails after retries: {e}")
            return []

    def get_email(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single email by message ID.

        Args:
            msg_id (str): Gmail message ID.

        Returns:
            dict or None: Message resource.

        Usage Example:
            msg = email_mgr.get_email(msg_id)
        """
        def _get_email():
            return self.service.users().messages().get(userId='me', id=msg_id).execute()
        
        try:
            msg = exponential_backoff_retry(_get_email)
            self.logger.debug(f"Fetched email {msg_id}")
            return msg
        except Exception as e:
            self.logger.error(f"Failed to get email {msg_id} after retries: {e}")
            return None

    def move_to_trash(self, msg_id: str) -> bool:
        """
        Move an email to trash.

        Args:
            msg_id (str): Gmail message ID.

        Returns:
            bool: True if successful.

        Usage Example:
            email_mgr.move_to_trash(msg_id)
        """
        def _move_to_trash():
            return self.service.users().messages().trash(userId='me', id=msg_id).execute()
        
        try:
            exponential_backoff_retry(_move_to_trash)
            self.logger.info(f"Moved email {msg_id} to trash.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move email {msg_id} to trash after retries: {e}")
            return False

    def delete_email(self, msg_id: str) -> bool:
        """
        Permanently delete an email.

        Args:
            msg_id (str): Gmail message ID.

        Returns:
            bool: True if successful.

        Usage Example:
            email_mgr.delete_email(msg_id)
        """
        try:
            self.service.users().messages().delete(userId='me', id=msg_id).execute()
            self.logger.info(f"Deleted email {msg_id}.")
            return True
        except HttpError as e:
            self.logger.error(f"Failed to delete email {msg_id}: {e}")
            return False

    def restore_from_trash(self, msg_id: str) -> bool:
        """
        Restore an email from trash.

        Args:
            msg_id (str): Gmail message ID.

        Returns:
            bool: True if successful.

        Usage Example:
            email_mgr.restore_from_trash(msg_id)
        """
        def _restore_from_trash():
            return self.service.users().messages().untrash(userId='me', id=msg_id).execute()
        
        try:
            exponential_backoff_retry(_restore_from_trash)
            self.logger.info(f"Restored email {msg_id} from trash.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore email {msg_id} from trash after retries: {e}")
            return False

    def modify_labels(self, msg_id: str, add_labels: Optional[List[str]] = None,
                     remove_labels: Optional[List[str]] = None) -> bool:
        """
        Add or remove labels from an email.

        Args:
            msg_id (str): Gmail message ID.
            add_labels (list, optional): Label IDs to add.
            remove_labels (list, optional): Label IDs to remove.

        Returns:
            bool: True if successful.

        Usage Example:
            email_mgr.modify_labels(msg_id, add_labels=['IMPORTANT'], remove_labels=['INBOX'])
        """
        body = {}
        if add_labels:
            body['addLabelIds'] = add_labels
        if remove_labels:
            body['removeLabelIds'] = remove_labels
        if not body:
            self.logger.warning("No labels specified for modification.")
            return False
        try:
            self.service.users().messages().modify(
                userId='me', id=msg_id, body=body).execute()
            self.logger.info(f"Modified labels for email {msg_id}: {body}")
            return True
        except HttpError as e:
            self.logger.error(f"Failed to modify labels for email {msg_id}: {e}")
            return False

    def archive_email(self, msg_id: str) -> bool:
        """
        Archive an email (remove INBOX label).

        Args:
            msg_id (str): Gmail message ID.

        Returns:
            bool: True if successful.

        Usage Example:
            email_mgr.archive_email(msg_id)
        """
        return self.modify_labels(msg_id, remove_labels=['INBOX'])

    # Batch operations

    def batch_modify(self, msg_ids: List[str], add_labels: Optional[List[str]] = None,
                     remove_labels: Optional[List[str]] = None, batch_size: int = 100) -> Dict[str, bool]:
        """
        Efficiently batch add/remove labels for multiple emails using Gmail API batch requests.

        Args:
            msg_ids (list): List of Gmail message IDs.
            add_labels (list, optional): Label IDs to add.
            remove_labels (list, optional): Label IDs to remove.
            batch_size (int): Number of operations per batch request (max 100).

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_modify(msg_ids, add_labels=['IMPORTANT'])
        """
        if not msg_ids:
            return {}
        
        results = {}
        batch_size = min(batch_size, 100)  # Gmail API limit
        
        # Process in chunks to respect API limits
        for i in range(0, len(msg_ids), batch_size):
            chunk = msg_ids[i:i + batch_size]
            chunk_results = self._execute_batch_modify_chunk(chunk, add_labels, remove_labels)
            results.update(chunk_results)
            
            # Small delay between chunks to be API-friendly
            if i + batch_size < len(msg_ids):
                time.sleep(0.1)
        
        return results

    def _execute_batch_modify_chunk(self, msg_ids: List[str], add_labels: Optional[List[str]], 
                                   remove_labels: Optional[List[str]]) -> Dict[str, bool]:
        """Execute a single batch modification chunk."""
        results = {}
        
        def execute_batch():
            batch = BatchHttpRequest()
            
            # Prepare the request body
            modify_body = {}
            if add_labels:
                modify_body['addLabelIds'] = add_labels
            if remove_labels:
                modify_body['removeLabelIds'] = remove_labels
            
            if not modify_body:
                # No modifications to make
                return {msg_id: True for msg_id in msg_ids}
            
            # Add each message modification to the batch
            for msg_id in msg_ids:
                def callback(request_id, response, exception):
                    nonlocal results
                    if exception is not None:
                        logger.error(f"Error modifying message {request_id}: {exception}")
                        results[request_id] = False
                    else:
                        results[request_id] = True
                
                request = self.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body=modify_body
                )
                batch.add(request, callback=callback, request_id=msg_id)
            
            # Execute the batch
            batch.execute()
            return results
        
        # Execute with retry logic
        try:
            return exponential_backoff_retry(execute_batch)
        except Exception as e:
            logger.error(f"Batch modify failed for chunk: {e}")
            return {msg_id: False for msg_id in msg_ids}

    def batch_delete(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]:
        """
        Efficiently batch delete emails using Gmail API batch requests.

        Args:
            msg_ids (list): List of Gmail message IDs.
            batch_size (int): Number of operations per batch request (max 100).

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_delete(msg_ids)
        """
        if not msg_ids:
            return {}
        
        results = {}
        batch_size = min(batch_size, 100)  # Gmail API limit
        
        # Process in chunks to respect API limits
        for i in range(0, len(msg_ids), batch_size):
            chunk = msg_ids[i:i + batch_size]
            chunk_results = self._execute_batch_delete_chunk(chunk)
            results.update(chunk_results)
            
            # Small delay between chunks to be API-friendly
            if i + batch_size < len(msg_ids):
                time.sleep(0.1)
        
        return results

    def _execute_batch_delete_chunk(self, msg_ids: List[str]) -> Dict[str, bool]:
        """Execute a single batch delete chunk."""
        results = {}
        
        def execute_batch():
            batch = BatchHttpRequest()
            
            # Add each message deletion to the batch
            for msg_id in msg_ids:
                def callback(request_id, response, exception):
                    nonlocal results
                    if exception is not None:
                        logger.error(f"Error deleting message {request_id}: {exception}")
                        results[request_id] = False
                    else:
                        results[request_id] = True
                
                request = self.service.users().messages().delete(userId='me', id=msg_id)
                batch.add(request, callback=callback, request_id=msg_id)
            
            # Execute the batch
            batch.execute()
            return results
        
        # Execute with retry logic
        try:
            return exponential_backoff_retry(execute_batch)
        except Exception as e:
            logger.error(f"Batch delete failed for chunk: {e}")
            return {msg_id: False for msg_id in msg_ids}

    def batch_move_to_trash(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]:
        """
        Efficiently batch move emails to trash using Gmail API batch requests.

        Args:
            msg_ids (list): List of Gmail message IDs.
            batch_size (int): Number of operations per batch request (max 100).

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_move_to_trash(msg_ids)
        """
        # Use the batch_modify method with TRASH label operations
        return self.batch_modify(msg_ids, add_labels=['TRASH'], remove_labels=['INBOX'], batch_size=batch_size)

    def batch_restore_from_trash(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]:
        """
        Efficiently batch restore emails from trash using Gmail API batch requests.

        Args:
            msg_ids (list): List of Gmail message IDs.
            batch_size (int): Number of operations per batch request (max 100).

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_restore_from_trash(msg_ids)
        """
        # Use the batch_modify method to remove TRASH label and add INBOX
        return self.batch_modify(msg_ids, add_labels=['INBOX'], remove_labels=['TRASH'], batch_size=batch_size)

    def batch_get_messages(self, msg_ids: List[str], format: str = 'metadata', 
                          metadata_headers: Optional[List[str]] = None, 
                          batch_size: int = 100) -> Dict[str, Any]:
        """
        Efficiently batch fetch message data using Gmail API batch requests.

        Args:
            msg_ids (list): List of Gmail message IDs.
            format (str): Message format ('minimal', 'metadata', 'full').
            metadata_headers (list, optional): Specific headers to include when format='metadata'.
            batch_size (int): Number of operations per batch request (max 100).

        Returns:
            dict: Mapping of msg_id to message data (or None if error).

        Usage Example:
            messages = email_mgr.batch_get_messages(msg_ids, format='metadata', 
                                                   metadata_headers=['From', 'Subject'])
        """
        if not msg_ids:
            return {}
        
        results = {}
        batch_size = min(batch_size, 100)  # Gmail API limit
        
        # Process in chunks to respect API limits
        for i in range(0, len(msg_ids), batch_size):
            chunk = msg_ids[i:i + batch_size]
            chunk_results = self._execute_batch_get_chunk(chunk, format, metadata_headers)
            results.update(chunk_results)
            
            # Small delay between chunks to be API-friendly
            if i + batch_size < len(msg_ids):
                time.sleep(0.1)
        
        return results

    def _execute_batch_get_chunk(self, msg_ids: List[str], format: str, 
                                metadata_headers: Optional[List[str]]) -> Dict[str, Any]:
        """Execute a single batch get messages chunk."""
        results = {}
        
        def execute_batch():
            batch = BatchHttpRequest()
            
            # Add each message get to the batch
            for msg_id in msg_ids:
                def callback(request_id, response, exception):
                    nonlocal results
                    if exception is not None:
                        logger.error(f"Error fetching message {request_id}: {exception}")
                        results[request_id] = None
                    else:
                        results[request_id] = response
                
                # Build the get request
                get_params = {'userId': 'me', 'id': msg_id, 'format': format}
                if format == 'metadata' and metadata_headers:
                    get_params['metadataHeaders'] = metadata_headers
                
                request = self.service.users().messages().get(**get_params)
                batch.add(request, callback=callback, request_id=msg_id)
            
            # Execute the batch
            batch.execute()
            return results
        
        # Execute with retry logic
        try:
            return exponential_backoff_retry(execute_batch)
        except Exception as e:
            logger.error(f"Batch get messages failed for chunk: {e}")
            return {msg_id: None for msg_id in msg_ids}

# =========================
# Utility Functions
# =========================

def get_label_id(service, label_name: str) -> Optional[str]:
    """
    Get the label ID for a given label name.

    Args:
        service: Authenticated Gmail API service object.
        label_name (str): Name of the label.

    Returns:
        str or None: Label ID if found.

    Usage Example:
        label_id = get_label_id(service, "IMPORTANT")
    """
    try:
        results = service.users().labels().list(userId='me').execute()
        for label in results.get('labels', []):
            if label['name'] == label_name:
                return label['id']
    except HttpError as e:
        logger.error(f"Failed to get label ID for '{label_name}': {e}")
    return None