import os
import sys
import json
import time
import subprocess
import traceback
from datetime import datetime, timedelta

from log_config import init_logging, get_logger
from pid_utils import PIDFileManager
from gmail_lm_cleaner import GmailLMCleaner
from gmail_api_utils import GmailEmailManager, get_gmail_service
import audit_tool
from cron_utils import CronScheduler # Import CronScheduler
import email_cleanup
from exceptions import (
    GmailAPIError, EmailProcessingError, LLMConnectionError, 
    AuthenticationError, ConfigurationError, handle_exception_with_logging
)

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
    logger.info("Triggering batch analysis (LM Studio).")
    if not gmail_cleaner:
        logger.warning("GmailLMCleaner not initialized. Skipping batch analysis.")
        return False

    def _batch_analysis_task():
        # Import LM Studio functions
        from lm_studio_integration import analyze_email_subjects_with_lm_studio, update_config_from_lm_analysis
        
        # Run LM Studio analysis using existing exported data or fresh export
        logger.info("Running LM Studio analysis on email subjects...")
        analysis_result = analyze_email_subjects_with_lm_studio(use_existing_export=True)
        
        if analysis_result:
            logger.info(f"LM Studio analysis completed with {len(analysis_result)} categorizations")
            
            # Update configuration based on analysis results
            config_updated = update_config_from_lm_analysis(analysis_result, settings_path)
            
            if config_updated:
                logger.info("Configuration successfully updated from LM Studio analysis")
                return True
            else:
                logger.warning("Configuration update failed, but analysis completed")
                return False
        else:
            logger.error("LM Studio analysis failed or returned no results")
            return False

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
        process_new_emails_batch(gmail_cleaner, email_manager, batch_size)
        return True

    try:
        return _retry_wrapper(_realtime_processing_task)
    except Exception as e:
        logger.error(f"Real-time processing failed after retries: {e}")
        logger.debug(traceback.format_exc())
        return False

def export_emails_for_analysis(export_dir, gmail_cleaner):
    """Export email subjects for batch analysis with Gemini."""
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

def run_gemini_analysis_on_export(export_path, output_dir):
    """Run Gemini analysis on exported email subjects."""
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

def process_new_emails_batch(gmail_cleaner, email_manager, batch_size=50):
    """Process a batch of new emails with LLM analysis and action execution."""
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
            except EmailProcessingError as processing_e:
                processing_e.log_error(logger)
                audit_tool.log_action("ERROR", msg_id, "Processing Failed", f"Processing error: {processing_e.message}")
                continue  # Continue to next email on processing errors
            except LLMConnectionError as llm_e:
                llm_e.log_error(logger)
                audit_tool.log_action("ERROR", msg_id, "LLM Failed", f"LLM error: {llm_e.message}")
                continue  # Continue to next email on LLM errors
            except GmailAPIError as api_e:
                api_e.log_error(logger)
                audit_tool.log_action("ERROR", msg_id, "API Failed", f"API error: {api_e.message}")
                continue  # Continue to next email on API errors
            except Exception as email_e:
                logger.error(f"Unexpected error processing email ID {msg_id}: {email_e}")
                logger.debug(traceback.format_exc())
                audit_tool.log_action("ERROR", msg_id, "Unexpected Error", f"Error: {email_e}")
                continue

    except GmailAPIError as api_e:
        api_e.log_error(logger)
        logger.error("Gmail API error during batch retrieval - may need re-authentication")
    except Exception as e:
        logger.error(f"Unexpected error during real-time email processing: {e}")
        logger.debug(traceback.format_exc())

