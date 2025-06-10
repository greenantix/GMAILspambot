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

from log_config import get_logger

logger = get_logger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# =========================
# OAuth2 Authentication
# =========================

def get_gmail_service(credentials_path: str = "credentials.json", token_path: str = "token.json"):
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
        try:
            results = self.service.users().labels().list(userId='me').execute()
            self._label_cache = {label['name']: label['id']
                                 for label in results.get('labels', [])}
            self.logger.debug(f"Label cache refreshed: {self._label_cache}")
        except HttpError as e:
            self.logger.error(f"Failed to refresh label cache: {e}")
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

        try:
            created = self.service.users().labels().create(
                userId='me', body=label_object).execute()
            self._label_cache[label_name] = created['id']
            self.logger.info(f"Created label '{label_name}'")
            return created['id']
        except HttpError as e:
            if hasattr(e, 'resp') and getattr(e.resp, 'status', None) == 409:
                # Already exists
                self.logger.warning(f"Label '{label_name}' already exists. Refreshing cache.")
                self.refresh_label_cache()
                return self._label_cache.get(label_name)
            self.logger.error(f"Failed to create label '{label_name}': {e}")
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
        try:
            response = self.service.users().messages().list(
                userId='me',
                labelIds=label_ids,
                q=query,
                maxResults=max_results
            ).execute()
            messages = response.get('messages', [])
            self.logger.info(f"Listed {len(messages)} emails.")
            return messages
        except HttpError as e:
            self.logger.error(f"Failed to list emails: {e}")
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
        try:
            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
            self.logger.debug(f"Fetched email {msg_id}")
            return msg
        except HttpError as e:
            self.logger.error(f"Failed to get email {msg_id}: {e}")
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
        try:
            self.service.users().messages().trash(userId='me', id=msg_id).execute()
            self.logger.info(f"Moved email {msg_id} to trash.")
            return True
        except HttpError as e:
            self.logger.error(f"Failed to move email {msg_id} to trash: {e}")
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
        try:
            self.service.users().messages().untrash(userId='me', id=msg_id).execute()
            self.logger.info(f"Restored email {msg_id} from trash.")
            return True
        except HttpError as e:
            self.logger.error(f"Failed to restore email {msg_id} from trash: {e}")
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
                     remove_labels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Batch add/remove labels for multiple emails.

        Args:
            msg_ids (list): List of Gmail message IDs.
            add_labels (list, optional): Label IDs to add.
            remove_labels (list, optional): Label IDs to remove.

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_modify(msg_ids, add_labels=['IMPORTANT'])
        """
        results = {}
        for msg_id in msg_ids:
            results[msg_id] = self.modify_labels(msg_id, add_labels, remove_labels)
        return results

    def batch_delete(self, msg_ids: List[str]) -> Dict[str, bool]:
        """
        Batch delete emails.

        Args:
            msg_ids (list): List of Gmail message IDs.

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_delete(msg_ids)
        """
        results = {}
        for msg_id in msg_ids:
            results[msg_id] = self.delete_email(msg_id)
        return results

    def batch_move_to_trash(self, msg_ids: List[str]) -> Dict[str, bool]:
        """
        Batch move emails to trash.

        Args:
            msg_ids (list): List of Gmail message IDs.

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_move_to_trash(msg_ids)
        """
        results = {}
        for msg_id in msg_ids:
            results[msg_id] = self.move_to_trash(msg_id)
        return results

    def batch_restore_from_trash(self, msg_ids: List[str]) -> Dict[str, bool]:
        """
        Batch restore emails from trash.

        Args:
            msg_ids (list): List of Gmail message IDs.

        Returns:
            dict: Mapping of msg_id to success status.

        Usage Example:
            results = email_mgr.batch_restore_from_trash(msg_ids)
        """
        results = {}
        for msg_id in msg_ids:
            results[msg_id] = self.restore_from_trash(msg_id)
        return results

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