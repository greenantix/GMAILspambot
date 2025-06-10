#!/usr/bin/env python3
"""
audit_tool.py - CLI tool for auditing and restoring Gmail automation actions.

Features:
- Load configuration from settings.json
- Initialize logging using log_config.py
- Read and filter audit logs (JSON lines)
- CLI review: filter/search by date, action, label, email_id, etc.
- Restore/revert actions (stubbed, with TODOs for Gmail API)
- Log all operations and errors
- Robust error handling and clear TODOs for future GUI/Gmail API integration
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Import logging config
import log_config

SETTINGS_PATH = "settings.json"

def load_settings(path: str) -> dict:
    try:
        with open(path, "r") as f:
            # Strip comments if present (JSON5 style)
            content = f.read()
            content = "\n".join(line for line in content.splitlines() if not line.strip().startswith("//") and not line.strip().startswith("/*") and not line.strip().startswith("*") and not line.strip().endswith("*/"))
            return json.loads(content)
    except Exception as e:
        print(f"Error loading settings: {e}")
        sys.exit(1)

def parse_date(date_str: str) -> Optional[datetime]:
    # Accepts YYYY-MM-DD, 'today', 'yesterday'
    if date_str.lower() == "today":
        return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if date_str.lower() == "yesterday":
        return (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def load_audit_log(audit_log_path: str) -> List[Dict[str, Any]]:
    entries = []
    if not os.path.exists(audit_log_path):
        return entries
    with open(audit_log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                entries.append(entry)
            except Exception:
                continue
    return entries

def filter_entries(
    entries: List[Dict[str, Any]],
    date: Optional[str] = None,
    action: Optional[str] = None,
    label: Optional[str] = None,
    email_id: Optional[str] = None,
    dry_run: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    result = []
    date_dt = parse_date(date) if date else None
    for entry in entries:
        try:
            # Date filter
            if date_dt:
                ts = entry.get("timestamp")
                if not ts:
                    continue
                try:
                    entry_dt = datetime.strptime(ts[:10], "%Y-%m-%d")
                except Exception:
                    continue
                if entry_dt < date_dt or entry_dt >= date_dt + timedelta(days=1):
                    continue
            # Action filter
            if action and entry.get("action") != action:
                continue
            # Label filter
            if label and entry.get("label") != label:
                continue
            # Email ID filter
            if email_id and entry.get("email_id") != email_id:
                continue
            # Dry run filter
            if dry_run is not None and entry.get("dry_run") != dry_run:
                continue
            result.append(entry)
        except Exception:
            continue
    return result

def print_entries(entries: List[Dict[str, Any]]):
    if not entries:
        print("No matching audit log entries found.")
        return
    for entry in entries:
        print(json.dumps(entry, indent=2, ensure_ascii=False))

def restore_action(entry: Dict[str, Any], logger):
    # Stub: In real implementation, this would call Gmail API to revert the action
    logger.info(f"Restoring action for email_id={entry.get('email_id')}, action={entry.get('action')}, label={entry.get('label')}")
    print(f"TODO: Restore action for email_id={entry.get('email_id')} (action={entry.get('action')}, label={entry.get('label')})")
    print("      [Gmail API call would be made here to revert the action]")
    # TODO: Implement Gmail API call to restore/revert the action
    # TODO: Handle edge cases (e.g., email already deleted, label missing, etc.)

def export_stats(entries: List[Dict[str, Any]], fmt: str):
    if fmt == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=entries[0].keys() if entries else [])
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)
        print(output.getvalue())
    else:
        print(json.dumps(entries, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Audit and restore Gmail automation actions.")
    parser.add_argument("--date", type=str, help="Filter by date (YYYY-MM-DD, 'today', 'yesterday')")
    parser.add_argument("--action", type=str, help="Filter by action type (e.g., LABEL_AND_ARCHIVE, TRASH)")
    parser.add_argument("--label", type=str, help="Filter by label")
    parser.add_argument("--email-id", type=str, help="Filter by email ID")
    parser.add_argument("--dry-run", action="store_true", help="Show only dry-run actions")
    parser.add_argument("--restore", action="store_true", help="Restore/revert the specified action(s)")
    parser.add_argument("--stats", action="store_true", help="Export stats for filtered actions")
    parser.add_argument("--format", type=str, default="json", choices=["json", "csv"], help="Export format for stats (json/csv)")
    args = parser.parse_args()

    # Load settings
    settings = load_settings(SETTINGS_PATH)
    audit_log_path = settings.get("audit", {}).get("audit_log_path", "logs/audit.log")
    log_dir = settings.get("paths", {}).get("logs", "logs")
    log_config.init_logging(log_level=None, log_dir=log_dir, log_file_name="audit_tool.log")
    logger = log_config.get_logger("audit_tool")

    logger.info("Starting audit_tool.py")
    logger.debug(f"Loaded settings: {settings}")

    # Load audit log
    try:
        entries = load_audit_log(audit_log_path)
        logger.info(f"Loaded {len(entries)} audit log entries from {audit_log_path}")
    except Exception as e:
        logger.error(f"Failed to load audit log: {e}")
        print(f"Error: Failed to load audit log: {e}")
        sys.exit(1)

    # Filter entries
    filtered = filter_entries(
        entries,
        date=args.date,
        action=args.action,
        label=args.label,
        email_id=args.email_id,
        dry_run=args.dry_run if args.dry_run else None,
    )
    logger.info(f"Filtered to {len(filtered)} entries with filters: date={args.date}, action={args.action}, label={args.label}, email_id={args.email_id}, dry_run={args.dry_run}")

    # Stats export
    if args.stats:
        export_stats(filtered, args.format)
        logger.info(f"Exported stats in format: {args.format}")
        return

    # Restore/revert actions
    if args.restore:
        if not filtered:
            print("No matching entries to restore.")
            logger.warning("No matching entries to restore.")
            return
        for entry in filtered:
            try:
                restore_action(entry, logger)
            except Exception as e:
                logger.error(f"Failed to restore action for email_id={entry.get('email_id')}: {e}")
                print(f"Error: Failed to restore action for email_id={entry.get('email_id')}: {e}")
        return

    # Default: print filtered entries
    print_entries(filtered)
    logger.info("Printed filtered entries.")

    # TODO: Add GUI integration (see settings['user_interface']['enable_gui'])
    # TODO: Add advanced restoration logic (batch, confirmation, etc.)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"Fatal error: {e}")
        traceback.print_exc()
        try:
            logger = log_config.get_logger("audit_tool")
            logger.error(f"Fatal error: {e}")
        except Exception:
            pass
        sys.exit(1)