def run_email_cleanup(gmail_service, settings_path):
    """Run email cleanup based on retention policies."""
    logger = get_logger(__name__)
    logger.info("Starting scheduled email cleanup process.")
    
    try:
        # Load current settings
        settings = load_settings(settings_path)
        
        # Identify emails for cleanup
        eligible_emails = email_cleanup.identify_emails_for_cleanup(settings, gmail_service)
        
        total_eligible = sum(len(emails) for emails in eligible_emails.values())
        if total_eligible == 0:
            logger.info("No emails eligible for cleanup based on retention policies.")
            return True
        
        logger.info(f"Found {total_eligible} emails eligible for cleanup: "
                   f"TRASH={len(eligible_emails.get('TRASH', []))}, "
                   f"DELETE={len(eligible_emails.get('DELETE', []))}, "
                   f"ARCHIVE={len(eligible_emails.get('ARCHIVE', []))}")
        
        # Execute cleanup actions
        results = email_cleanup.cleanup_emails(
            settings, 
            gmail_service, 
            dry_run=settings.get("email_cleanup", {}).get("dry_run", False)
        )
        
        # Log results with detailed breakdown for main log
        if results:
            total_actions = results.get('TRASH', 0) + results.get('DELETE', 0) + results.get('ARCHIVE', 0)
            error_count = results.get('ERRORS', 0)
            
            # Detailed breakdown for main automation log
            logger.info(f"Email cleanup results breakdown:")
            logger.info(f"  - Emails moved to trash: {results.get('TRASH', 0)}")
            logger.info(f"  - Emails permanently deleted: {results.get('DELETE', 0)}")
            logger.info(f"  - Emails archived: {results.get('ARCHIVE', 0)}")
            logger.info(f"  - Errors encountered: {error_count}")
            logger.info(f"  - Total actions performed: {total_actions}")
            
            if error_count > 0:
                logger.warning(f"Some cleanup actions failed. Check detailed logs for specifics.")
                return error_count == 0  # Return True only if no errors
            return True
        else:
            logger.error("Email cleanup execution returned no results")
            return False
            
    except Exception as e:
        logger.error(f"Error during email cleanup: {e}")
        logger.debug(traceback.format_exc())
        return False

def check_job_prerequisites(job_name, settings, logger):
    """
    Check if prerequisites are met for a specific job.
    
    Args:
        job_name (str): Name of the job to check
        settings (dict): Application settings
        logger: Logger instance
    
    Returns:
        tuple: (can_run: bool, reason: str)
    """
    if job_name == "batch_analysis":
        # Check if LM Studio is reachable
        lm_studio_endpoint = settings.get("api", {}).get("lm_studio", {}).get("endpoint", "http://localhost:1234")
        try:
            import requests
            response = requests.get(f"{lm_studio_endpoint}/v1/models", timeout=5)
            if response.status_code != 200:
                return False, f"LM Studio models endpoint check failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"LM Studio not reachable for batch analysis: {e}"
        
        # Check export directory exists
        export_dir = settings.get("paths", {}).get("exports", "exports")
        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir, exist_ok=True)
                logger.info(f"Created export directory: {export_dir}")
            except Exception as e:
                return False, f"Cannot create export directory: {e}"
    
    elif job_name == "realtime_processing":
        # Check if LM Studio is reachable
        lm_studio_endpoint = settings.get("api", {}).get("lm_studio", {}).get("endpoint", "http://localhost:1234")
        try:
            import requests
            response = requests.get(f"{lm_studio_endpoint}/health", timeout=5)
            if response.status_code != 200:
                return False, f"LM Studio health check failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"LM Studio not reachable: {e}"
    
    elif job_name == "email_cleanup":
        # Check if cleanup is enabled
        cleanup_enabled = settings.get("email_cleanup", {}).get("enable_cleanup", True)
        if not cleanup_enabled:
            return False, "Email cleanup is disabled in settings"
        
        # Check retention settings
        retention_settings = settings.get("retention", {})
        if not retention_settings:
            return False, "No retention policies configured"
    
    return True, "Prerequisites met"

