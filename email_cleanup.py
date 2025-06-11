"""
email_cleanup.py

Automates retention policy enforcement and trash cleanup for the Gmail automation system.

- Loads retention and cleanup policies from settings.json.
- Uses gmail_api_utils.py for all Gmail operations.
- Uses cron_utils.py for scheduling and persistent state tracking.
- Logs all actions and errors using log_config.py.
- Designed for import and use by runners or as a scheduled job.
- No CLI or main entry point.

All functions/classes are documented with docstrings and usage examples.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from log_config import get_logger
from gmail_api_utils import GmailLabelManager, GmailEmailManager, get_gmail_service
from cron_utils import CronScheduler

logger = get_logger(__name__)

DEFAULT_RETENTION_DAYS = 365
TRASH_RETENTION_DAYS = 30

def load_settings(settings_path: str = "config/settings.json") -> Dict[str, Any]:
    """
    Load settings from a JSON file.

    Args:
        settings_path (str): Path to the settings.json file.

    Returns:
        dict: Parsed settings.

    Usage Example:
        settings = load_settings()
    """
    with open(settings_path, "r") as f:
        return json.load(f)

def get_retention_policy(settings: Dict[str, Any]) -> Dict[str, int]:
    """
    Get retention policy per label from settings, or use default.

    Args:
        settings (dict): Settings dictionary.

    Returns:
        dict: Mapping of label name to retention days.

    Usage Example:
        policy = get_retention_policy(settings)
    """
    # Future: support per-label retention in settings["retention"]["per_label"]
    default_days = settings.get("retention", {}).get("default_days", DEFAULT_RETENTION_DAYS)
    # If per-label retention is not present, use default for all mapped labels
    label_action_mappings = settings.get("label_action_mappings", {})
    return {label: default_days for label in label_action_mappings}

def identify_emails_for_cleanup(
    settings: Dict[str, Any],
    service,
    as_of: Optional[datetime] = None
) -> Dict[str, List[str]]:
    """
    Identify emails eligible for deletion or archiving based on policy.

    Args:
        settings (dict): Settings dictionary.
        service: Authenticated Gmail API service object.
        as_of (datetime, optional): Reference time for cutoff (default: now).

    Returns:
        dict: Mapping of action ("TRASH", "DELETE", "ARCHIVE") to list of message IDs.

    Usage Example:
        service = get_gmail_service()
        eligible = identify_emails_for_cleanup(settings, service)
    """
    logger.info("Identifying emails eligible for cleanup...")
    label_mgr = GmailLabelManager(service)
    email_mgr = GmailEmailManager(service)
    label_mgr.refresh_label_cache()

    retention_policy = get_retention_policy(settings)
    label_action_mappings = settings.get("label_action_mappings", {})
    max_results = settings.get("gmail", {}).get("max_results_per_query", 500)
    as_of = as_of or datetime.utcnow()

    eligible: Dict[str, List[str]] = {"TRASH": [], "DELETE": [], "ARCHIVE": []}

    for label, action in label_action_mappings.items():
        retention_days = retention_policy.get(label, DEFAULT_RETENTION_DAYS)
        cutoff_date = (as_of - timedelta(days=retention_days)).strftime("%Y/%m/%d")
        label_id = label_mgr.list_labels().get(label)
        if not label_id:
            logger.warning(f"Label '{label}' not found in Gmail. Skipping.")
            continue

        # Gmail query for emails before cutoff
        query = f"label:{label} before:{cutoff_date}"
        emails = email_mgr.list_emails(label_ids=[label_id], query=query, max_results=max_results)
        msg_ids = [msg["id"] for msg in emails]

        if not msg_ids:
            continue

        if action == "TRASH":
            eligible["TRASH"].extend(msg_ids)
        elif action == "DELETE":
            eligible["DELETE"].extend(msg_ids)
        elif action == "LABEL_AND_ARCHIVE":
            eligible["ARCHIVE"].extend(msg_ids)
        # "KEEP" and unknown actions are ignored

    logger.info(
        f"Identified {len(eligible['TRASH'])} for trash, "
        f"{len(eligible['DELETE'])} for delete, "
        f"{len(eligible['ARCHIVE'])} for archive."
    )
    return eligible

def cleanup_emails(
    settings: Dict[str, Any],
    service,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Move emails to trash, permanently delete, or archive as required by policy.

    Args:
        settings (dict): Settings dictionary.
        service: Authenticated Gmail API service object.
        dry_run (bool): If True, only log actions without performing them.

    Returns:
        dict: Counts of actions performed.

    Usage Example:
        service = get_gmail_service()
        cleanup_emails(settings, service)
    """
    logger.info("Starting email cleanup...")
    email_mgr = GmailEmailManager(service)
    eligible = identify_emails_for_cleanup(settings, service)
    results = {"TRASH": 0, "DELETE": 0, "ARCHIVE": 0, "ERRORS": 0}

    # Trash
    for msg_id in eligible["TRASH"]:
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would move email {msg_id} to trash.")
            else:
                if email_mgr.move_to_trash(msg_id):
                    results["TRASH"] += 1
        except Exception as e:
            logger.error(f"Error trashing email {msg_id}: {e}")
            results["ERRORS"] += 1

    # Delete
    for msg_id in eligible["DELETE"]:
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would permanently delete email {msg_id}.")
            else:
                if email_mgr.delete_email(msg_id):
                    results["DELETE"] += 1
        except Exception as e:
            logger.error(f"Error deleting email {msg_id}: {e}")
            results["ERRORS"] += 1

    # Archive (remove INBOX label)
    for msg_id in eligible["ARCHIVE"]:
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would archive email {msg_id}.")
            else:
                if email_mgr.archive_email(msg_id):
                    results["ARCHIVE"] += 1
        except Exception as e:
            logger.error(f"Error archiving email {msg_id}: {e}")
            results["ERRORS"] += 1

    logger.info(
        f"Cleanup complete: {results['TRASH']} trashed, "
        f"{results['DELETE']} deleted, {results['ARCHIVE']} archived, "
        f"{results['ERRORS']} errors."
    )
    return results

