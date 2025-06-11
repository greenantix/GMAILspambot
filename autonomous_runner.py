import os
import sys
import json
import time
import subprocess
import traceback
from datetime import datetime, timedelta

from log_config import init_logging, get_logger
from gmail_lm_cleaner import GmailLMCleaner
from gmail_api_utils import GmailEmailManager, get_gmail_service
import audit_tool
from cron_utils import CronScheduler # Import CronScheduler

SETTINGS_PATH = "config/settings.json"
DEFAULT_LOG_FILE = "automation.log"

def load_settings(settings_path):
    """Loads settings from a JSON file."""
    try:
        with open(settings_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Settings file not found at {settings_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Settings file at {settings_path} is not a valid JSON.")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while loading settings: {e}")

def save_settings(settings, settings_path):
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2, sort_keys=False)

# Removed get_next_batch_time as it's replaced by CronScheduler

def _retry_wrapper(func, max_retries=3, delay_seconds=5, *args, **kwargs):
    logger = get_logger(__name__)
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying {func.__name__} in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
            else:
                logger.error(f"All {max_retries} attempts failed for {func.__name__}.")
                raise # Re-raise the last exception

def run_batch_analysis(gmail_cleaner, export_dir, settings_path):
    logger = get_logger(__name__)
    logger.info("Triggering batch analysis (Gemini).")
    if not gmail_cleaner:
        logger.warning("GmailLMCleaner not initialized. Skipping batch analysis.")
        return False

    def _batch_analysis_task():
        export_path = stub_export_emails(export_dir, gmail_cleaner)
        if export_path:
            gemini_output_path = stub_run_gemini_analysis(export_path, export_dir)
            run_gemini_config_updater(gemini_output_path, settings_path)
        return True

    try:
        return _retry_wrapper(_batch_analysis_task)
    except Exception as e:
        logger.error(f"Batch analysis failed after retries: {e}")
        logger.debug(traceback.format_exc())
        return False

def run_realtime_processing(gmail_cleaner, email_manager, batch_size=50):
    logger = get_logger(__name__)
    logger.info("Triggering real-time email processing.")

    def _realtime_processing_task():
        stub_process_new_emails(gmail_cleaner, email_manager, batch_size)
        return True

    try:
        return _retry_wrapper(_realtime_processing_task)
    except Exception as e:
        logger.error(f"Real-time processing failed after retries: {e}")
        logger.debug(traceback.format_exc())
        return False

def stub_export_emails(export_dir, gmail_cleaner):
    logger = get_logger(__name__)
    export_filename = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    export_path = os.path.join(export_dir, export_filename)
    
    logger.info(f"Exporting email subjects to {export_path} for batch analysis.")
    
    try:
        # Ensure the export directory exists
        os.makedirs(export_dir, exist_ok=True)
        
        # Call the export_subjects method from GmailLMCleaner
        exported_file_path = gmail_cleaner.export_subjects(
            max_emails=1000, # Or load from settings if needed
            days_back=30,   # Or load from settings if needed
            output_file=export_path
        )
        if exported_file_path:
            logger.info(f"Successfully exported emails to {exported_file_path}.")
            return exported_file_path
        else:
            logger.error("Email export failed, no file path returned.")
            return None
    except IOError as e:
        logger.error(f"File I/O error during email export to {export_path}: {e}")
        logger.debug(traceback.format_exc())
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during email export: {e}")
        logger.debug(traceback.format_exc())
        return None