def log_job_result_to_main_log(job_name, success, duration, details, logger):
    """
    Log job results to the main automation log for unified tracking.
    
    Args:
        job_name (str): Name of the job
        success (bool): Whether the job succeeded
        duration (timedelta): How long the job took
        details (str): Additional details about the job result
        logger: Logger instance
    """
    status = "SUCCESS" if success else "FAILED"
    
    logger.info(f"=== JOB EXECUTION SUMMARY ===")
    logger.info(f"Job: {job_name}")
    logger.info(f"Status: {status}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Details: {details}")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    logger.info(f"=== END JOB SUMMARY ===")

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
        print(f"Unexpected error during settings loading: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logging
    log_dir = settings.get("paths", {}).get("logs", "logs")
    log_file = DEFAULT_LOG_FILE
    init_logging(log_dir=log_dir, log_file_name=log_file)
    logger = get_logger(__name__)
    
    # Initialize PID file management
    try:
        with PIDFileManager(process_name="autonomous_runner") as pid_manager:
            logger.info("Autonomous runner started with PID file management.")
            _run_main_loop(settings, logger)
    except RuntimeError as e:
        logger.error(f"Failed to start autonomous runner: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in autonomous runner: {e}")
        sys.exit(1)

def _run_main_loop(settings, logger):
    """Main loop logic extracted for PID file management."""
    
    # Initialize Gmail API service
    gmail_service = None
    try:
        gmail_service = get_gmail_service()
        if gmail_service:
            logger.info("Gmail API service initialized successfully.")
        else:
            logger.error("Failed to get Gmail API service.")
            return
    except AuthenticationError as auth_e:
        auth_e.log_error(logger)
        logger.critical("Gmail authentication failed. Check credentials and token files.")
        return
    except GmailAPIError as api_e:
        api_e.log_error(logger)
        logger.critical("Gmail API initialization failed.")
        return
    except Exception as e:
        logger.error(f"Unexpected error initializing Gmail API service: {e}")
        logger.debug(traceback.format_exc())
        return

    # Initialize GmailLMCleaner and GmailEmailManager
    gmail_cleaner = None
    email_manager = None
    try:
        gmail_cleaner = GmailLMCleaner(service=gmail_service)
        email_manager = GmailEmailManager(service=gmail_service)
        logger.info("GmailLMCleaner and GmailEmailManager initialized successfully.")
    except ConfigurationError as config_e:
        config_e.log_error(logger)
        logger.critical("Configuration error during cleaner initialization.")
        return
    except AuthenticationError as auth_e:
        auth_e.log_error(logger)
        logger.critical("Authentication error during cleaner initialization.")
        return
    except Exception as e:
        logger.error(f"Unexpected error initializing GmailLMCleaner or GmailEmailManager: {e}")
        logger.debug(traceback.format_exc())
        return

    # Scheduling config
    # Use reasonable cron expressions for the jobs
    jobs_config = {
        "batch_analysis": "0 3 * * *",  # Daily at 3 AM UTC
        "realtime_processing": "*/5 * * * *", # Every 5 minutes
        "email_cleanup": "0 2 * * 0"  # Weekly on Sunday at 2 AM UTC
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
                logger.info(f"Checking prerequisites for job: {job.name}")
                
                # Check prerequisites before running job
                can_run, prereq_reason = check_job_prerequisites(job.name, settings, logger)
                if not can_run:
                    logger.warning(f"Skipping job '{job.name}': {prereq_reason}")
                    scheduler.update_job(job.name, status="skipped")
                    continue
                
                logger.info(f"Prerequisites met, executing job: {job.name}")
                job_start_time = datetime.now()
                success = False
                job_details = ""
                
                try:
                    if job.name == "batch_analysis":
                        success = run_batch_analysis(gmail_cleaner, export_dir, SETTINGS_PATH)
                        job_details = f"Export dir: {export_dir}"
                    elif job.name == "realtime_processing":
                        success = run_realtime_processing(gmail_cleaner, email_manager, batch_size=50)
                        job_details = "Batch size: 50"
                    elif job.name == "email_cleanup":
                        success = run_email_cleanup(gmail_service, SETTINGS_PATH)
                        job_details = "Retention policy applied"
                    else:
                        logger.warning(f"Unknown job '{job.name}' found in scheduler. Skipping.")
                        continue
                    
                    # Calculate duration and log results
                    job_duration = datetime.now() - job_start_time
                    
                    if success:
                        scheduler.update_job(job.name, status="success")
                        logger.info(f"Job '{job.name}' completed successfully in {job_duration}")
                        log_job_result_to_main_log(job.name, True, job_duration, job_details, logger)
                    else:
                        scheduler.update_job(job.name, status="error")
                        logger.error(f"Job '{job.name}' failed after {job_duration}")
                        log_job_result_to_main_log(job.name, False, job_duration, f"Job failed: {job_details}", logger)
                except (GmailAPIError, EmailProcessingError, LLMConnectionError) as job_e:
                    job_e.log_error(logger)
                    scheduler.update_job(job.name, status="error")
                    # These are recoverable errors, continue with next job
                except AuthenticationError as auth_e:
                    auth_e.log_error(logger)
                    scheduler.update_job(job.name, status="error") 
                    logger.critical(f"Authentication failed for job '{job.name}'. System may need re-authentication.")
                    time.sleep(300)  # Wait 5 minutes before retrying on auth errors
                except Exception as job_e:
                    logger.error(f"Unexpected error executing job '{job.name}': {job_e}")
                    logger.debug(traceback.format_exc())
                    scheduler.update_job(job.name, status="error")

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down gracefully...")
            break
        except (GmailAPIError, LLMConnectionError) as recoverable_e:
            recoverable_e.log_error(logger)
            logger.warning("Recoverable error in main loop, continuing after delay...")
            time.sleep(30)  # Brief pause for recoverable errors
        except AuthenticationError as auth_e:
            auth_e.log_error(logger)
            logger.critical("Authentication error in main loop. Manual intervention required.")
            time.sleep(3600)  # Wait 1 hour before retrying on auth errors
        except Exception as e:
            logger.critical(f"Critical unexpected error in main loop: {e}")
            logger.debug(traceback.format_exc())
            # Sleep longer on critical error to prevent rapid-fire failures
            time.sleep(60)

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