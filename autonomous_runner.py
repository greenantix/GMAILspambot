import os
import sys
import json
import time
import subprocess
import traceback
from datetime import datetime, timedelta

from log_config import init_logging, get_logger

SETTINGS_PATH = "settings.json"
DEFAULT_LOG_FILE = "automation.log"

def load_settings(settings_path):
    with open(settings_path, "r") as f:
        return json.load(f)

def save_settings(settings, settings_path):
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2, sort_keys=False)

def get_next_batch_time(last_run, cron_str):
    # Only supports weekly cron: "0 3 * * 0" (Sundays at 3am)
    # For extensibility, parse cron_str if needed
    now = datetime.utcnow()
    if last_run is None:
        # Run immediately if never run
        return now
    # Find next Sunday 3am UTC after last_run
    days_ahead = 6 - last_run.weekday()  # Sunday=6
    if days_ahead <= 0:
        days_ahead += 7
    next_sunday = (last_run + timedelta(days=days_ahead)).replace(hour=3, minute=0, second=0, microsecond=0)
    if next_sunday <= now:
        next_sunday += timedelta(weeks=1)
    return next_sunday

def stub_export_emails(export_dir):
    # Stub: Export emails for batch analysis
    export_path = os.path.join(export_dir, f"analysis_{datetime.utcnow().strftime('%Y%m%d')}.txt")
    # TODO: Implement actual export logic (call export_subjects.py)
    logger = get_logger(__name__)
    logger.info(f"Stub: Exporting emails to {export_path} (not implemented).")
    # Simulate export file creation
    with open(export_path, "w") as f:
        f.write("# Stub email export\n")
    return export_path

def stub_run_gemini_analysis(export_path, output_dir):
    # Stub: Run Gemini analysis on exported emails
    gemini_output_path = os.path.join(output_dir, f"gemini_output_{datetime.utcnow().strftime('%Y%m%d')}.json")
    logger = get_logger(__name__)
    logger.info(f"Stub: Running Gemini analysis on {export_path} (not implemented).")
    # Simulate Gemini output
    stub_output = {
        "label_schema": {
            "create": ["BILLS", "SHOPPING"],
            "delete": ["OLD_PROMO_2023"],
            "rename": {"MISC": "PERSONAL"}
        },
        "category_rules": {
            "BILLS": {
                "keywords": ["invoice", "receipt"],
                "senders": ["billing@"],
                "action": "LABEL_AND_ARCHIVE"
            }
        },
        "auto_operations": {
            "delete_after_days": {"NEWSLETTERS": 30},
            "auto_delete_senders": ["noreply@spam.com"],
            "never_touch": ["security@bank.com"]
        }
    }
    with open(gemini_output_path, "w") as f:
        json.dump(stub_output, f, indent=2)
    return gemini_output_path

def run_gemini_config_updater(gemini_output_path, settings_path):
    logger = get_logger(__name__)
    try:
        cmd = [
            sys.executable, "gemini_config_updater.py",
            "--gemini-output", gemini_output_path,
            "--settings", settings_path
        ]
        logger.info(f"Invoking gemini_config_updater.py with {gemini_output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"gemini_config_updater.py failed: {result.stderr}")
        else:
            logger.info("Gemini config update complete.")
    except Exception as e:
        logger.error(f"Error running gemini_config_updater.py: {e}")
        logger.debug(traceback.format_exc())

def stub_process_new_emails(batch_size=50):
    logger = get_logger(__name__)
    logger.info(f"Stub: Processing new emails (batch_size={batch_size}) (not implemented).")
    # TODO: Implement real-time email processing using LM Studio and current rules

def main():
    # Load settings
    try:
        settings = load_settings(SETTINGS_PATH)
    except Exception as e:
        print(f"Failed to load settings: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logging
    log_dir = settings.get("paths", {}).get("logs", "logs")
    log_file = DEFAULT_LOG_FILE
    init_logging(log_dir=log_dir, log_file_name=log_file)
    logger = get_logger(__name__)
    logger.info("Autonomous runner started.")

    # Scheduling config
    batch_cron = settings.get("automation", {}).get("batch_analysis_cron", "0 3 * * 0")
    realtime_interval = settings.get("automation", {}).get("realtime_processing_interval_minutes", 15)
    export_dir = settings.get("paths", {}).get("exports", "exports")
    rules_dir = settings.get("paths", {}).get("rules", "rules")

    # State tracking
    last_batch_run = None
    last_realtime_run = None

    # Main loop
    while True:
        now = datetime.utcnow()
        try:
            # Batch analysis (weekly, per cron)
            next_batch_time = get_next_batch_time(last_batch_run, batch_cron)
            if now >= next_batch_time:
                logger.info("Triggering batch analysis (Gemini).")
                try:
                    export_path = stub_export_emails(export_dir)
                    gemini_output_path = stub_run_gemini_analysis(export_path, export_dir)
                    run_gemini_config_updater(gemini_output_path, SETTINGS_PATH)
                    last_batch_run = now
                except Exception as e:
                    logger.error(f"Batch analysis failed: {e}")
                    logger.debug(traceback.format_exc())
            else:
                logger.debug(f"Next batch analysis scheduled for {next_batch_time} UTC.")

            # Real-time processing (every N minutes)
            if (last_realtime_run is None or
                (now - last_realtime_run).total_seconds() >= realtime_interval * 60):
                logger.info("Triggering real-time email processing.")
                try:
                    stub_process_new_emails(batch_size=50)
                    last_realtime_run = now
                except Exception as e:
                    logger.error(f"Real-time processing failed: {e}")
                    logger.debug(traceback.format_exc())
            else:
                logger.debug("Waiting for next real-time processing window.")

        except Exception as e:
            logger.error(f"Main loop error: {e}")
            logger.debug(traceback.format_exc())

        # Sleep until next real-time interval
        logger.info(f"Sleeping for {realtime_interval} minutes.")
        time.sleep(realtime_interval * 60)

if __name__ == "__main__":
    """
    Autonomous Runner for Gmail Automation System

    - Periodically triggers batch analysis (Gemini) and real-time email processing (LM Studio).
    - Loads configuration from settings.json.
    - Initializes logging using log_config.py.
    - Logs all major actions, errors, and scheduling events.
    - Provides robust error handling and clear TODOs for unimplemented integrations.

    Scheduling:
    - By default, uses an internal loop with time.sleep.
    - For production, consider using cron or systemd for more robust scheduling.
      See claude.md for example systemd and cron configurations.
    """
    main()