def stub_run_gemini_analysis(export_path, output_dir):
    logger = get_logger(__name__)
    gemini_output_filename = f"gemini_output_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    gemini_output_path = os.path.join(output_dir, gemini_output_filename)

    logger.info(f"Running Gemini analysis on exported subjects from {export_path}.")

    try:
        # Initialize GmailLMCleaner to access analyze_with_gemini
        # Note: This will attempt to load settings and set up Gmail service,
        # but for analysis, only the analyze_with_gemini method is strictly needed.
        # Ensure GEMINI_API_KEY is set in .env for this to work.
        gmail_cleaner = GmailLMCleaner()
        
        # Perform Gemini analysis
        gemini_rules = gmail_cleaner.analyze_with_gemini(subjects_file=export_path)

        if gemini_rules:
            # Save the resulting JSON rules to a file
            os.makedirs(output_dir, exist_ok=True)
            with open(gemini_output_path, "w") as f:
                json.dump(gemini_rules, f, indent=2)
            logger.info(f"Gemini analysis results saved to {gemini_output_path}.")
            return gemini_output_path
        else:
            logger.error("Gemini analysis did not return any rules.")
            return None
    except (IOError, OSError) as e:
        logger.error(f"File I/O error during Gemini analysis or saving results: {e}")
        logger.debug(traceback.format_exc())
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error during Gemini analysis (possibly malformed LLM output): {e}")
        logger.debug(traceback.format_exc())
        return None
    except ValueError as e: # Catch issues related to missing API keys or invalid config during GmailLMCleaner init
        logger.error(f"Configuration error during Gemini analysis setup: {e}")
        logger.debug(traceback.format_exc())
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini analysis: {e}")
        logger.debug(traceback.format_exc())
        return None