def empty_trash(
    settings: Dict[str, Any],
    service,
    dry_run: bool = False
) -> int:
    """
    Permanently delete emails from trash older than the trash retention period.

    Args:
        settings (dict): Settings dictionary.
        service: Authenticated Gmail API service object.
        dry_run (bool): If True, only log actions without performing them.

    Returns:
        int: Number of emails permanently deleted from trash.

    Usage Example:
        service = get_gmail_service()
        empty_trash(settings, service)
    """
    logger.info("Emptying trash for emails older than retention period...")
    email_mgr = GmailEmailManager(service)
    trash_retention = settings.get("retention", {}).get("trash_days", TRASH_RETENTION_DAYS)
    cutoff_date = (datetime.utcnow() - timedelta(days=trash_retention)).strftime("%Y/%m/%d")
    query = f"in:trash before:{cutoff_date}"
    max_results = settings.get("gmail", {}).get("max_results_per_query", 1000)
    emails = email_mgr.list_emails(query=query, max_results=max_results)
    msg_ids = [msg["id"] for msg in emails]
    deleted = 0

    for msg_id in msg_ids:
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would permanently delete trashed email {msg_id}.")
            else:
                if email_mgr.delete_email(msg_id):
                    deleted += 1
        except Exception as e:
            logger.error(f"Error deleting trashed email {msg_id}: {e}")

    logger.info(f"Emptied {deleted} emails from trash.")
    return deleted

def run_cleanup_job(
    settings_path: str = "config/settings.json",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run the full cleanup job: enforce retention and empty trash.

    Args:
        settings_path (str): Path to settings.json.
        dry_run (bool): If True, only log actions without performing them.

    Returns:
        dict: Summary of actions performed.

    Usage Example:
        run_cleanup_job("config/settings.json", dry_run=True)
    """
    logger.info("Running full email cleanup job...")
    settings = load_settings(settings_path)
    service = get_gmail_service()
    results = cleanup_emails(settings, service, dry_run=dry_run)
    trash_deleted = empty_trash(settings, service, dry_run=dry_run)
    results["TRASH_DELETED"] = trash_deleted
    logger.info(f"Cleanup job summary: {results}")
    return results

# Usage Example (for import, not execution):
#
# from email_cleanup import run_cleanup_job
# run_cleanup_job("config/settings.json", dry_run=True)
#
# For scheduled jobs, use cron_utils.CronScheduler to track last run and status.