def run_gemini_config_updater(gemini_output_path, settings_path):
    logger = get_logger(__name__)
    try:
        cmd = [
            sys.executable, "gemini_config_updater.py",
            "--gemini-output", gemini_output_path,
            "--settings", settings_path
        ]
        logger.info(f"Invoking gemini_config_updater.py with {gemini_output_path}")
        
        # Using check=True to raise CalledProcessError for non-zero exit codes
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Gemini config update complete.")
    except FileNotFoundError:
        logger.error(f"Error: gemini_config_updater.py not found at {cmd[1]}. Ensure it's in the PATH or current directory.")
        logger.debug(traceback.format_exc())
    except subprocess.CalledProcessError as e:
        logger.error(f"gemini_config_updater.py failed with exit code {e.returncode}: {e.stderr}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"An unexpected error occurred while running gemini_config_updater.py: {e}")
        logger.debug(traceback.format_exc())

def stub_process_new_emails(gmail_cleaner, email_manager, batch_size=50):
    logger = get_logger(__name__)
    logger.info(f"Processing new emails (batch_size={batch_size}).")

    if not gmail_cleaner or not email_manager:
        logger.error("GmailLMCleaner or GmailEmailManager not initialized. Cannot process emails.")
        return

    try:
        # Retrieve a batch of unprocessed emails from the inbox
        # Using 'UNREAD' to focus on new emails, and 'INBOX' to ensure they are in the primary inbox
        emails = email_manager.list_emails(query="is:unread in:inbox", max_results=batch_size)
        
        if not emails:
            logger.info("No new emails to process.")
            return

        logger.info(f"Found {len(emails)} new emails to process.")

        for i, email_msg in enumerate(emails, 1):
            msg_id = email_msg['id']
            logger.info(f"[{i}/{len(emails)}] Processing email ID: {msg_id}")
            
            try:
                email_data = gmail_cleaner.get_email_content(msg_id)
                if not email_data:
                    logger.warning(f"Could not retrieve content for email ID: {msg_id}. Skipping.")
                    audit_tool.log_action("WARNING", msg_id, "Skipped", "Could not retrieve email content")
                    continue

                logger.info(f"  Subject: {email_data['subject'][:70]}...")
                logger.info(f"  From: {email_data['sender']}")

                # Analyze email with local LLM
                decision = gmail_cleaner.analyze_email_with_llm(email_data)
                action = decision.get('action', 'KEEP')
                reason = decision.get('reason', 'No specific reason provided by LLM.')
                
                logger.info(f"  LLM Decision: Action='{action}', Reason='{reason}'")

                # Execute the recommended action and log to audit
                success = gmail_cleaner.execute_action(
                    email_data['id'],
                    action,
                    reason,
                    log_callback=audit_tool.log_action
                )
                if not success:
                    logger.error(f"Failed to execute action '{action}' for email ID: {msg_id}")
                    audit_tool.log_action("ERROR", msg_id, action, f"Failed to execute action: {reason}")
            except Exception as email_e:
                logger.error(f"Error processing individual email ID {msg_id}: {email_e}")
                logger.debug(traceback.format_exc())
                audit_tool.log_action("ERROR", msg_id, "Processing Failed", f"Error: {email_e}")
                continue # Continue to the next email even if one fails

    except Exception as e:
        logger.error(f"Error during real-time email processing batch retrieval: {e}")
        logger.debug(traceback.format_exc())

def main():
    # Load settings
    try:
        settings = load_settings(SETTINGS_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unhandled error occurred during settings loading: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logging
    log_dir = settings.get("paths", {}).get("logs", "logs")
    log_file = DEFAULT_LOG_FILE
    init_logging(log_dir=log_dir, log_file_name=log_file)
    logger = get_logger(__name__)
    logger.info("Autonomous runner started.")

    # Initialize Gmail API service
    gmail_service = None
    try:
        gmail_service = get_gmail_service()
        if gmail_service:
            logger.info("Gmail API service initialized successfully.")
        else:
            logger.error("Failed to get Gmail API service.")
            sys.exit(1) # Exit if Gmail service cannot be initialized
    except Exception as e:
        logger.error(f"Failed to initialize Gmail API service: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1) # Exit if Gmail service cannot be initialized

    # Initialize GmailLMCleaner and GmailEmailManager
    gmail_cleaner = None
    email_manager = None
    try:
        gmail_cleaner = GmailLMCleaner(service=gmail_service) # Pass service to cleaner
        email_manager = GmailEmailManager(service=gmail_service) # Pass service to manager
        logger.info("GmailLMCleaner and GmailEmailManager initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize GmailLMCleaner or GmailEmailManager: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1) # Exit if core components fail to initialize

    # Scheduling config
    # Use reasonable cron expressions for the jobs
    jobs_config = {
        "batch_analysis": "0 3 * * *",  # Daily at 3 AM UTC
        "realtime_processing": "*/5 * * * *" # Every 5 minutes
    }
    export_dir = settings.get("paths", {}).get("exports", "exports")
    rules_dir = settings.get("paths", {}).get("rules", "rules") # Not directly used in main loop, but good to keep

    # Initialize CronScheduler
    scheduler = CronScheduler(jobs_config)
    logger.info("CronScheduler initialized with jobs: %s", ", ".join(jobs_config.keys()))

    # Main loop
    while True:
        try:
            due_jobs = scheduler.get_due_jobs()
            if due_jobs:
                logger.info(f"Found {len(due_jobs)} job(s) due: {[job.name for job in due_jobs]}")
            
            for job in due_jobs:
                logger.info(f"Executing scheduled job: {job.name}")
                success = False
                try:
                    if job.name == "batch_analysis":
                        success = run_batch_analysis(gmail_cleaner, export_dir, SETTINGS_PATH)
                    elif job.name == "realtime_processing":
                        success = run_realtime_processing(gmail_cleaner, email_manager, batch_size=50)
                    else:
                        logger.warning(f"Unknown job '{job.name}' found in scheduler. Skipping.")
                        continue
                    
                    if success:
                        scheduler.update_job(job.name, status="success")
                        logger.info(f"Job '{job.name}' completed successfully.")
                    else:
                        scheduler.update_job(job.name, status="error")
                        logger.error(f"Job '{job.name}' failed.")
                except Exception as job_e:
                    logger.error(f"Error executing job '{job.name}': {job_e}")
                    logger.debug(traceback.format_exc())
                    scheduler.update_job(job.name, status="error") # Mark job as error even if it re-raises

        except Exception as e:
            logger.critical(f"Critical error in main loop, attempting graceful shutdown: {e}")
            logger.debug(traceback.format_exc())
            # Consider adding a mechanism for graceful shutdown or alerting here
            # For now, we'll just log and continue, but in a real system,
            # you might want to break the loop or trigger a system restart.
            time.sleep(60) # Sleep longer on critical error to prevent rapid-fire failures

        # Sleep for a shorter, fixed interval to allow for more responsive scheduling checks
        sleep_interval_seconds = 30
        logger.debug(f"Sleeping for {sleep_interval_seconds} seconds.")
        time.sleep(sleep_interval_seconds)

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