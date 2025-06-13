# LLMdiver Enhanced Analysis - 2025-06-12 19:30:19.733897

## Project: GMAILspambot

# Repository Analysis: GMAILspambot

## Project Information
- Primary Language: python
- Framework: unknown
- Manifests: 1

## Manifest Analysis

### New manifest: /home/greenantix/AI/GMAILspambot/requirements.txt
**Dependencies:** google-api-python-client, google-auth, google-auth-oauthlib, google-auth-httplib2, google-generativeai, flask, requests, python-dotenv, pandas, croniter, colorama, PySide6



## Code Analysis
This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.
The content has been processed where comments have been removed, empty lines have been removed, content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: *.py, *.js, *.ts, *.jsx, *.tsx, *.sh
- Files matching these patterns are excluded: *.md, *.log, *.tmp, node_modules, __pycache__, .git
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Code comments have been removed from supported file types
- Empty lines have been removed from all files
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
audit_tool.py
autonomous_runner.py
build-flatpak.sh
bulk_processor.py
check_status.py
cron_utils.py
email_cleanup.py
exceptions.py
gemini_config_updater.py
gmail_api_utils.py
gmail_lm_cleaner.py
gmail-cleaner.sh
health_check.py
llmdiver_daemon.py
lm_studio_integration.py
log_config.py
pid_utils.py
progress_monitor.py
qml_main.py
setup.sh
start_llmdiver.sh
start_qml.sh
start_stable.sh
start.sh
stop.sh
test_automation.py
test_llmdiver.sh
test_lm_studio.py
test_oauth_scopes.py
test_real_categorization.py
test-qml.sh
```

# Files

## File: audit_tool.py
```python
SETTINGS_PATH = "config/settings.json"
def load_settings(path: str) -> dict
⋮----
content = f.read()
content = "\n".join(line for line in content.splitlines() if not line.strip().startswith("//") and not line.strip().startswith("/*") and not line.strip().startswith("*") and not line.strip().endswith("*/"))
⋮----
def parse_date(date_str: str) -> Optional[datetime]
def load_audit_log(audit_log_path: str) -> List[Dict[str, Any]]
⋮----
entries = []
⋮----
entry = json.loads(line)
⋮----
result = []
date_dt = parse_date(date) if date else None
⋮----
ts = entry.get("timestamp")
⋮----
entry_dt = datetime.strptime(ts[:10], "%Y-%m-%d")
⋮----
def print_entries(entries: List[Dict[str, Any]])
def _log_audit_action(action_type: str, email_id: str, label: str, reason: str, dry_run: bool = False)
⋮----
settings = load_settings(SETTINGS_PATH)
audit_log_path = settings.get("audit", {}).get("audit_log_path", "logs/audit.log")
⋮----
audit_entry = {
⋮----
def log_action(action_type: str, email_id: str, label: str, reason: str, dry_run: bool = False)
def restore_action(audit_entry: Dict[str, Any], gmail_manager: GmailEmailManager, logger)
⋮----
email_id = audit_entry.get("email_id")
action_type = audit_entry.get("action")
label = audit_entry.get("label")
timestamp = audit_entry.get("timestamp")
⋮----
# Verify email still exists and is accessible
email_data = gmail_manager.get_email(email_id)
⋮----
success = False
⋮----
# Restore from trash by removing TRASH label and adding INBOX
success = gmail_manager.modify_labels(email_id, add_labels=['INBOX'], remove_labels=['TRASH'])
⋮----
# To restore, add INBOX label and remove the custom label
success = gmail_manager.modify_labels(email_id, add_labels=['INBOX'], remove_labels=[label])
⋮----
# Restore by adding INBOX label back
success = gmail_manager.modify_labels(email_id, add_labels=['INBOX'], remove_labels=[])
⋮----
# Remove the label that was added
success = gmail_manager.modify_labels(email_id, add_labels=[], remove_labels=[label])
⋮----
# Log the restoration action
⋮----
def export_stats(entries: List[Dict[str, Any]], fmt: str)
⋮----
output = io.StringIO()
writer = csv.DictWriter(output, fieldnames=entries[0].keys() if entries else [])
⋮----
def main()
⋮----
parser = argparse.ArgumentParser(description="Audit and restore Gmail automation actions.")
⋮----
args = parser.parse_args()
# Load settings
⋮----
log_dir = settings.get("paths", {}).get("logs", "logs")
⋮----
logger = log_config.get_logger("audit_tool")
⋮----
# Load audit log
⋮----
entries = load_audit_log(audit_log_path)
⋮----
# Filter entries
filtered = filter_entries(
⋮----
# Stats export
⋮----
# Restore/revert actions
⋮----
# Initialize Gmail API service and manager
⋮----
gmail_service = get_gmail_service()
⋮----
gmail_manager = GmailEmailManager(gmail_service)
⋮----
# Default: print filtered entries
⋮----
# TODO: Add GUI integration (see settings['user_interface']['enable_gui'])
```

## File: autonomous_runner.py
```python
SETTINGS_PATH = "config/settings.json"
DEFAULT_LOG_FILE = "automation.log"
def load_settings(settings_path)
def save_settings(settings, settings_path)
def _retry_wrapper(func, max_retries=3, delay_seconds=5, *args, **kwargs)
⋮----
logger = get_logger(__name__)
⋮----
raise # Re-raise the last exception
def run_batch_analysis(gmail_cleaner, export_dir, settings_path)
⋮----
def _batch_analysis_task()
⋮----
# Import LM Studio functions
⋮----
# Run LM Studio analysis using existing exported data or fresh export
⋮----
analysis_result = analyze_email_subjects_with_lm_studio(use_existing_export=True)
⋮----
# Update configuration based on analysis results
config_updated = update_config_from_lm_analysis(analysis_result, settings_path)
⋮----
def run_realtime_processing(gmail_cleaner, email_manager, batch_size=50)
⋮----
def _realtime_processing_task()
⋮----
def export_emails_for_analysis(export_dir, gmail_cleaner)
⋮----
export_filename = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
export_path = os.path.join(export_dir, export_filename)
⋮----
# Ensure the export directory exists
⋮----
# Call the export_subjects method from GmailLMCleaner
exported_file_path = gmail_cleaner.export_subjects(
⋮----
max_emails=1000, # Or load from settings if needed
days_back=30,   # Or load from settings if needed
⋮----
def run_gemini_analysis_on_export(export_path, output_dir)
⋮----
gemini_output_filename = f"gemini_output_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
gemini_output_path = os.path.join(output_dir, gemini_output_filename)
⋮----
# Initialize GmailLMCleaner to access analyze_with_gemini
# Note: This will attempt to load settings and set up Gmail service,
# but for analysis, only the analyze_with_gemini method is strictly needed.
# Ensure GEMINI_API_KEY is set in .env for this to work.
gmail_cleaner = GmailLMCleaner()
# Perform Gemini analysis
gemini_rules = gmail_cleaner.analyze_with_gemini(subjects_file=export_path)
⋮----
# Save the resulting JSON rules to a file
⋮----
except ValueError as e: # Catch issues related to missing API keys or invalid config during GmailLMCleaner init
⋮----
def run_gemini_config_updater(gemini_output_path, settings_path)
⋮----
cmd = [
⋮----
# Using check=True to raise CalledProcessError for non-zero exit codes
result = subprocess.run(cmd, capture_output=True, text=True, check=True)
⋮----
def process_new_emails_batch(gmail_cleaner, email_manager, batch_size=50)
⋮----
# Retrieve a batch of unprocessed emails from the inbox
# Using 'UNREAD' to focus on new emails, and 'INBOX' to ensure they are in the primary inbox
emails = email_manager.list_emails(query="is:unread in:inbox", max_results=batch_size)
⋮----
msg_id = email_msg['id']
⋮----
email_data = gmail_cleaner.get_email_content(msg_id)
⋮----
# Analyze email with local LLM
decision = gmail_cleaner.analyze_email_with_llm(email_data)
action = decision.get('action', 'KEEP')
reason = decision.get('reason', 'No specific reason provided by LLM.')
⋮----
# Execute the recommended action and log to audit
success = gmail_cleaner.execute_action(
⋮----
continue  # Continue to next email on processing errors
⋮----
continue  # Continue to next email on LLM errors
⋮----
continue  # Continue to next email on API errors
⋮----
def run_email_cleanup(gmail_service, settings_path)
⋮----
# Load current settings
settings = load_settings(settings_path)
# Identify emails for cleanup
eligible_emails = email_cleanup.identify_emails_for_cleanup(settings, gmail_service)
total_eligible = sum(len(emails) for emails in eligible_emails.values())
⋮----
# Execute cleanup actions
results = email_cleanup.cleanup_emails(
# Log results with detailed breakdown for main log
⋮----
total_actions = results.get('TRASH', 0) + results.get('DELETE', 0) + results.get('ARCHIVE', 0)
error_count = results.get('ERRORS', 0)
# Detailed breakdown for main automation log
⋮----
return error_count == 0  # Return True only if no errors
⋮----
def check_job_prerequisites(job_name, settings, logger)
⋮----
# Check if LM Studio is reachable
lm_studio_endpoint = settings.get("api", {}).get("lm_studio", {}).get("endpoint", "http://localhost:1234")
⋮----
response = requests.get(f"{lm_studio_endpoint}/v1/models", timeout=5)
⋮----
# Check export directory exists
export_dir = settings.get("paths", {}).get("exports", "exports")
⋮----
response = requests.get(f"{lm_studio_endpoint}/health", timeout=5)
⋮----
# Check if cleanup is enabled
cleanup_enabled = settings.get("email_cleanup", {}).get("enable_cleanup", True)
⋮----
# Check retention settings
retention_settings = settings.get("retention", {})
⋮----
def log_job_result_to_main_log(job_name, success, duration, details, logger)
⋮----
status = "SUCCESS" if success else "FAILED"
⋮----
def main()
⋮----
# Load settings
⋮----
settings = load_settings(SETTINGS_PATH)
⋮----
# Initialize logging
log_dir = settings.get("paths", {}).get("logs", "logs")
log_file = DEFAULT_LOG_FILE
⋮----
# Initialize PID file management
⋮----
def _run_main_loop(settings, logger)
⋮----
# Initialize Gmail API service
gmail_service = None
⋮----
gmail_service = get_gmail_service()
⋮----
# Initialize GmailLMCleaner and GmailEmailManager
gmail_cleaner = None
email_manager = None
⋮----
gmail_cleaner = GmailLMCleaner(service=gmail_service)
email_manager = GmailEmailManager(service=gmail_service)
⋮----
# Scheduling config
# Use reasonable cron expressions for the jobs
jobs_config = {
⋮----
"batch_analysis": "0 3 * * *",  # Daily at 3 AM UTC
"realtime_processing": "*/5 * * * *", # Every 5 minutes
"email_cleanup": "0 2 * * 0"  # Weekly on Sunday at 2 AM UTC
⋮----
rules_dir = settings.get("paths", {}).get("rules", "rules") # Not directly used in main loop, but good to keep
# Initialize CronScheduler
scheduler = CronScheduler(jobs_config)
⋮----
# Main loop
⋮----
due_jobs = scheduler.get_due_jobs()
⋮----
# Check prerequisites before running job
⋮----
job_start_time = datetime.now()
success = False
job_details = ""
⋮----
success = run_batch_analysis(gmail_cleaner, export_dir, SETTINGS_PATH)
job_details = f"Export dir: {export_dir}"
⋮----
success = run_realtime_processing(gmail_cleaner, email_manager, batch_size=50)
job_details = "Batch size: 50"
⋮----
success = run_email_cleanup(gmail_service, SETTINGS_PATH)
job_details = "Retention policy applied"
⋮----
# Calculate duration and log results
job_duration = datetime.now() - job_start_time
⋮----
# These are recoverable errors, continue with next job
⋮----
time.sleep(300)  # Wait 5 minutes before retrying on auth errors
⋮----
time.sleep(30)  # Brief pause for recoverable errors
⋮----
time.sleep(3600)  # Wait 1 hour before retrying on auth errors
⋮----
# Sleep longer on critical error to prevent rapid-fire failures
⋮----
# Sleep for a shorter, fixed interval to allow for more responsive scheduling checks
sleep_interval_seconds = 30
```

## File: build-flatpak.sh
```bash
set -e
echo "🏗️  Building Gmail Cleaner Flatpak..."
if ! command -v flatpak-builder &> /dev/null; then
    echo "❌ flatpak-builder not found. Installing..."
    sudo apt update
    sudo apt install -y flatpak-builder
fi
if ! flatpak remotes | grep -q flathub; then
    echo "📦 Adding Flathub remote..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi
echo "📚 Installing required runtimes..."
flatpak install -y flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
echo "🧹 Cleaning previous build..."
rm -rf build-dir .flatpak-builder
echo "📝 Updating requirements.txt with PySide6..."
if ! grep -q "PySide6" requirements.txt; then
    echo "PySide6>=6.5.0" >> requirements.txt
fi
echo "🔨 Building Flatpak package..."
flatpak-builder build-dir flatpak/com.greenantix.GmailCleaner.json --force-clean --ccache
echo "📦 Installing locally..."
flatpak-builder --user --install --force-clean build-dir flatpak/com.greenantix.GmailCleaner.json
echo "✅ Build complete!"
echo ""
echo "🚀 To run your app:"
echo "   flatpak run com.greenantix.GmailCleaner"
echo ""
echo "📱 Or find it in your applications menu: 'Gmail Cleaner'"
echo ""
echo "🗂️  To uninstall:"
echo "   flatpak uninstall com.greenantix.GmailCleaner"
echo ""
echo "📦 To create a bundle for distribution:"
echo "   flatpak build-bundle ~/.local/share/flatpak/repo gmail-cleaner.flatpak com.greenantix.GmailCleaner"
```

## File: bulk_processor.py
```python
def run_server_side_filter_pass(cleaner, log_callback)
⋮----
stats = apply_existing_filters_to_backlog(
processed_count = stats.get('server_side_processed', 0)
filter_stats = stats.get('filter_stats', {})
⋮----
all_filters = fetch_and_parse_filters(cleaner.service)
filter_map = {f['id']: f for f in all_filters}
⋮----
filter_details = filter_map.get(filter_id)
query_str = f"'{filter_details['query']}'" if filter_details else f"ID: {filter_id}"
⋮----
applied_labels = set()
⋮----
def setup_logging()
⋮----
log_dir = "logs"
⋮----
def progress_callback(processed, total)
⋮----
percentage = (processed / total) * 100
⋮----
def log_callback(message)
def pause_callback()
def main()
⋮----
parser = argparse.ArgumentParser(description="Bulk Email Processor with Server-Side Filtering")
⋮----
args = parser.parse_args()
logger = setup_logging()
⋮----
def _run_bulk_processing(batch_size, logger)
⋮----
cleaner = GmailLMCleaner()
⋮----
inbox_label = cleaner.service.users().labels().get(userId='me', id='INBOX').execute()
total_unread = inbox_label.get('messagesUnread', 0)
⋮----
total_unread = 0
start_time = datetime.now()
⋮----
exclusion_query = "is:unread in:inbox"
⋮----
label_exclusions = [f"-label:{label.replace(' ', '-')}" for label in applied_labels]
⋮----
llm_stats = {}
⋮----
llm_stats = cleaner.process_email_backlog(
⋮----
end_time = datetime.now()
duration = end_time - start_time
total_server_processed = server_stats.get('server_side_processed', 0)
total_llm_processed = llm_stats.get('total_processed', 0)
total_processed = total_server_processed + total_llm_processed
⋮----
rate = total_processed / max(duration.total_seconds(), 1)
⋮----
inbox_label_after = cleaner.service.users().labels().get(userId='me', id='INBOX').execute()
remaining_unread = inbox_label_after.get('messagesUnread', 0)
⋮----
processed_percentage = ((total_unread - remaining_unread) / total_unread) * 100
⋮----
success = main()
```

## File: check_status.py
```python
def get_process_status()
⋮----
result = subprocess.run(['pgrep', '-f', 'bulk_processor.py'],
⋮----
pid = result.stdout.strip()
⋮----
def get_gmail_status()
⋮----
service = get_gmail_service()
⋮----
inbox = service.users().labels().get(userId='me', id='INBOX').execute()
unread = inbox.get('messagesUnread', 0)
⋮----
def get_processing_stats()
⋮----
lines = f.readlines()
processed_count = sum(1 for line in lines if 'Processed:' in line)
⋮----
timestamp = line.split()[0:2]
latest_time = ' '.join(timestamp)
⋮----
latest_time = "No recent activity"
⋮----
def main()
⋮----
log_files = ['logs/email_processing.log', 'logs/bulk_processing.log']
⋮----
size = os.path.getsize(log_file) / 1024 / 1024
```

## File: cron_utils.py
```python
DEFAULT_STATE_FILE = os.path.join("data", "automation_state.json")
ISOFORMAT = "%Y-%m-%dT%H:%M:%S.%f"
logger = get_logger(__name__)
class CronJob
⋮----
def __init__(self, name: str, cron_expr: str, last_run: Optional[datetime] = None, status: str = "never")
def next_run(self, from_time: Optional[datetime] = None) -> datetime
⋮----
ref = from_time or datetime.utcnow()
⋮----
def is_due(self, now: Optional[datetime] = None) -> bool
⋮----
now = now or datetime.utcnow()
⋮----
next_run = croniter(self.cron_expr, self.last_run).get_next(datetime)
⋮----
def update_last_run(self, run_time: Optional[datetime] = None, status: str = "success")
def missed_runs(self, now: Optional[datetime] = None) -> int
⋮----
missed = 0
ref = self.last_run
⋮----
next_run = croniter(self.cron_expr, ref).get_next(datetime)
⋮----
ref = next_run
⋮----
def to_dict(self) -> Dict[str, Any]
⋮----
@classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CronJob"
⋮----
last_run = None
⋮----
last_run = datetime.fromisoformat(data["last_run"])
⋮----
class CronScheduler
⋮----
def __init__(self, jobs_config: Dict[str, str], state_file: str = DEFAULT_STATE_FILE)
def _load_jobs(self, jobs_config: Dict[str, str])
def _load_state(self)
⋮----
state = json.load(f)
⋮----
def _save_state(self)
⋮----
state = {name: job.to_dict() for name, job in self.jobs.items()}
⋮----
def get_due_jobs(self, now: Optional[datetime] = None) -> List[CronJob]
⋮----
due = []
⋮----
def update_job(self, job_name: str, run_time: Optional[datetime] = None, status: str = "success")
def get_next_run(self, job_name: str, from_time: Optional[datetime] = None) -> Optional[datetime]
def get_job_status(self, job_name: str) -> Optional[str]
def get_last_run(self, job_name: str) -> Optional[datetime]
def get_missed_runs(self, job_name: str, now: Optional[datetime] = None) -> int
def reload(self)
def save(self)
⋮----
jobs = {
scheduler = CronScheduler(jobs)
due_jobs = scheduler.get_due_jobs()
```

## File: email_cleanup.py
```python
logger = get_logger(__name__)
DEFAULT_RETENTION_DAYS = 365
TRASH_RETENTION_DAYS = 30
def load_settings(settings_path: str = "config/settings.json") -> Dict[str, Any]
def get_retention_policy(settings: Dict[str, Any]) -> Dict[str, int]
⋮----
default_days = settings.get("retention", {}).get("default_days", DEFAULT_RETENTION_DAYS)
label_action_mappings = settings.get("label_action_mappings", {})
⋮----
label_mgr = GmailLabelManager(service)
email_mgr = GmailEmailManager(service)
⋮----
retention_policy = get_retention_policy(settings)
⋮----
max_results = settings.get("gmail", {}).get("max_results_per_query", 500)
as_of = as_of or datetime.utcnow()
eligible: Dict[str, List[str]] = {"TRASH": [], "DELETE": [], "ARCHIVE": []}
⋮----
retention_days = retention_policy.get(label, DEFAULT_RETENTION_DAYS)
cutoff_date = (as_of - timedelta(days=retention_days)).strftime("%Y/%m/%d")
label_id = label_mgr.list_labels().get(label)
⋮----
query = f"label:{label} before:{cutoff_date}"
emails = email_mgr.list_emails(label_ids=[label_id], query=query, max_results=max_results)
msg_ids = [msg["id"] for msg in emails]
⋮----
eligible = identify_emails_for_cleanup(settings, service)
results = {"TRASH": 0, "DELETE": 0, "ARCHIVE": 0, "ERRORS": 0}
⋮----
trash_retention = settings.get("retention", {}).get("trash_days", TRASH_RETENTION_DAYS)
cutoff_date = (datetime.utcnow() - timedelta(days=trash_retention)).strftime("%Y/%m/%d")
query = f"in:trash before:{cutoff_date}"
max_results = settings.get("gmail", {}).get("max_results_per_query", 1000)
emails = email_mgr.list_emails(query=query, max_results=max_results)
⋮----
deleted = 0
⋮----
settings = load_settings(settings_path)
service = get_gmail_service()
results = cleanup_emails(settings, service, dry_run=dry_run)
trash_deleted = empty_trash(settings, service, dry_run=dry_run)
⋮----
# For scheduled jobs, use cron_utils.CronScheduler to track last run and status.
```

## File: exceptions.py
```python
class GmailCleanerException(Exception)
⋮----
def log_error(self, logger: logging.Logger)
class GmailAPIError(GmailCleanerException)
⋮----
details = {}
⋮----
recovery_suggestion = self._get_recovery_suggestion(api_error)
⋮----
def _get_recovery_suggestion(self, api_error: Optional[Exception]) -> str
⋮----
error_str = str(api_error).lower()
⋮----
class EmailProcessingError(GmailCleanerException)
⋮----
recovery_suggestion = "Skip this email and continue processing, or retry with different parameters"
⋮----
class LLMConnectionError(GmailCleanerException)
⋮----
recovery_suggestion = self._get_llm_recovery_suggestion(service_name)
⋮----
def _get_llm_recovery_suggestion(self, service_name: Optional[str]) -> str
class FilterProcessingError(GmailCleanerException)
⋮----
recovery_suggestion = "Check filter syntax and Gmail API permissions for filter management"
⋮----
class AuthenticationError(GmailCleanerException)
⋮----
def __init__(self, message: str, auth_type: Optional[str] = None)
⋮----
recovery_suggestion = self._get_auth_recovery_suggestion(auth_type)
⋮----
def _get_auth_recovery_suggestion(self, auth_type: Optional[str]) -> str
class ConfigurationError(GmailCleanerException)
⋮----
recovery_suggestion = "Check configuration file format and required fields"
⋮----
class ValidationError(GmailCleanerException)
⋮----
recovery_suggestion = "Check input data format and required fields"
```

## File: gemini_config_updater.py
```python
SETTINGS_PATH = "config/settings.json"
def load_settings(settings_path)
def save_settings(settings, settings_path)
def load_gemini_output(path)
def update_label_schema(gmail_label_manager, label_rules, logger)
⋮----
label_id = gmail_label_manager.create_label(label_name)
⋮----
def update_category_rules(category_rules, rules_dir, logger)
⋮----
rule_path = os.path.join(rules_dir, f"{label}.json")
⋮----
def update_auto_operations(auto_ops, rules_dir, logger)
⋮----
auto_ops_path = os.path.join(rules_dir, "auto_operations.json")
⋮----
def update_label_action_mappings(settings, category_rules, logger)
⋮----
updated = False
⋮----
action = rule.get("action")
⋮----
updated = True
⋮----
def main()
⋮----
parser = argparse.ArgumentParser(description="Update system config/rules from Gemini output JSON.")
⋮----
args = parser.parse_args()
⋮----
settings = load_settings(args.settings)
⋮----
log_dir = settings.get("paths", {}).get("logs", "logs")
⋮----
logger = get_logger(__name__)
gemini_output_path = args.gemini_output
⋮----
gemini = load_gemini_output(gemini_output_path)
⋮----
gmail_service = get_gmail_service()
⋮----
gmail_label_manager = GmailLabelManager(gmail_service)
⋮----
rules_dir = settings.get("paths", {}).get("rules", "rules")
⋮----
updated = update_label_action_mappings(settings, gemini.get("category_rules", {}), logger)
```

## File: gmail_api_utils.py
```python
logger = get_logger(__name__)
SCOPES = [
def exponential_backoff_retry(func, max_retries: int = 3, base_delay: float = 1.0)
⋮----
delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
⋮----
def get_gmail_service(credentials_path: str = "config/credentials.json", token_path: str = "config/token.json", max_retries: int = 3)
⋮----
creds = None
⋮----
creds = Credentials.from_authorized_user_file(token_path, SCOPES)
⋮----
flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
creds = flow.run_local_server(port=0)
⋮----
service = build('gmail', 'v1', credentials=creds)
⋮----
profile = service.users().getProfile(userId='me').execute()
⋮----
class GmailLabelManager
⋮----
def __init__(self, service)
def refresh_label_cache(self)
⋮----
def _fetch_labels()
⋮----
results = self.service.users().labels().list(userId='me').execute()
⋮----
def create_label(self, label_name: str, label_color: Optional[Dict[str, str]] = None) -> Optional[str]
⋮----
label_object = {
⋮----
def _create_label()
⋮----
created = exponential_backoff_retry(_create_label)
⋮----
def delete_label(self, label_name: str) -> bool
⋮----
label_id = self._label_cache.get(label_name)
⋮----
def rename_label(self, old_name: str, new_name: str) -> bool
⋮----
old_id = self._label_cache.get(old_name)
⋮----
results = self.service.users().messages().list(
message_ids = [m['id'] for m in results.get('messages', [])]
⋮----
new_id = self.create_label(new_name)
⋮----
def list_labels(self) -> Dict[str, str]
class GmailEmailManager
⋮----
def _list_emails()
⋮----
response = exponential_backoff_retry(_list_emails)
messages = response.get('messages', [])
⋮----
def get_email(self, msg_id: str) -> Optional[Dict[str, Any]]
⋮----
def _get_email()
⋮----
msg = exponential_backoff_retry(_get_email)
⋮----
def move_to_trash(self, msg_id: str) -> bool
⋮----
def _move_to_trash()
⋮----
def delete_email(self, msg_id: str) -> bool
def restore_from_trash(self, msg_id: str) -> bool
⋮----
def _restore_from_trash()
⋮----
body = {}
⋮----
def archive_email(self, msg_id: str) -> bool
⋮----
results = {}
batch_size = min(batch_size, 100)
⋮----
chunk = msg_ids[i:i + batch_size]
chunk_results = self._execute_batch_modify_chunk(chunk, add_labels, remove_labels)
⋮----
def execute_batch()
⋮----
batch = BatchHttpRequest()
modify_body = {}
⋮----
def callback(request_id, response, exception)
request = self.service.users().messages().modify(
⋮----
def batch_delete(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]
⋮----
chunk_results = self._execute_batch_delete_chunk(chunk)
⋮----
def _execute_batch_delete_chunk(self, msg_ids: List[str]) -> Dict[str, bool]
⋮----
request = self.service.users().messages().delete(userId='me', id=msg_id)
⋮----
def batch_move_to_trash(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]
def batch_restore_from_trash(self, msg_ids: List[str], batch_size: int = 100) -> Dict[str, bool]
⋮----
chunk_results = self._execute_batch_get_chunk(chunk, format, metadata_headers)
⋮----
get_params = {'userId': 'me', 'id': msg_id, 'format': format}
⋮----
request = self.service.users().messages().get(**get_params)
⋮----
def get_label_id(service, label_name: str) -> Optional[str]
⋮----
results = service.users().labels().list(userId='me').execute()
```

## File: gmail_lm_cleaner.py
```python
SCOPES = [
⋮----
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
⋮----
DEFAULT_SETTINGS = {
class EmailLearningEngine
⋮----
def __init__(self, history_file='logs/categorization_history.json')
def load_history(self)
def save_history(self)
def record_categorization(self, email_data, decision, user_override=None)
⋮----
record = {
⋮----
def suggest_rule_updates(self)
⋮----
suggestions = {
override_patterns = {}
low_confidence_patterns = {}
⋮----
sender = record.get('sender', '').lower()
subject = record.get('subject', '').lower()
llm_action = record.get('llm_action')
user_override = record.get('user_override')
confidence = record.get('confidence', 0.5)
⋮----
correction_key = f"{sender}|{llm_action}→{user_override}"
⋮----
keyword_suggestions = self._extract_keyword_patterns(override_patterns)
⋮----
dominant_category = max(pattern['categories'], key=pattern['categories'].get)
⋮----
total_records = len(self.categorization_history)
total_overrides = len([r for r in self.categorization_history if r.get('user_override')])
low_confidence_count = len([r for r in self.categorization_history if r.get('confidence', 0.5) < 0.7])
⋮----
def _extract_keyword_patterns(self, override_patterns)
⋮----
keyword_suggestions = {}
category_subjects = {}
⋮----
target_cat = pattern['to_category']
⋮----
word_counts = {}
⋮----
words = subject.lower().split()
⋮----
threshold = max(2, len(subjects) * 0.3)
common_keywords = [word for word, count in word_counts.items() if count >= threshold]
⋮----
def detect_new_patterns(self)
⋮----
review_emails = []
⋮----
patterns = []
sender_clusters = self._cluster_by_sender_domain(review_emails)
subject_clusters = self._cluster_by_subject_keywords(review_emails)
⋮----
pattern = self._analyze_domain_pattern(domain, emails)
⋮----
pattern = self._analyze_subject_pattern(keyword_group, emails)
⋮----
def _cluster_by_sender_domain(self, emails)
⋮----
domain_clusters = {}
⋮----
sender = email['sender']
⋮----
domain = sender.split('@')[-1].strip()
⋮----
domain = sender
⋮----
def _cluster_by_subject_keywords(self, emails)
⋮----
keyword_groups = {}
⋮----
subject = email['subject']
words = [w for w in subject.split() if len(w) > 3 and w.isalpha()]
⋮----
keyword_combo = ' '.join(words[i:j+1])
⋮----
filtered_groups = {}
⋮----
def _analyze_domain_pattern(self, domain, emails)
⋮----
subjects = [e['subject'] for e in emails]
avg_confidence = sum(e['confidence'] for e in emails) / len(emails)
common_words = self._extract_common_words(subjects)
suggested_category = self._suggest_category_for_domain(domain, common_words)
⋮----
def _analyze_subject_pattern(self, keyword_group, emails)
⋮----
unique_senders = list(set(e['sender'] for e in emails))
⋮----
suggested_category = self._suggest_category_for_keywords(keyword_group)
⋮----
def _extract_common_words(self, subjects)
⋮----
words = [w.lower() for w in subject.split() if len(w) > 3 and w.isalpha()]
⋮----
def _suggest_category_for_domain(self, domain, common_words)
⋮----
domain_lower = domain.lower()
words_text = ' '.join(common_words).lower()
⋮----
def _suggest_category_for_keywords(self, keywords)
⋮----
keywords_lower = keywords.lower()
⋮----
def record_categorization(self, email_data, llm_decision, user_override=None)
⋮----
'subject': email_data.get('subject', '')[:100],  # Truncate for privacy
⋮----
# Keep only last 1000 records to prevent file from growing too large
⋮----
suggestions = []
⋮----
# Group by sender and final action
sender_patterns = {}
⋮----
final_action = record.get('final_action', '')
⋮----
# Find consistent patterns (senders with 3+ emails in same category)
⋮----
total_emails = sum(actions.values())
⋮----
# Find most common action for this sender
most_common_action = max(actions, key=actions.get)
most_common_count = actions[most_common_action]
# If 80% or more go to the same category, suggest a rule
consistency_ratio = most_common_count / total_emails
⋮----
# Find keyword patterns in corrected emails
user_corrections = [r for r in self.categorization_history if r.get('user_override')]
⋮----
keyword_patterns = {}
⋮----
# Extract potential keywords (2+ character words)
words = [word for word in subject.split() if len(word) >= 2 and word.isalpha()]
⋮----
# Find consistent keyword patterns
⋮----
total_count = sum(actions.values())
⋮----
consistency_ratio = most_common_count / total_count
⋮----
# Sort suggestions by confidence and email count
⋮----
return suggestions[:10]  # Return top 10 suggestions
⋮----
review_emails = [r for r in self.categorization_history if r.get('final_action') == 'REVIEW']
⋮----
# Group by domain patterns
⋮----
sender = record.get('sender', '')
⋮----
domain = sender.split('@')[-1].lower()
⋮----
# Extract common subject patterns
subjects = [email.get('subject', '') for email in emails]
⋮----
def get_learning_stats(self)
⋮----
# Calculate accuracy (emails where LLM decision wasn't overridden)
accurate_decisions = sum(1 for r in self.categorization_history if not r.get('user_override'))
accuracy_rate = accurate_decisions / total_records
category_counts = {}
⋮----
category = record.get('final_action', '')
⋮----
top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
⋮----
class GmailLMCleaner
⋮----
def __init__(self, credentials_file='config/credentials.json', token_file='config/token.json', settings_file='config/settings.json')
def load_settings(self)
⋮----
settings = json.load(f)
⋮----
def setup_logging(self)
⋮----
logger = logging.getLogger("GmailCleaner")
⋮----
# File handler with rotation
fh = RotatingFileHandler(
⋮----
# Console handler
ch = logging.StreamHandler()
⋮----
# Formatter
formatter = logging.Formatter(
⋮----
def log_email_processing(self, email_id, subject, decision, reason, confidence=None)
⋮----
confidence_str = f" | Confidence: {confidence:.2f}" if confidence is not None else ""
⋮----
def load_llm_prompts(self)
def save_settings(self)
⋮----
# When saving, ensure llm_prompts are also saved if they were modified
# For this task, we assume llm_prompts are static after initial load
# and only modify the main settings.
⋮----
def setup_gmail_service(self)
⋮----
# Use the unified authentication function from gmail_api_utils
⋮----
# Additional service setup can go here if needed
⋮----
def ensure_gmail_connection(self)
⋮----
# No service exists, set it up
⋮----
# Quick test to see if connection is alive
⋮----
def get_email_content(self, msg_id)
⋮----
message = self.service.users().messages().get(
headers = message.get('payload', {}).get('headers', [])
subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No Subject')
sender = next((h['value'] for h in headers if h.get('name') == 'From'), 'Unknown Sender')
date = next((h['value'] for h in headers if h.get('name') == 'Date'), 'Unknown Date')
body = self.extract_body(message.get('payload', {}))
⋮----
def extract_body(self, payload)
⋮----
body = ""
⋮----
data = part['body']['data']
body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
⋮----
body = base64.urlsafe_b64decode(
⋮----
def is_critical_email(self, email_data)
⋮----
subject = email_data.get('subject', '').lower()
sender = email_data.get('sender', '').lower()
body = email_data.get('body', '').lower()
# Ultra-high priority triggers - expanded and categorized
critical_patterns = {
# Critical sender patterns (only truly urgent stuff) - enhanced
critical_senders = [
⋮----
# Security and fraud
⋮----
# Financial institutions (major ones only)
⋮----
# Critical services
⋮----
# Government and legal
⋮----
# Confidence scoring
confidence_score = 0.0
reasons = []
# Check for critical senders (high confidence)
⋮----
# Check for critical keywords with context scoring
full_text = (subject + ' ' + body).lower()
⋮----
category_matches = 0
⋮----
# Subject matches are more important than body matches
⋮----
# Multiple keywords in same category increase confidence
⋮----
# Check if it's a personal human (moderate confidence)
⋮----
time_sensitive_patterns = ['expires in 24', 'expires today', 'final notice', 'last chance']
⋮----
is_critical = confidence_score >= 0.7
⋮----
def is_priority_email(self, email_data)
⋮----
priority_patterns = self._load_priority_patterns()
⋮----
pattern_confidence = 0.0
⋮----
keyword_matches = 0
⋮----
priority_indicators = [
⋮----
is_priority = confidence_score >= 0.5
⋮----
def _load_priority_patterns(self)
⋮----
config_path = 'config/priority_patterns.json'
⋮----
config = json.load(f)
⋮----
def _is_professional_sender(self, sender)
⋮----
professional_domains = [
free_email_domains = ['@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com', '@aol.com']
is_not_free_email = not any(domain in sender for domain in free_email_domains)
has_professional_pattern = any(pattern in sender for pattern in professional_domains)
⋮----
def is_personal_human_sender(self, sender, email_data)
⋮----
automated_patterns = [
# Personal domain indicators (common personal email services)
personal_domains = [
# Human-like patterns in content
human_language_patterns = [
# Automated content patterns
automated_content_patterns = [
⋮----
# Check for automated sender patterns (strong negative indicator)
⋮----
# Check for personal domains (moderate positive indicator)
⋮----
# Check for human-like language patterns
⋮----
human_patterns_found = sum(1 for pattern in human_language_patterns if pattern in full_text)
⋮----
# Check for automated content patterns (negative indicator)
automated_patterns_found = sum(1 for pattern in automated_content_patterns if pattern in full_text)
⋮----
# Check sender name patterns (first.last@domain suggests human)
sender_local = sender.split('@')[0] if '@' in sender else sender
⋮----
# Could be first.last format
⋮----
# Very short emails are less likely to be human (unless they're replies)
text_length = len(subject) + len(body)
⋮----
is_human = confidence_score > 0.2
⋮----
def is_important_email(self, email_data)
def is_promotional_email(self, email_data)
⋮----
subject_lower = email_data.get('subject', '').lower()
body_lower = email_data.get('body', '').lower()
promo_count = 0
⋮----
def generate_dynamic_llm_prompt(self)
⋮----
labels = self.get_all_gmail_labels()
rules = self.load_all_category_rules()
categories_info = self.format_categories_with_descriptions(labels, rules)
learned_patterns = self.get_learned_patterns()
user_preferences = self.get_user_preferences()
prompt_template = f"""Email categorization assistant. Respond ONLY with valid JSON.
⋮----
def get_all_gmail_labels(self)
⋮----
results = self.service.users().labels().list(userId='me').execute()
labels = results.get('labels', [])
user_labels = []
system_labels = ['INBOX', 'SENT', 'DRAFT', 'TRASH', 'SPAM', 'STARRED', 'IMPORTANT', 'UNREAD']
category_labels = ['BILLS', 'SHOPPING', 'NEWSLETTERS', 'SOCIAL', 'PERSONAL', 'JUNK', 'REVIEW']
⋮----
label_name = label['name']
⋮----
def load_all_category_rules(self)
⋮----
all_rules = {}
⋮----
rules_dir = 'rules'
⋮----
category_name = filename[:-5]
⋮----
rule_data = json.load(f)
⋮----
def format_categories_with_descriptions(self, labels, rules)
⋮----
formatted_categories = []
standard_categories = {
⋮----
description = standard_categories[label_name]
rule_details = ""
⋮----
rule_data = rules[label_name]
keywords = rule_data.get('keywords', [])
senders = rule_data.get('senders', [])
⋮----
def get_learned_patterns(self)
⋮----
patterns = [
⋮----
def get_user_preferences(self)
⋮----
preferences = []
⋮----
important_keywords = self.settings.get('important_keywords', [])
⋮----
promotional_keywords = self.settings.get('promotional_keywords', [])
⋮----
never_delete = self.settings.get('never_delete_senders', [])
⋮----
def get_fallback_prompt(self)
def build_categorization_prompt(self, email_data)
⋮----
base_prompt = self.generate_dynamic_llm_prompt()
email_prompt = f"""
⋮----
def call_lm_studio(self, prompt, timeout=30, max_retries=3)
⋮----
def _make_request()
⋮----
payload = {
model_name = self.settings.get('lm_studio_model', 'meta-llama-3.1-8b-instruct')
⋮----
response = requests.post(
⋮----
result = response.json()
⋮----
choice = result['choices'][0]
⋮----
content = choice['message']['content'].strip()
json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
⋮----
cleaned_json = json_match.group().replace('\n', ' ').replace('\t', ' ')
⋮----
action_match = re.search(r'"action":\s*"([^"]+)"', content)
reason_match = re.search(r'"reason":\s*"([^"]+)"', content)
⋮----
action = action_match.group(1)
reason = reason_match.group(1) if reason_match else "LLM response parsing fallback"
⋮----
delay = (2 ** attempt) + random.uniform(0, 1)
⋮----
delay = (3 ** attempt) + random.uniform(0, 2)
⋮----
delay = 1 + random.uniform(0, 0.5)
⋮----
def validate_llm_decision(self, decision)
⋮----
valid_actions = ["INBOX", "PRIORITY", "BILLS", "SHOPPING", "NEWSLETTERS", "SOCIAL", "PERSONAL", "JUNK", "KEEP", "REVIEW"]
⋮----
action = decision.get('action', 'KEEP').upper()
⋮----
reason = str(decision.get('reason', 'No reason provided'))[:200]
confidence = decision.get('confidence', 0.5)
⋮----
confidence = float(confidence)
confidence = max(0.0, min(1.0, confidence))
⋮----
confidence = 0.5
⋮----
def harvest_existing_filters(self)
⋮----
filters = self.service.users().settings().filters().list(userId='me').execute()
filter_list = filters.get('filter', [])
processed_filters = []
⋮----
criteria = gmail_filter.get('criteria', {})
action = gmail_filter.get('action', {})
filter_rule = {
⋮----
def build_query_from_criteria(self, criteria)
⋮----
query_parts = []
⋮----
def apply_existing_filters_to_backlog(self, log_callback=None, max_emails_per_filter=1000)
⋮----
# Get existing filters
filters = self.harvest_existing_filters()
⋮----
total_processed = 0
⋮----
# Find messages matching this filter
query = f"is:unread in:inbox {filter_rule['query']}"
results = self.service.users().messages().list(
messages = results.get('messages', [])
⋮----
# Apply filter actions in batches
batch_size = 100
⋮----
batch = messages[j:j+batch_size]
message_ids = [msg['id'] for msg in batch]
# Build modify request
modify_request = {}
⋮----
# Apply batch modification
⋮----
def setup_gmail_filters(self, log_callback=None)
⋮----
category_rules = self.settings.get('category_rules', {})
filters_created = 0
⋮----
if category == 'INBOX':  # Skip INBOX - we want these to stay
⋮----
# Create label if it doesn't exist
label_id = self.create_label_if_not_exists(category)
⋮----
# Create filters for sender patterns (only specific, non-generic patterns)
senders = rules.get('senders', [])
# Filter out overly broad patterns that could cause issues
specific_senders = [s for s in senders if not s.startswith('@gmail.com') and not s.startswith('@outlook.com') and not s.startswith('@yahoo.com') and len(s) > 3]
for sender_pattern in specific_senders[:5]:  # Limit to 5 per category to avoid spam
⋮----
filter_criteria = {
filter_action = {
⋮----
'removeLabelIds': ['INBOX']  # Remove from inbox for non-inbox categories
⋮----
# For JUNK category, also mark as spam
⋮----
filter_body = {
# Check if filter already exists to avoid duplicates
existing_filters = self.service.users().settings().filters().list(userId='me').execute()
filter_exists = False
⋮----
filter_exists = True
⋮----
# Create filter with retry logic
success = self._create_filter_with_retry(filter_body)
⋮----
if log_callback and filters_created == 0:  # Only log scope issues once
⋮----
error_msg = str(e)
⋮----
if log_callback and filters_created == 0:  # Only log scope issues once
⋮----
break  # Stop trying if we have scope issues
⋮----
# Create filters for subject keywords (top 3 most specific, avoid generic words)
keywords = rules.get('keywords', [])
generic_words = ['update', 'notification', 'message', 'email', 'info', 'news']
specific_keywords = [kw for kw in keywords if len(kw) > 8 and kw.lower() not in generic_words][:3]  # Longer, more specific keywords
⋮----
# Check if filter already exists
⋮----
def _create_filter_with_retry(self, filter_body, max_retries=3)
⋮----
return False  # Permission issue, don't retry
⋮----
def apply_suggested_filters(self, suggested_filters, log_callback=None)
⋮----
# Build filter criteria
criteria = {}
⋮----
# Build filter action based on action type
action = {}
action_type = filter_spec.get('action', 'label_and_archive')
⋮----
action = {
⋮----
existing_criteria = existing_filter.get('criteria', {})
⋮----
# Create descriptive log message
filter_desc = []
⋮----
def get_available_models(self)
⋮----
response = requests.get(LM_STUDIO_MODELS_URL, timeout=5)
⋮----
data = response.json()
models = [model['id'] for model in data.get('data', [])]
⋮----
def check_email_against_local_rules(self, email_data)
⋮----
rules_dir = "rules"
⋮----
# Get all rule files
rule_files = [f for f in os.listdir(rules_dir) if f.endswith('.json')]
⋮----
rule_path = os.path.join(rules_dir, rule_file)
⋮----
category = rule_file.replace('.json', '').upper()
# Handle both old and new rule formats
⋮----
# Skip list format - this shouldn't happen but handle gracefully
⋮----
# Check sender rules
rule_senders = rule_data.get('senders', [])
⋮----
# Check keywords - handle both old and new format
keywords_data = rule_data.get('keywords', {})
⋮----
# Old format: keywords is a list
⋮----
# New format: keywords is a dict with subject/body
# Check subject keywords
subject_keywords = keywords_data.get('subject', [])
⋮----
# Check body keywords
body_keywords = keywords_data.get('body', [])
⋮----
# Check domain rules (new format only)
conditions = rule_data.get('conditions', {})
⋮----
sender_domains = conditions.get('sender_domain', [])
sender_domain = sender.split('@')[-1] if '@' in sender else ''
⋮----
# Check exclude keywords (if present, rule doesn't apply)
exclude_keywords = conditions.get('exclude_keywords', [])
⋮----
# This rule doesn't apply, continue to next rule
⋮----
# No exclude keywords matched, continue with other checks if any
⋮----
return None  # No rules matched
⋮----
def analyze_email_with_llm(self, email_data)
⋮----
# Pre-validation
⋮----
# Validate email_data has required fields
required_fields = ['subject', 'sender', 'body', 'date']
⋮----
# Pre-filter based on settings (Tier 0: Basic Safety Checks)
⋮----
# Tier 1 & 2: Deterministic Local Rules (Highest Priority)
# Server-side filters are applied before this function is even called
local_rule_decision = self.check_email_against_local_rules(email_data)
⋮----
# Tier 3: Heuristic-Based Classification (Fast & High-Confidence)
⋮----
# Check for promotional content (part of heuristics)
⋮----
# Prepare safe data for LLM
safe_email_data = {
# Build LLM prompt
prompt = self.build_categorization_prompt(safe_email_data)
# Call LLM with longer timeout for stability
⋮----
decision = self.call_lm_studio(prompt, timeout=30)
⋮----
email_id = email_data.get('id', 'unknown')
email_subject = email_data.get('subject', 'No Subject')
error = EmailProcessingError(
⋮----
def create_label_if_not_exists(self, label_name)
⋮----
# Get existing labels
⋮----
# Check if label exists
⋮----
# Create new label
label_object = {
created_label = self.service.users().labels().create(
⋮----
# Check if it's a label conflict error - try to find existing label
⋮----
# Re-fetch labels to find the existing one
⋮----
def execute_action(self, email_id, action, reason, log_callback=None)
⋮----
# Move to trash
⋮----
# Keep in inbox, add important label
⋮----
# Move to appropriate folder/label
label_id = self.create_label_if_not_exists(action)
⋮----
# Remove from inbox and add to category label
⋮----
folder_emoji = {
emoji = folder_emoji.get(action, '📁')
⋮----
def process_inbox(self, log_callback=None)
⋮----
# Process emails from all categories, not just inbox
⋮----
date_after = (datetime.now() - timedelta(days=self.settings['days_back'])).strftime('%Y/%m/%d')
query = f'after:{date_after}'
⋮----
query = 'is:unread'  # Focus on unread emails from all categories
⋮----
email_data = self.get_email_content(msg['id'])
⋮----
subject_text = email_data.get('subject', 'No Subject')[:60]
sender_text = email_data.get('sender', 'Unknown Sender')
⋮----
decision = self.analyze_email_with_llm(email_data)
# Record the categorization decision for learning
⋮----
# Log the processing details
⋮----
# After processing, suggest rule updates based on the session
⋮----
def process_email_backlog(self, batch_size=100, older_than_days=0, query_override=None, log_callback=None, progress_callback=None, pause_callback=None)
⋮----
# Build query for unread emails from ALL categories
⋮----
query = query_override
⋮----
query_parts = ['is:unread']
⋮----
date_before = (datetime.now() - timedelta(days=older_than_days)).strftime('%Y/%m/%d')
⋮----
query = ' '.join(query_parts)
# Initialize statistics
stats = {
⋮----
# Ensure Gmail connection before starting
⋮----
# Get total count first for accurate progress
⋮----
total_messages = 0
⋮----
# Get the number of unread messages in the inbox.
# This is a reliable count for the most common use case.
# If the query is more complex (e.g., with 'older_than'), this count is an approximation.
inbox_label_data = self.service.users().labels().get(userId='me', id='INBOX').execute()
total_messages = inbox_label_data.get('messagesUnread', 0)
⋮----
progress_callback(0, total_messages) # Update progress bar immediately
⋮----
stats['total_found'] = 0 # We'll count as we go
# Efficient batch processing: fetch large chunks, process in smaller batches
next_page_token = None
processed_count = 0
fetch_size = min(500, batch_size * 10)  # Fetch larger chunks efficiently
⋮----
retry_count = 0
max_retries = 3
⋮----
# Fetch large chunk of email IDs efficiently
⋮----
maxResults=fetch_size,  # Fetch efficiently
⋮----
retry_count = 0  # Reset retry counter on success
⋮----
# Wait before retrying (exponential backoff)
wait_time = 2 ** retry_count
⋮----
continue  # Retry the same page
⋮----
# Apply existing Gmail filters before LLM processing
email_ids = [msg['id'] for msg in messages]
filter_result = apply_existing_filters_to_backlog(
# Update statistics with filter results
filter_processed = filter_result['processed_count']
remaining_ids = filter_result['remaining_ids']
filter_stats = filter_result['filter_stats']
⋮----
# Create filtered message list for LLM processing
messages_for_llm = [msg for msg in messages if msg['id'] in remaining_ids]
# Update processed count with filter results
⋮----
# Skip LLM processing if all emails were handled by filters
⋮----
# Very brief pause and continue to next page
⋮----
# Process remaining emails in smaller batches
⋮----
sub_batch = messages_for_llm[i:i+batch_size]
⋮----
# Process each email in this sub-batch
⋮----
# Check for pause
⋮----
# Get email content
⋮----
# Log email being processed (every 10th to avoid spam)
⋮----
subject_preview = email_data.get('subject', 'No Subject')[:50]
⋮----
# Analyze email
⋮----
action = decision['action']
reason = decision['reason']
# Update statistics
⋮----
# Update progress
⋮----
# Show LLM connection status occasionally
⋮----
# Log decision
⋮----
# Execute action
⋮----
None  # Skip detailed action logging to speed up
⋮----
if log_callback and processed_count % 50 == 0:  # Only log errors occasionally
⋮----
# Sub-batch complete
⋮----
percentage = (processed_count / total_messages * 100) if total_messages > 0 else 100
⋮----
# Update final stats for this chunk
⋮----
# Check for next page
next_page_token = results.get('nextPageToken')
⋮----
# Very brief pause to avoid rate limits
⋮----
# Final statistics
elapsed = datetime.now() - stats['start_time']
⋮----
percentage = (count / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0
⋮----
def export_subjects(self, max_emails=1000, days_back=30, output_file='email_subjects.txt')
⋮----
# Use absolute path if not already absolute
⋮----
output_file = os.path.abspath(output_file)
⋮----
date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
# Use broader query to get emails from all categories, not just inbox
⋮----
all_messages = []
⋮----
# Paginate through results to get up to max_emails
⋮----
remaining = max_emails - len(all_messages)
page_size = min(500, remaining)  # Gmail API max is 500 per request
⋮----
page_messages = results.get('messages', [])
⋮----
messages = all_messages[:max_emails]  # Limit to requested amount
⋮----
return output_file # Return output_file even if no messages
⋮----
f.flush()  # Force write to disk
⋮----
headers = message['payload']['headers']
subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
⋮----
f.flush()  # Flush after each write
⋮----
return output_file # Return the path to the exported file
⋮----
return None # Return None on error
def analyze_with_lm_studio(self, subjects_file='email_subjects.txt', progress_callback=None)
⋮----
def update_progress(message)
⋮----
subjects_content = f.read()
email_data = [{"subject": line} for line in subjects_content.splitlines()]
analysis_result = lm_studio.analyze_email_patterns(email_data)
⋮----
filter_rules = lm_studio.generate_filter_rules(analysis_result)
⋮----
def apply_lm_studio_rules(self, rules, log_callback=None)
⋮----
# This is a placeholder for now. In a real implementation, you would
# parse the rules and apply them to your settings or directly to Gmail.
⋮----
def export_and_analyze(self, max_emails=1000, days_back=30)
⋮----
# Export subjects
subjects_file = self.export_subjects(max_emails, days_back)
⋮----
# Analyze with LM Studio
rules = self.analyze_with_lm_studio(subjects_file)
⋮----
# Apply the rules
⋮----
def analyze_unsubscribe_candidates(self, log_callback=None)
⋮----
candidates = {}
⋮----
# Query for unread promotional-looking emails
query = "is:unread category:promotions"
results = self.service.users().messages().list(userId='me', q=query, maxResults=500).execute()
⋮----
sender = email_data['sender']
⋮----
# Filter for high-frequency senders
unsubscribe_list = []
⋮----
if data['count'] > 5: # Arbitrary threshold for "high frequency"
⋮----
def get_detailed_unsubscribe_candidates(self, log_callback=None)
⋮----
# Query for unread promotional and marketing emails
queries = [
⋮----
results = self.service.users().messages().list(userId='me', q=query, maxResults=300).execute()
⋮----
# Remove duplicates
unique_messages = {msg['id']: msg for msg in all_messages}.values()
⋮----
# Show progress every 50 emails
⋮----
subject = email_data['subject']
⋮----
# Keep the most recent subject
⋮----
# Filter for candidates with enough emails to warrant unsubscribing
filtered_candidates = []
⋮----
if data['count'] >= 3:  # At least 3 unread emails
⋮----
# Sort by count (most emails first)
⋮----
def process_unsubscribe_requests(self, candidates, max_tabs=5, auto_process=False)
⋮----
success_count = 0
failed_count = 0
tabs_opened = 0
⋮----
sender = candidate['sender']
message_ids = candidate['message_ids']
⋮----
# Get the most recent message to look for unsubscribe headers
⋮----
latest_msg_id = message_ids[0]  # Assuming most recent is first
unsubscribe_info = self.extract_unsubscribe_info(latest_msg_id)
⋮----
# Check if we should limit browser tabs
⋮----
# No unsubscribe info found, just log it as failed
⋮----
def extract_unsubscribe_info(self, message_id)
⋮----
# Get the message with headers
⋮----
headers = message['payload'].get('headers', [])
# Look for List-Unsubscribe header
list_unsubscribe = None
⋮----
list_unsubscribe = header['value']
⋮----
# Parse the List-Unsubscribe header
# Format is usually: <mailto:unsubscribe@example.com>, <http://example.com/unsubscribe>
⋮----
# Extract URLs
url_matches = re.findall(r'<(https?://[^>]+)>', list_unsubscribe)
# Extract email addresses
email_matches = re.findall(r'<mailto:([^>]+)>', list_unsubscribe)
⋮----
def attempt_unsubscribe(self, unsubscribe_info, sender, auto_process=False)
⋮----
# Send unsubscribe email automatically (only when auto_process=True)
email = unsubscribe_info['emails'][0]
⋮----
success = self.send_unsubscribe_email(email, sender)
⋮----
# Open unsubscribe URL in browser (but limit to prevent tab explosion)
url = unsubscribe_info['urls'][0]  # Use the first URL
⋮----
# For mailto, open email client instead of sending automatically
⋮----
mailto_url = f"mailto:{email}?subject=Unsubscribe&body=Please unsubscribe me from this mailing list."
⋮----
def send_unsubscribe_email(self, unsubscribe_email, sender)
⋮----
# Create the email message
message = email.mime.multipart.MIMEMultipart()
⋮----
message['from'] = 'me'  # Gmail API uses 'me' for the authenticated user
⋮----
# Email body
body = f"""Hello,
⋮----
# Encode the message
raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
# Send via Gmail API
send_message = {'raw': raw_message}
result = self.service.users().messages().send(userId='me', body=send_message).execute()
⋮----
def auto_evolve_system(self, log_callback=None)
⋮----
# 1. Analyze categorization history for patterns and suggest updates
suggested_updates = self.learning_engine.suggest_rule_updates()
⋮----
# In a real implementation, you'd present these to the user for confirmation
⋮----
# 2. Detect new, uncategorized patterns
new_patterns = self.learning_engine.detect_new_patterns()
⋮----
# 3. Monitor filter effectiveness (placeholder)
⋮----
# 4. Suggest filter adjustments (placeholder)
⋮----
def analyze_and_suggest_rules(self, log_callback=None)
⋮----
# Import the backlog analyzer
⋮----
# Analyze recent unread emails to find patterns
analysis_report = analyze_backlog(
⋮----
max_emails=1000  # Analyze up to 1000 recent emails
⋮----
sender_frequency = analysis_report.get('sender_frequency', {})
total_analyzed = analysis_report.get('analysis_summary', {}).get('total_emails_analyzed', 0)
⋮----
# Generate rule suggestions based on high-volume senders
⋮----
# Suggest rules for senders with 10+ emails
⋮----
# Try to categorize the sender based on domain/patterns
suggested_category = self._suggest_category_for_sender(sender)
⋮----
'confidence': min(0.9, 0.5 + (count * 0.02)),  # Higher confidence for more emails
⋮----
# Sort suggestions by email count (highest first)
⋮----
def _suggest_category_for_sender(self, sender_email)
⋮----
sender_lower = sender_email.lower()
# Newsletter patterns
⋮----
# Shopping patterns
⋮----
# Bills/Finance patterns
⋮----
# Social patterns
⋮----
# Check domain patterns
domain = sender_email.split('@')[-1] if '@' in sender_email else ''
⋮----
# Default to NEWSLETTERS for high-volume automated senders
⋮----
class GmailCleanerGUI
⋮----
def __init__(self)
⋮----
# Setup global exception handler for UI
⋮----
# Auto-connect to Gmail on startup
self.root.after(1000, self.auto_connect_gmail)  # Connect after UI loads
def setup_global_exception_handler(self)
⋮----
def handle_exception(exc_type, exc_value, exc_traceback)
⋮----
# Allow keyboard interrupt to work normally
⋮----
# Log the exception
error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
⋮----
# Show user-friendly error dialog
⋮----
# If we can't show a dialog, at least print to console
⋮----
def tkinter_exception_handler(exc, val, tb)
⋮----
def reset_ui_state(self)
def handle_ui_exception(self, exc_type, exc_value, exc_traceback)
⋮----
error_msg = f"UI callback exception: {exc_type.__name__}: {exc_value}"
⋮----
def auto_connect_gmail(self)
def setup_ui_styling(self)
⋮----
style = ttk.Style()
⋮----
bg_color = '#f0f0f0'
accent_color = '#0078d4'
success_color = '#107c10'
warning_color = '#ff8c00'
error_color = '#d13438'
text_color = '#323130'
⋮----
def setup_ui(self)
⋮----
notebook = ttk.Notebook(self.root)
⋮----
dashboard_frame = ttk.Frame(notebook)
⋮----
main_frame = ttk.Frame(notebook)
⋮----
backlog_frame = ttk.Frame(notebook)
⋮----
settings_frame = ttk.Frame(notebook)
⋮----
management_frame = ttk.Frame(notebook)
⋮----
analytics_frame = ttk.Frame(notebook)
⋮----
learning_frame = ttk.Frame(notebook)
⋮----
unsubscribe_frame = ttk.Frame(notebook)
⋮----
def setup_dashboard_tab(self, parent)
⋮----
canvas = tk.Canvas(parent)
scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)
⋮----
welcome_frame = ttk.LabelFrame(scrollable_frame, text="Gmail Intelligent Cleaner Dashboard", padding=10)
⋮----
stats_frame = ttk.LabelFrame(scrollable_frame, text="Quick Statistics", padding=10)
⋮----
stats_grid = ttk.Frame(stats_frame)
⋮----
status_frame = ttk.LabelFrame(scrollable_frame, text="System Status", padding=10)
⋮----
actions_frame = ttk.LabelFrame(scrollable_frame, text="Quick Actions", padding=10)
⋮----
actions_grid = ttk.Frame(actions_frame)
⋮----
activity_frame = ttk.LabelFrame(scrollable_frame, text="Recent Activity", padding=10)
⋮----
refresh_frame = ttk.Frame(scrollable_frame)
⋮----
def refresh_dashboard(self)
⋮----
stats = self.cleaner.learning_engine.get_learning_stats()
⋮----
top_category = stats['top_categories'][0]
⋮----
def update_recent_activity(self)
⋮----
history = self.cleaner.learning_engine.categorization_history
recent_history = history[-10:] if len(history) > 10 else history
⋮----
timestamp = record.get('timestamp', 'Unknown time')
action = record.get('final_action', record.get('llm_action', 'UNKNOWN'))
sender = record.get('sender', 'Unknown sender')[:30]
subject = record.get('subject', 'No subject')[:40]
⋮----
dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
time_str = dt.strftime('%H:%M:%S')
⋮----
time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
activity_line = f"[{time_str}] {action}: {subject}... (from {sender})\n"
⋮----
def setup_main_tab(self, parent)
⋮----
status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
⋮----
control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
⋮----
options_frame = ttk.LabelFrame(parent, text="Options", padding=10)
⋮----
use_existing_cb = ttk.Checkbutton(options_frame, text="Use existing email_subjects.txt (skip re-export)",
⋮----
info_label = ttk.Label(options_frame, text="   ℹ️ Useful for testing or when you have connection issues",
⋮----
log_frame = ttk.LabelFrame(parent, text="Log", padding=10)
⋮----
def setup_backlog_tab(self, parent)
⋮----
status_frame = ttk.LabelFrame(parent, text="Backlog Status", padding=10)
⋮----
config_frame = ttk.LabelFrame(parent, text="Processing Options", padding=10)
⋮----
batch_frame = ttk.Frame(config_frame)
⋮----
batch_spinbox = ttk.Spinbox(batch_frame, from_=10, to=500, width=10, textvariable=self.batch_size_var)
⋮----
age_frame = ttk.Frame(config_frame)
⋮----
age_spinbox = ttk.Spinbox(age_frame, from_=0, to=365, width=10, textvariable=self.older_than_var)
⋮----
mode_frame = ttk.Frame(config_frame)
⋮----
mode_combo = ttk.Combobox(mode_frame, textvariable=self.processing_mode_var,
⋮----
mode_desc_frame = ttk.Frame(config_frame)
⋮----
mode_descriptions = {
⋮----
def update_mode_description(*args)
⋮----
mode = self.processing_mode_var.get()
⋮----
button_frame = ttk.Frame(control_frame)
⋮----
progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
⋮----
stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=10)
⋮----
stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
⋮----
backlog_log_frame = ttk.LabelFrame(parent, text="Processing Log", padding=10)
⋮----
def setup_settings_tab(self, parent)
⋮----
keywords_frame = ttk.LabelFrame(scrollable_frame, text="Important Keywords", padding=10)
⋮----
senders_frame = ttk.LabelFrame(scrollable_frame, text="Important Sender Patterns", padding=10)
⋮----
never_delete_frame = ttk.LabelFrame(scrollable_frame, text="Never Delete Senders", padding=10)
⋮----
proc_frame = ttk.LabelFrame(scrollable_frame, text="Processing Options", padding=10)
⋮----
model_frame = ttk.Frame(proc_frame)
⋮----
button_frame = ttk.Frame(scrollable_frame)
⋮----
oauth_frame = ttk.LabelFrame(scrollable_frame, text="OAuth & Authentication", padding=10)
⋮----
oauth_button_frame = ttk.Frame(oauth_frame)
⋮----
def setup_management_tab(self, parent)
⋮----
mappings_frame = ttk.LabelFrame(scrollable_frame, text="Label Action Mappings", padding=10)
⋮----
labels_frame = ttk.LabelFrame(scrollable_frame, text="Gmail Label Manager", padding=10)
⋮----
label_buttons_frame = ttk.Frame(labels_frame)
⋮----
rules_frame = ttk.LabelFrame(scrollable_frame, text="Rule Viewer/Editor", padding=10)
⋮----
rule_select_frame = ttk.Frame(rules_frame)
⋮----
rule_actions_frame = ttk.Frame(rules_frame)
⋮----
rule_editor_frame = ttk.Frame(rules_frame)
⋮----
category_frame = ttk.Frame(rule_editor_frame)
⋮----
sender_tab = ttk.Frame(self.rule_notebook)
⋮----
keyword_tab = ttk.Frame(self.rule_notebook)
⋮----
advanced_tab = ttk.Frame(self.rule_notebook)
⋮----
def log(self, message)
def connect_gmail(self)
def ensure_cleaner_connection(self)
def process_emails(self)
def _process_emails_thread(self)
⋮----
error_msg = f"Error processing emails: {e}"
⋮----
# Restore UI state
⋮----
def restore_process_ui_state(self)
def export_subjects(self)
⋮----
# Prevent double-clicking
⋮----
# Clear log
⋮----
# Start export in thread to avoid freezing UI
⋮----
def _export_subjects_thread(self)
⋮----
# Update button to show it's working
⋮----
result = self.cleaner.export_subjects(max_emails=500, days_back=30)
⋮----
error_msg = "Export failed - no subjects were exported"
⋮----
error_msg = f"Error exporting subjects: {e}"
⋮----
def restore_export_ui_state(self)
def auto_analyze(self)
def _auto_analyze_thread(self)
⋮----
# Check if we should use existing export or create new one
subjects_file = 'email_subjects.txt'
⋮----
# Use existing export file if it exists
⋮----
# Check if file has content
⋮----
content = f.read().strip()
⋮----
subjects_file = None
⋮----
line_count = len(content.split('\n'))
⋮----
# Export subjects if needed
⋮----
subjects_file = self.cleaner.export_subjects(max_emails=500, days_back=30)
⋮----
error_msg = "Failed to export email subjects. Check your Gmail connection."
⋮----
# Analyze with LM Studio
⋮----
proposed_rules = self.cleaner.analyze_with_lm_studio(subjects_file, progress_callback=self.log)
⋮----
error_msg = "LM Studio analysis failed. Make sure the LM Studio server is running and a model is loaded."
⋮----
# Show confirmation dialog with proposed changes
⋮----
error_msg = f"Unexpected error during auto-analysis: {e}"
⋮----
# Show error dialog to user
⋮----
# Always restore UI state
⋮----
def restore_ui_after_analysis(self)
⋮----
# Re-enable any disabled buttons
⋮----
def setup_filters(self)
⋮----
# Start filter setup in thread to avoid freezing UI
⋮----
def _setup_filters_thread(self)
def start_backlog_cleanup(self)
⋮----
# Update cleaner settings
⋮----
# Reset state
⋮----
# Update UI state
⋮----
# Clear logs and reset progress
⋮----
# Start processing in thread
⋮----
def pause_backlog_cleanup(self)
def resume_backlog_cleanup(self)
def cancel_backlog_cleanup(self)
⋮----
# Reset UI state
⋮----
def _backlog_cleanup_thread(self)
⋮----
# Get parameters
batch_size = int(self.batch_size_var.get())
older_than_days = int(self.older_than_var.get())
⋮----
# Define callbacks
def log_callback(message)
def progress_callback(current, total)
def pause_callback()
# Get processing mode
processing_mode = self.processing_mode_var.get()
⋮----
total_stats = {
# Apply existing filters first (if not ai_only mode)
⋮----
filter_processed = self.cleaner.apply_existing_filters_to_backlog(
⋮----
# AI processing for remaining emails (if not filters_only mode)
⋮----
phase_name = "Phase 2: AI processing remaining emails" if processing_mode == "hybrid" else "AI processing all emails"
⋮----
stats = self.cleaner.process_email_backlog(
⋮----
total_stats.update(stats)  # Include category breakdown
⋮----
# Update final stats
⋮----
error_msg = f"Backlog cleanup error: {e}"
⋮----
# Always reset UI state regardless of success or failure
⋮----
# Show learning suggestions after processing
⋮----
def _update_backlog_log(self, message)
def _update_backlog_progress(self, current, total)
⋮----
percentage = (current / total) * 100
⋮----
# Calculate rate if we have stats
⋮----
elapsed = (datetime.now() - self.current_stats['start_time']).total_seconds()
⋮----
rate = current / elapsed
⋮----
def _update_final_stats(self, stats)
⋮----
# Clear and update stats text
⋮----
stats_text = f"📊 Processing Summary:\n"
⋮----
rate = stats['total_processed'] / stats['duration']
⋮----
def _cleanup_finished(self)
def show_confirmation_dialog(self, proposed_rules)
⋮----
# Create confirmation window
confirm_window = tk.Toplevel(self.root)
⋮----
# Main frame
main_frame = ttk.Frame(confirm_window)
⋮----
# Title
⋮----
# Check if we have valid proposed rules
⋮----
# Show error message
error_frame = ttk.Frame(main_frame)
⋮----
error_text = scrolledtext.ScrolledText(error_frame, height=10, wrap=tk.WORD)
⋮----
error_message = """LM Studio analysis failed or returned no results.
⋮----
# Just a close button
⋮----
# Create notebook for organized display
notebook = ttk.Notebook(main_frame)
⋮----
# Important Keywords tab
⋮----
keywords_frame = ttk.Frame(notebook)
⋮----
keywords_text = scrolledtext.ScrolledText(keywords_frame, height=8)
⋮----
# Important Senders tab
⋮----
senders_frame = ttk.Frame(notebook)
⋮----
senders_text = scrolledtext.ScrolledText(senders_frame, height=8)
⋮----
# Category Rules tab
⋮----
categories_frame = ttk.Frame(notebook)
⋮----
categories_text = scrolledtext.ScrolledText(categories_frame, height=15)
⋮----
# Auto-delete Senders tab
⋮----
delete_frame = ttk.Frame(notebook)
⋮----
delete_text = scrolledtext.ScrolledText(delete_frame, height=8)
⋮----
# Handle any other keys in the response
handled_keys = {'important_keywords', 'important_senders', 'category_rules', 'auto_delete_senders'}
other_keys = set(proposed_rules.keys()) - handled_keys
⋮----
other_frame = ttk.Frame(notebook)
⋮----
other_text = scrolledtext.ScrolledText(other_frame, height=15, wrap=tk.WORD)
⋮----
other_content = []
⋮----
value = proposed_rules[key]
⋮----
# Raw Data tab - always show this for debugging
raw_frame = ttk.Frame(notebook)
⋮----
raw_text = scrolledtext.ScrolledText(raw_frame, height=15, wrap=tk.WORD)
⋮----
# Buttons frame
buttons_frame = ttk.Frame(main_frame)
⋮----
def apply_changes()
⋮----
# Refresh UI components
⋮----
def cancel_changes()
⋮----
# Warning label
warning_label = ttk.Label(main_frame,
⋮----
def refresh_models(self)
⋮----
models = self.cleaner.get_available_models()
model_options = ["auto"] + models
⋮----
def relogin_gmail(self)
⋮----
# Delete existing token
token_path = "config/token.json"
⋮----
# Reset cleaner connection
⋮----
# Reconnect
⋮----
def reset_oauth_token(self)
⋮----
# Backup the token first
backup_path = f"config/token_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
⋮----
# Delete current token
⋮----
# Clear cleaner connection
⋮----
settings = self.cleaner.settings
⋮----
# Load model selection
model_setting = settings.get('lm_studio_model', 'auto')
⋮----
# Auto-refresh management tab components if they exist
⋮----
pass  # Silently fail if management tab not initialized yet
⋮----
# Update settings from UI
⋮----
# Save model selection
⋮----
def reset_settings(self)
def setup_label_mappings_table(self)
⋮----
# Clear existing widgets
⋮----
# Load settings to get label_action_mappings
⋮----
mappings = self.cleaner.settings.get('label_action_mappings', {})
# Header
header_frame = ttk.Frame(self.mappings_table_frame)
⋮----
# Action options
action_options = ["KEEP", "LABEL_AND_ARCHIVE", "TRASH", "IMPORTANT"]
⋮----
row_frame = ttk.Frame(self.mappings_table_frame)
⋮----
action_var = tk.StringVar(value=action)
⋮----
action_combo = ttk.Combobox(row_frame, textvariable=action_var,
⋮----
# Save button
⋮----
def update_label_mapping(self, label)
⋮----
new_action = self.mapping_vars[label].get()
⋮----
def save_all_mappings(self)
def refresh_labels(self)
⋮----
# Initialize Gmail label manager if not already done
⋮----
gmail_service = get_gmail_service()
⋮----
# Refresh label cache
⋮----
labels = self.gmail_label_manager.list_labels()
# Clear existing widgets
⋮----
# Create header
header_frame = ttk.Frame(self.labels_list_frame)
⋮----
# List labels with action buttons
⋮----
# Skip system labels
⋮----
row_frame = ttk.Frame(self.labels_list_frame)
⋮----
actions_frame = ttk.Frame(row_frame)
⋮----
# Update rule combo box
label_names = [name for name in labels.keys()
⋮----
def create_new_label(self)
⋮----
label_name = simpledialog.askstring("Create Label", "Enter label name:")
⋮----
label_id = self.gmail_label_manager.create_label(label_name)
⋮----
self.setup_label_mappings_table()  # Refresh mappings table
⋮----
def rename_label(self, old_name)
⋮----
new_name = simpledialog.askstring("Rename Label", f"Enter new name for '{old_name}':")
⋮----
self.setup_label_mappings_table()  # Refresh mappings table
⋮----
def delete_label(self, label_name)
⋮----
# Check if a corresponding rule file exists
rule_file_path = os.path.join("rules", f"{label_name}.json")
has_rule_file = os.path.exists(rule_file_path)
# Prepare confirmation message
confirm_msg = f"Delete label '{label_name}'?\n\nThis will remove the label from all emails."
⋮----
# Delete the Gmail label
⋮----
# If rule file exists, ask to delete it too
⋮----
def load_rule_details(self, event=None)
⋮----
label_name = self.rule_label_var.get()
⋮----
# Update category display
⋮----
rule_file = os.path.join(rules_dir, f"{label_name}.json")
# Clear all fields first
⋮----
# Populate sender rules
⋮----
# Populate keyword rules
keywords = rule_data.get('keywords', {})
subject_keywords = keywords.get('subject', [])
⋮----
body_keywords = keywords.get('body', [])
⋮----
# Populate advanced rules
⋮----
domains = conditions.get('sender_domain', [])
⋮----
# Store original content for change detection
⋮----
# Clear fields on error
⋮----
def _serialize_current_rule_state(self)
def on_rule_text_modified(self, event=None)
⋮----
current_content = self._serialize_current_rule_state()
⋮----
# If there's an error, enable save button to be safe
⋮----
def save_rule_details(self)
⋮----
content = self.rule_details_text.get(1.0, tk.END).strip()
⋮----
rule_data = json.loads(content)
⋮----
def validate_rule_structure(self, rule_data)
⋮----
required_fields = ['description', 'senders', 'keywords', 'conditions', 'actions']
⋮----
list_fields = ['senders']
⋮----
keywords = rule_data['keywords']
⋮----
conditions = rule_data['conditions']
⋮----
actions = rule_data['actions']
⋮----
def validate_rule_format(self)
def create_new_rule(self)
⋮----
new_rule_dialog = tk.Toplevel(self.root)
⋮----
rule_name_var = tk.StringVar()
rule_name_entry = ttk.Entry(new_rule_dialog, textvariable=rule_name_var, width=30)
⋮----
description_var = tk.StringVar()
description_entry = ttk.Entry(new_rule_dialog, textvariable=description_var, width=50)
⋮----
button_frame = ttk.Frame(new_rule_dialog)
⋮----
def create_rule()
⋮----
rule_name = rule_name_var.get().strip()
description = description_var.get().strip()
⋮----
new_rule = {
⋮----
rule_file = os.path.join(rules_dir, f"{rule_name}.json")
⋮----
def refresh_rule_labels(self)
⋮----
rule_files = [f[:-5] for f in os.listdir(rules_dir) if f.endswith('.json')]
⋮----
def cleanup_threads(self)
def on_closing(self)
def run(self)
def setup_analytics_tab(self, parent)
⋮----
control_frame = ttk.LabelFrame(scrollable_frame, text="Analytics Controls", padding=10)
⋮----
dist_frame = ttk.LabelFrame(scrollable_frame, text="Category Distribution", padding=10)
⋮----
effectiveness_frame = ttk.LabelFrame(scrollable_frame, text="Filter Effectiveness", padding=10)
⋮----
insights_frame = ttk.LabelFrame(scrollable_frame, text="Learning Insights", padding=10)
⋮----
optimizations_frame = ttk.LabelFrame(scrollable_frame, text="Suggested Optimizations", padding=10)
⋮----
evolve_frame = ttk.LabelFrame(scrollable_frame, text="Auto-Evolution", padding=10)
⋮----
evolution_buttons = ttk.Frame(evolve_frame)
⋮----
def setup_learning_tab(self, parent)
⋮----
stats_frame = ttk.LabelFrame(scrollable_frame, text="Learning Statistics", padding=10)
⋮----
refresh_stats_btn = ttk.Button(stats_frame, text="Refresh Stats", command=self.refresh_learning_stats)
⋮----
suggestions_frame = ttk.LabelFrame(scrollable_frame, text="AI-Generated Rule Suggestions", padding=10)
⋮----
suggestions_btn_frame = ttk.Frame(suggestions_frame)
⋮----
manual_frame = ttk.LabelFrame(scrollable_frame, text="Manual Learning", padding=10)
⋮----
manual_btn_frame = ttk.Frame(manual_frame)
⋮----
history_frame = ttk.LabelFrame(scrollable_frame, text="Learning History", padding=10)
⋮----
history_btn_frame = ttk.Frame(history_frame)
⋮----
def refresh_learning_stats(self)
⋮----
stats_content = f"Learning Engine Statistics\n"
⋮----
percentage = (count / stats['total_records']) * 100 if stats['total_records'] > 0 else 0
⋮----
def refresh_learning_history(self)
⋮----
history_content = f"Recent Learning History (Last {min(20, len(history))} decisions)\n"
⋮----
recent_history = history[-20:] if len(history) > 20 else history
⋮----
timestamp = record.get('timestamp', 'Unknown')
llm_action = record.get('llm_action', 'UNKNOWN')
confidence = record.get('llm_confidence', 0.0)
⋮----
sender = record.get('sender', 'Unknown')[:25]
subject = record.get('subject', 'No subject')[:35]
⋮----
time_str = dt.strftime('%m/%d %H:%M')
⋮----
time_str = timestamp[:10] if len(timestamp) > 10 else timestamp
status = "✅ Correct" if not user_override else f"⚠️ Corrected to {user_override}"
⋮----
history_content = "No learning history available yet.\n\n"
⋮----
def review_recent_decisions(self)
def train_on_emails(self)
def export_learning_data(self)
⋮----
filename = filedialog.asksaveasfilename(
⋮----
export_data = {
⋮----
def clear_learning_history(self)
⋮----
result = messagebox.askyesno(
⋮----
def setup_unsubscribe_tab(self, parent)
⋮----
control_frame = ttk.LabelFrame(parent, text="Actions", padding=10)
⋮----
candidates_frame = ttk.LabelFrame(parent, text="Unsubscribe Candidates", padding=10)
⋮----
canvas = tk.Canvas(candidates_frame)
scrollbar = ttk.Scrollbar(candidates_frame, orient="vertical", command=canvas.yview)
⋮----
def find_unsubscribe_candidates(self)
⋮----
def log_callback(message)
def find_candidates_thread()
⋮----
candidates_data = self.cleaner.get_detailed_unsubscribe_candidates(log_callback=log_callback)
⋮----
def display_unsubscribe_candidates(self, candidates_data)
⋮----
var = tk.BooleanVar()
⋮----
frame = ttk.Frame(self.unsubscribe_candidates_frame)
⋮----
checkbox = ttk.Checkbutton(
⋮----
sender = candidate.get('sender', 'Unknown')
count = candidate.get('count', 0)
latest_subject = candidate.get('latest_subject', 'No subject')
label_text = f"{sender} ({count} emails) - Latest: {latest_subject[:50]}..."
label = ttk.Label(frame, text=label_text, wraplength=600)
⋮----
def update_unsubscribe_button_state(self)
⋮----
selected_count = sum(1 for var in self.candidate_vars if var.get())
⋮----
def unsubscribe_selected(self)
⋮----
selected_candidates = []
⋮----
def unsubscribe_thread()
⋮----
def update_ui()
⋮----
def refresh_analytics(self)
⋮----
def refresh_thread()
⋮----
analytics_data = self.generate_analytics_data()
⋮----
def generate_analytics_data(self)
⋮----
analytics = {
⋮----
confidence_by_category = {}
⋮----
action = record.get('llm_action', 'UNKNOWN')
⋮----
overrides = [r for r in history if r.get('user_override')]
total_decisions = len(history)
override_rate = (len(overrides) / total_decisions * 100) if total_decisions > 0 else 0
⋮----
rule_suggestions = self.cleaner.learning_engine.suggest_rule_updates()
pattern_suggestions = self.cleaner.learning_engine.detect_new_patterns()
⋮----
filter_stats = self.get_filter_effectiveness_stats()
⋮----
def get_filter_effectiveness_stats(self)
⋮----
filter_count = 0
llm_count = 0
⋮----
processing_method = record.get('processing_method', 'llm')
⋮----
total = filter_count + llm_count
⋮----
stats_file = 'data/processing_stats.json'
⋮----
stored_stats = json.load(f)
⋮----
def update_analytics_ui(self, analytics_data)
def draw_category_pie_chart(self, category_data)
⋮----
total = sum(category_data.values())
⋮----
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
⋮----
start_angle = 0
legend_y = 50
⋮----
extent = 360 * count / total
color = colors[i % len(colors)]
⋮----
percentage = (count / total) * 100
⋮----
def update_category_stats(self, analytics_data)
⋮----
stats = analytics_data.get('processing_stats', {})
confidence_by_cat = analytics_data.get('confidence_by_category', {})
text = f"📊 Processing Statistics:\n"
⋮----
def update_filter_effectiveness(self, effectiveness_data)
⋮----
text = "📈 Filter Effectiveness Analysis:\n\n"
filter_count = effectiveness_data.get('filter_processed_count', 0)
llm_count = effectiveness_data.get('llm_processed_count', 0)
total_count = effectiveness_data.get('total_processed', 0)
⋮----
percentage = score * 100 if isinstance(score, (int, float)) else 0
bar_length = int(score * 20) if isinstance(score, (int, float)) else 0
bar = "█" * bar_length + "░" * (20 - bar_length)
⋮----
def update_learning_insights(self, analytics_data)
⋮----
suggestions = analytics_data.get('suggestions', {})
rule_updates = suggestions.get('rule_updates', {})
text = "🧠 Learning Insights:\n\n"
⋮----
summary = rule_updates['summary']
⋮----
sender_corrections = rule_updates.get('sender_corrections', {})
⋮----
keyword_patterns = rule_updates.get('keyword_patterns', {})
⋮----
keywords = ', '.join(pattern['suggested_keywords'][:3])
⋮----
def update_suggestions_display(self, suggestions_data)
⋮----
text = "💡 Optimization Suggestions:\n\n"
rule_updates = suggestions_data.get('rule_updates', {})
new_patterns = suggestions_data.get('new_patterns', [])
suggestion_count = 0
⋮----
def export_analytics_report(self)
⋮----
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"exports/analytics_report_{timestamp}.json"
⋮----
def show_learning_engine_suggestions(self)
⋮----
suggestions = self.cleaner.learning_engine.suggest_rule_updates()
new_patterns = self.cleaner.learning_engine.detect_new_patterns()
⋮----
dialog = tk.Toplevel(self.root)
⋮----
main_frame = ttk.Frame(dialog)
⋮----
rule_frame = ttk.Frame(notebook)
⋮----
rule_list = tk.Listbox(rule_frame, height=8)
⋮----
rule_btn_frame = ttk.Frame(rule_frame)
⋮----
def apply_selected_rules()
⋮----
selected_indices = rule_list.curselection()
⋮----
applied_count = 0
⋮----
suggestion = suggestions[idx]
⋮----
pattern_frame = ttk.Frame(notebook)
⋮----
pattern_list = tk.Listbox(pattern_frame, height=6)
⋮----
def apply_sender_rule_suggestion(self, suggestion)
⋮----
category = suggestion['category']
sender = suggestion['sender']
⋮----
rule_file = os.path.join(rules_dir, f"{category}.json")
⋮----
rule_data = {
⋮----
def apply_keyword_rule_suggestion(self, suggestion)
⋮----
keyword = suggestion['keyword']
⋮----
def show_rule_suggestions(self)
⋮----
progress_window = tk.Toplevel(self.root)
⋮----
progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
⋮----
status_label = ttk.Label(progress_window, text="Starting analysis...")
⋮----
def update_status(message)
def analyze_thread()
⋮----
suggestions = self.cleaner.analyze_and_suggest_rules(log_callback=update_status)
⋮----
def show_rule_suggestion_dialog(self, suggestions)
⋮----
canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
⋮----
selected_suggestions = []
⋮----
suggestion_frame = ttk.LabelFrame(scrollable_frame, text=f"Suggestion {i+1}", padding=10)
⋮----
var = tk.BooleanVar(value=True)
⋮----
cb_frame = ttk.Frame(suggestion_frame)
⋮----
details_text = f"Sender: {suggestion['sender']}\nCategory: {suggestion['suggested_category']}\nConfidence: {suggestion['confidence']:.1%}"
⋮----
def apply_selected()
def cancel()
⋮----
def _apply_rule_suggestion(self, suggestion)
⋮----
category = suggestion['suggested_category']
⋮----
def apply_learning_suggestions(self)
⋮----
summary = suggestions.get('summary', {})
message = f"Apply learning suggestions?\n\n"
⋮----
applied_count = self.apply_rule_suggestions(suggestions)
⋮----
def apply_rule_suggestions(self, suggestions)
⋮----
sender_corrections = suggestions.get('sender_corrections', {})
⋮----
keyword_patterns = suggestions.get('keyword_patterns', {})
⋮----
keywords = data.get('keywords', [])
⋮----
confidence_improvements = suggestions.get('confidence_improvements', [])
⋮----
def _update_rule_file_with_sender(self, category, sender)
def _update_rule_file_with_keywords(self, category, keywords)
⋮----
subject_keywords = rule_data.setdefault('keywords', {}).setdefault('subject', [])
added_any = False
⋮----
added_any = True
⋮----
def _apply_confidence_improvement(self, improvement)
⋮----
improvement_type = improvement.get('type')
⋮----
category = improvement.get('category')
keyword = improvement.get('keyword')
⋮----
domain = improvement.get('domain')
⋮----
def _add_exclude_keyword(self, category, keyword)
⋮----
exclude_keywords = rule_data.setdefault('conditions', {}).setdefault('exclude_keywords', [])
⋮----
def _add_domain_rule(self, category, domain)
⋮----
domain_rules = rule_data.setdefault('conditions', {}).setdefault('sender_domain', [])
⋮----
def run_auto_evolution(self)
⋮----
def auto_evolve_thread()
⋮----
def main()
⋮----
app = GmailCleanerGUI()
```

## File: gmail-cleaner.sh
```bash
export QML_IMPORT_PATH="/app/qml"
export PYTHONPATH="/app:$PYTHONPATH"
mkdir -p "$HOME/.config/gmail-cleaner"
mkdir -p "$HOME/.local/share/gmail-cleaner"
if [ ! -f "$HOME/.config/gmail-cleaner/settings.json" ] && [ -f "/app/config/settings.json" ]; then
    cp "/app/config/settings.json" "$HOME/.config/gmail-cleaner/"
fi
cd /app
exec python3 qml_main.py "$@"
```

## File: health_check.py
```python
def load_settings(settings_path="config/settings.json")
⋮----
content = f.read()
content = "\n".join(line for line in content.splitlines() if not line.strip().startswith("//"))
⋮----
settings = load_settings()
log_dir = settings.get("paths", {}).get("logs", "logs")
log_file_name = "health_check.log"
⋮----
logger = get_logger(__name__)
def build_jobs_config(settings)
⋮----
jobs = {}
automation = settings.get("automation", {})
⋮----
interval = automation["realtime_processing_interval_minutes"]
⋮----
jobs_config = build_jobs_config(settings)
state_file = DEFAULT_STATE_FILE
app = Flask(__name__)
⋮----
@app.route("/health", methods=["GET"])
def health()
⋮----
@app.route("/status", methods=["GET"])
def status()
⋮----
scheduler = CronScheduler(jobs_config, state_file=state_file)
jobs_status = []
now = datetime.utcnow()
⋮----
last_run = scheduler.get_last_run(job_name)
status = scheduler.get_job_status(job_name)
missed = scheduler.get_missed_runs(job_name, now)
next_run = scheduler.get_next_run(job_name, now)
⋮----
error_count = sum(1 for job in jobs_status if job["status"] == "error")
log_info = {}
log_path = os.path.join(log_dir, log_file_name)
⋮----
lines = f.readlines()
⋮----
resp = {
⋮----
@app.errorhandler(Exception)
def handle_exception(e)
⋮----
@app.route("/api/lmstudio/status", methods=["GET"])
def lm_studio_status()
⋮----
loaded_model = lm_studio.get_loaded_model()
⋮----
@app.route("/api/lmstudio/models", methods=["GET"])
def lm_studio_models()
⋮----
@app.route("/api/lmstudio/analyze", methods=["POST"])
def lm_studio_analyze()
⋮----
data = request.get_json()
use_existing_export = data.get("use_existing_export", False) if data else False
⋮----
result = analyze_email_subjects_with_lm_studio(use_existing_export)
⋮----
@app.route("/api/lmstudio/apply-suggestions", methods=["POST"])
def lm_studio_apply_suggestions()
⋮----
suggestions = data.get("suggestions") if data else None
⋮----
success = apply_lm_studio_suggestions(suggestions)
⋮----
@app.route("/api/lmstudio/switch-model", methods=["POST"])
def lm_studio_switch_model()
⋮----
model_key = data.get("model_key") if data else None
⋮----
success = lm_studio.load_model(model_key)
⋮----
# --- Web Dashboard ---
⋮----
@app.route("/", methods=["GET"])
def dashboard()
⋮----
dashboard_html = """
⋮----
# --- API Documentation endpoint ---
⋮----
@app.route("/api", methods=["GET"])
def api_docs()
⋮----
doc = {
```

## File: llmdiver_daemon.py
```python
class LLMdiverConfig
⋮----
def __init__(self, config_path: str = "config/llmdiver.json")
def load_config(self) -> Dict
⋮----
default_config = {
⋮----
config = json.load(f)
⋮----
class RepoWatcher(FileSystemEventHandler)
⋮----
def __init__(self, daemon, repo_config)
def on_modified(self, event)
⋮----
file_path = Path(event.src_path)
triggers = self.repo_config["analysis_triggers"]
⋮----
current_time = time.time()
⋮----
class LLMStudioClient
⋮----
def __init__(self, config)
def chunk_text(self, text: str, chunk_size: int = 16000) -> List[str]
⋮----
words = text.split()
chunks = []
current_chunk = []
current_length = 0
⋮----
word_length = len(word) + 1
⋮----
current_chunk = [word]
current_length = word_length
⋮----
def analyze_repo_summary(self, summary_text: str) -> str
⋮----
system_prompt = """You are an expert code auditor. Analyze the repository summary and identify:
enable_chunking = self.config["llm_integration"].get("enable_chunking", False)
chunk_size = self.config["llm_integration"].get("chunk_size", 16000)
⋮----
chunks = self.chunk_text(summary_text, chunk_size)
all_analyses = []
⋮----
chunk_prompt = f"Analyze this repository section ({i+1}/{len(chunks)}):\n\n{chunk}"
analysis = self._send_single_request(system_prompt, chunk_prompt)
⋮----
combined = "\n\n".join(all_analyses)
final_prompt = f"Summarize and consolidate these code audit findings:\n\n{combined}"
⋮----
def _send_single_request(self, system_prompt: str, user_prompt: str) -> str
⋮----
payload = {
⋮----
response = requests.post(self.url, json=payload, timeout=300)
⋮----
result = response.json()
⋮----
error_text = ""
⋮----
error_data = e.response.json()
error_text = error_data.get("error", e.response.text)
⋮----
error_text = e.response.text
⋮----
class GitAutomation
⋮----
def analyze_changes(self, repo_path: str) -> Dict
⋮----
repo = git.Repo(repo_path)
modified_files = [item.a_path for item in repo.index.diff(None)]
untracked_files = repo.untracked_files
total_changes = len(modified_files) + len(untracked_files)
⋮----
def generate_commit_message(self, analysis: str, changes: Dict) -> str
⋮----
lines = analysis.split('\n')
critical_issues = []
todos = []
improvements = []
current_section = ""
⋮----
line = line.strip()
⋮----
current_section = "critical"
⋮----
current_section = "todos"
⋮----
current_section = "improvements"
⋮----
summary_parts = []
⋮----
summary = ", ".join(summary_parts) if summary_parts else "Update codebase"
details = []
⋮----
details_text = "\n".join(details)
⋮----
def auto_commit(self, repo_path: str, analysis: str) -> bool
⋮----
changes = self.analyze_changes(repo_path)
⋮----
repo = changes["repo"]
⋮----
message = self.generate_commit_message(analysis, changes)
⋮----
origin = repo.remote('origin')
⋮----
class LLMdiverDaemon
⋮----
def setup_logging(self)
⋮----
log_level = getattr(logging, self.config.config["daemon"]["log_level"])
⋮----
def run_repomix_analysis(self, repo_path: str) -> str
⋮----
output_file = f"{repo_path}/.llmdiver_analysis.md"
cmd = [
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
⋮----
def schedule_analysis(self, repo_config: Dict)
def process_analysis_queue(self)
⋮----
repo_config = self.analysis_queue.pop(0)
⋮----
def analyze_repository(self, repo_config: Dict)
⋮----
summary = self.run_repomix_analysis(repo_config["path"])
⋮----
analysis = self.llm_client.analyze_repo_summary(summary)
analysis_dir = Path(repo_config["path"]) / ".llmdiver"
⋮----
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_file = analysis_dir / f"analysis_{timestamp}.md"
⋮----
latest_link = analysis_dir / "latest_analysis.md"
⋮----
def start_watching(self)
⋮----
repo_path = repo_config["path"]
⋮----
observer = Observer()
handler = RepoWatcher(self, repo_config)
⋮----
def start(self)
⋮----
analysis_thread = threading.Thread(target=self.process_analysis_queue)
⋮----
def stop(self)
def signal_handler(signum, frame)
⋮----
daemon = LLMdiverDaemon()
```

## File: lm_studio_integration.py
```python
logger = get_logger(__name__)
class LMStudioManager
⋮----
def __init__(self, base_url: str = "http://127.0.0.1:1234", timeout: int = 60)
def is_server_running(self) -> bool
⋮----
response = requests.get(f"{self.base_url}/v1/models", timeout=self.timeout)
⋮----
def get_loaded_model(self) -> Optional[str]
⋮----
models = response.json()
⋮----
def load_model(self, model_key: str) -> bool
def detect_current_model_capability(self) -> str
⋮----
current_model_id = self.get_loaded_model()
⋮----
model_id_lower = current_model_id.lower()
⋮----
detected_capability = self.detect_current_model_capability()
⋮----
adjusted_max_tokens = max_tokens
adjusted_temperature = temperature
⋮----
adjusted_max_tokens = min(max_tokens, 500)
⋮----
adjusted_max_tokens = min(max_tokens, 2000)
adjusted_temperature = max(temperature, 0.1)
⋮----
payload = {
response = requests.post(
⋮----
result = response.json()
⋮----
content = result["choices"][0]["message"]["content"].strip()
⋮----
categories = ["INBOX", "BILLS", "SHOPPING", "NEWSLETTERS", "SOCIAL", "PERSONAL", "JUNK", "REVIEW"]
emails_text = ""
⋮----
sender = email_senders[i] if email_senders and i < len(email_senders) else "unknown"
⋮----
prompt = f"""You are an expert email categorization system. Analyze each email and assign the most appropriate category.
result = self.generate_completion(
⋮----
categories_data = json.loads(result)
⋮----
emails_sample = email_data[:max_emails]
analysis_data = {
prompt = f"""You are an advanced email pattern analysis expert. Analyze this dataset of {len(emails_sample)} emails and provide comprehensive insights.
⋮----
def generate_filter_rules(self, pattern_analysis: Dict) -> List[Dict]
⋮----
prompt = f"""Based on this email pattern analysis, generate practical Gmail filter rules.
⋮----
prompt = f"""You are a system optimization expert. Based on current settings and processing statistics, suggest improvements.
⋮----
lm_studio = LMStudioManager()
def analyze_email_subjects_with_lm_studio(use_existing_export: bool = False) -> Optional[Dict]
⋮----
email_data = []
⋮----
export_files = list(Path("exports").glob("*.json")) if Path("exports").exists() else []
⋮----
latest_export = max(export_files, key=lambda f: f.stat().st_mtime)
⋮----
email_data = json.load(f)
⋮----
subjects_file = Path("email_subjects.txt")
⋮----
subjects = [line.strip() for line in f if line.strip()]
email_data = [{"subject": subj, "sender": "unknown"} for subj in subjects]
⋮----
pattern_analysis = lm_studio.analyze_email_patterns(email_data)
⋮----
filter_rules = lm_studio.generate_filter_rules(pattern_analysis)
result = {
⋮----
def update_config_from_lm_analysis(analysis_result: Dict, settings_path: str = "config/settings.json") -> bool
⋮----
settings = {}
⋮----
settings = json.load(f)
categorizations = analysis_result.get("categorizations", [])
metadata = analysis_result.get("metadata", {})
⋮----
updates_made = False
sender_patterns = {}
category_counts = {}
⋮----
category = item.get("category", "UNKNOWN")
sender = item.get("sender", "")
⋮----
domain = sender.split("@")[-1].lower()
⋮----
strong_patterns = {}
⋮----
category = list(categories.keys())[0]
count = categories[category]
⋮----
updates_made = True
⋮----
def apply_lm_studio_suggestions(suggestions: Dict) -> bool
```

## File: log_config.py
```python
log_format = (
date_format = "%Y-%m-%d %H:%M:%S"
logger = logging.getLogger()
⋮----
file_handler = TimedRotatingFileHandler(
⋮----
ch_level = console_log_level if console_log_level is not None else log_level
console_handler = logging.StreamHandler()
⋮----
def get_logger(name=None)
```

## File: pid_utils.py
```python
logger = get_logger(__name__)
class PIDFileManager
⋮----
def __init__(self, pid_dir: str = "pids", process_name: str = "process")
def create_pid_file(self) -> bool
⋮----
# Check if PID file already exists and process is running
⋮----
# Write current PID to file
⋮----
# Register cleanup handlers
⋮----
def remove_pid_file(self) -> bool
⋮----
# Verify this is our PID file
stored_pid = self.get_stored_pid()
⋮----
def get_stored_pid(self) -> Optional[int]
def is_process_running(self) -> bool
⋮----
# Send signal 0 to check if process exists
⋮----
# Process doesn't exist, clean up stale PID file
⋮----
def _register_cleanup_handlers(self)
⋮----
def signal_handler(signum, frame)
⋮----
def __enter__(self)
def __exit__(self, exc_type, exc_val, exc_tb)
def get_running_processes(pid_dir: str = "pids") -> dict
⋮----
running = {}
pid_path = Path(pid_dir)
⋮----
process_name = pid_file.stem
manager = PIDFileManager(pid_dir, process_name)
⋮----
stored_pid = manager.get_stored_pid()
⋮----
def stop_process_by_name(process_name: str, pid_dir: str = "pids", timeout: int = 10) -> bool
def cleanup_stale_pid_files(pid_dir: str = "pids")
⋮----
cleaned_count = 0
```

## File: progress_monitor.py
```python
def monitor_progress()
⋮----
log_file = "logs/bulk_processing.log"
⋮----
stats = defaultdict(int)
last_size = 0
start_time = datetime.now()
⋮----
content = f.read()
⋮----
total_processed = sum(stats.values())
current_time = datetime.now()
elapsed = current_time - start_time
⋮----
rate = total_processed / elapsed.total_seconds()
⋮----
percentage = (count / total_processed) * 100
```

## File: qml_main.py
```python
project_root = Path(__file__).parent
⋮----
logger = get_logger(__name__)
class GmailCleanerService(QObject)
⋮----
isConnectedChanged = Signal(bool)
unreadCountChanged = Signal(int)
accuracyRateChanged = Signal(float)
def __init__(self)
def initialize_cleaner(self)
⋮----
@Slot()
    def refresh_stats(self)
⋮----
unread_query = "is:unread"
messages = self._cleaner.gmail_service.users().messages().list(
⋮----
history_file = Path("logs/categorization_history.json")
⋮----
history = json.load(f)
⋮----
recent = history[-100:]
⋮----
@Property(bool, notify=isConnectedChanged)
    def isConnected(self)
⋮----
@Property(int, notify=unreadCountChanged)
    def unreadCount(self)
⋮----
@Property(float, notify=accuracyRateChanged)
    def accuracyRate(self)
class LMStudioService(QObject)
⋮----
currentModelChanged = Signal(str)
availableModelsChanged = Signal(list)
⋮----
def initialize_lm_studio(self)
⋮----
current = self._lm_studio.get_loaded_model()
⋮----
@Slot()
    def refresh_status(self)
⋮----
@Slot(str)
    def switchModel(self, model_key)
⋮----
success = self._lm_studio.load_model(model_key)
⋮----
@Slot()
    def runAnalysis(self)
⋮----
result = analyze_email_subjects_with_lm_studio(use_existing_export=True)
⋮----
@Property(str, notify=currentModelChanged)
    def currentModel(self)
⋮----
@Property(list, notify=availableModelsChanged)
    def availableModels(self)
⋮----
@Property(int)
    def currentModelIndex(self)
⋮----
@Slot(str)
    def setStrategy(self, strategy)
class EmailRunnerService(QObject)
⋮----
isProcessingChanged = Signal(bool)
progressChanged = Signal(int, int)
liveLogChanged = Signal(str)
⋮----
@Slot()
    def start(self)
⋮----
cleaner = GmailLMCleaner()
⋮----
messages = cleaner.gmail_service.users().messages().list(
⋮----
@Slot()
    def pause(self)
⋮----
@Slot()
    def stop(self)
def add_log(self, message)
⋮----
timestamp = datetime.datetime.now().strftime("%H:%M:%S")
⋮----
@Property(bool, notify=isProcessingChanged)
    def isProcessing(self)
⋮----
@Property(int, notify=progressChanged)
    def processedCount(self)
⋮----
@Property(int, notify=progressChanged)
    def totalCount(self)
⋮----
@Property(str, notify=liveLogChanged)
    def liveLog(self)
⋮----
@Property(int)
    def batchSize(self)
⋮----
@batchSize.setter
    def setBatchSize(self, size)
⋮----
@Property(str)
    def query(self)
⋮----
@query.setter
    def setQuery(self, query)
⋮----
@Property(str)
    def estimatedTimeRemaining(self)
⋮----
remaining = self._total_count - self._processed_count
seconds = remaining * 2
⋮----
hours = seconds // 3600
minutes = (seconds % 3600) // 60
⋮----
@Slot()
    def startBulkProcessing(self)
⋮----
@Slot()
    def exportEmailList(self)
⋮----
export_result = cleaner.export_email_subjects_to_file(
⋮----
@Slot()
    def startCleanup(self)
⋮----
cleanup = EmailCleanup()
⋮----
class SettingsManagerService(QObject)
⋮----
lmStudioEndpointChanged = Signal(str)
temperatureChanged = Signal(float)
batchSizeChanged = Signal(int)
requestDelayChanged = Signal(int)
useServerSideFilteringChanged = Signal(bool)
junkRetentionDaysChanged = Signal(int)
newsletterRetentionDaysChanged = Signal(int)
⋮----
def load_settings(self)
⋮----
settings_file = Path("config/settings.json")
⋮----
@Slot()
    def saveSettings(self)
⋮----
@Property(str, notify=lmStudioEndpointChanged)
    def lmStudioEndpoint(self)
⋮----
@lmStudioEndpoint.setter
    def setLmStudioEndpoint(self, endpoint)
⋮----
old_value = self._settings["lm_studio"].get("endpoint", "")
⋮----
@Property(float, notify=temperatureChanged)
    def temperature(self)
⋮----
@temperature.setter
    def setTemperature(self, temp)
⋮----
old_value = self._settings["lm_studio"].get("temperature", 0.3)
⋮----
@Property(int, notify=batchSizeChanged)
    def batchSize(self)
⋮----
old_value = self._settings["processing"].get("batch_size", 100)
⋮----
@Property(int, notify=requestDelayChanged)
    def requestDelay(self)
⋮----
@requestDelay.setter
    def setRequestDelay(self, delay)
⋮----
old_value = self._settings["gmail"].get("request_delay", 100)
⋮----
@Property(bool, notify=useServerSideFilteringChanged)
    def useServerSideFiltering(self)
⋮----
@useServerSideFiltering.setter
    def setUseServerSideFiltering(self, enabled)
⋮----
old_value = self._settings["gmail"].get("use_server_side_filtering", False)
⋮----
@Property(int, notify=junkRetentionDaysChanged)
    def junkRetentionDays(self)
⋮----
@junkRetentionDays.setter
    def setJunkRetentionDays(self, days)
⋮----
old_value = self._settings["cleanup"].get("junk_retention_days", 30)
⋮----
@Property(int, notify=newsletterRetentionDaysChanged)
    def newsletterRetentionDays(self)
⋮----
@newsletterRetentionDays.setter
    def setNewsletterRetentionDays(self, days)
⋮----
old_value = self._settings["cleanup"].get("newsletter_retention_days", 90)
⋮----
class AuditManagerService(QObject)
⋮----
filteredEntriesChanged = Signal(list)
totalEntriesChanged = Signal(int)
recentActivityChanged = Signal(list)
⋮----
def load_audit_data(self)
⋮----
audit_entry = {
⋮----
log_file = Path("logs/email_processing.log")
⋮----
lines = f.readlines()
⋮----
parts = line.strip().split(' - ')
⋮----
timestamp = parts[0]
message = parts[-1]
⋮----
def _get_category_icon(self, category)
⋮----
icons = {
⋮----
@Property(list, notify=filteredEntriesChanged)
    def filteredEntries(self)
⋮----
@Property(int, notify=totalEntriesChanged)
    def totalEntries(self)
⋮----
@Property(list, notify=recentActivityChanged)
    def recentActivity(self)
⋮----
@Slot(str)
    def setDateFilter(self, date_filter)
⋮----
@Slot(str)
    def setActionFilter(self, action_filter)
⋮----
@Slot(str)
    def setCategoryFilter(self, category_filter)
def _apply_filters(self)
⋮----
filtered = self._entries.copy()
⋮----
filtered = [e for e in filtered if self._date_filter.lower() in e.get('timestamp', '').lower()]
⋮----
filtered = [e for e in filtered if self._action_filter.lower() in e.get('action', '').lower()]
⋮----
filtered = [e for e in filtered if self._category_filter.lower() in e.get('category', '').lower()]
⋮----
def main()
⋮----
app = QGuiApplication(sys.argv)
⋮----
engine = QQmlApplicationEngine()
gmail_cleaner = GmailCleanerService()
lm_studio_manager = LMStudioService()
email_runner = EmailRunnerService()
settings_manager = SettingsManagerService()
audit_manager = AuditManagerService()
⋮----
qml_file = Path(__file__).parent / "qml" / "main.qml"
```

## File: setup.sh
```bash
set -e
function fail() {
  echo "❌ Error: $1"
  exit 1
}
echo "🔧 Gmail Automation System Setup"
echo "--------------------------------"
if [ ! -d "venv" ]; then
  echo "🟢 Creating Python virtual environment..."
  python3 -m venv venv || fail "Failed to create virtual environment"
else
  echo "✅ Virtual environment already exists."
fi
source venv/bin/activate || fail "Failed to activate virtual environment"
echo "🔄 Upgrading pip..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  echo "📦 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt || fail "Failed to install requirements"
else
  echo "📦 Installing core dependencies (no requirements.txt found)..."
  pip install google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client google-generativeai python-dotenv \
    requests croniter flask pandas colorama || fail "Failed to install core dependencies"
fi
for d in logs exports rules data config; do
  if [ ! -d "$d" ]; then
    echo "📁 Creating directory: $d"
    mkdir -p "$d" || fail "Failed to create directory $d"
  else
    echo "✅ Directory exists: $d"
  fi
done
if [ ! -f "rules/.initialized" ]; then
  echo "📋 Initializing rules directory structure..."
  echo "Rules directory initialized on $(date)" > "rules/.initialized"
  echo "✅ Rules directory prepared for first-time use"
fi
chmod +x *.py *.sh
SYSTEMD_DIR="./systemd_units"
mkdir -p "$SYSTEMD_DIR"
RUNNER_SERVICE="$SYSTEMD_DIR/gmail-autonomy-runner.service"
if [ ! -f "$RUNNER_SERVICE" ]; then
  cat > "$RUNNER_SERVICE" <<EOF
[Unit]
Description=Gmail Autonomy Runner
After=network.target
[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/autonomous_runner.py
Restart=on-failure
User=$USER
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
  echo "📝 Created sample systemd unit: $RUNNER_SERVICE"
else
  echo "✅ Systemd unit exists: $RUNNER_SERVICE"
fi
HEALTH_SERVICE="$SYSTEMD_DIR/gmail-autonomy-health.service"
if [ ! -f "$HEALTH_SERVICE" ]; then
  cat > "$HEALTH_SERVICE" <<EOF
[Unit]
Description=Gmail Autonomy Health Check API
After=network.target
[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/health_check.py
Restart=on-failure
User=$USER
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
  echo "📝 Created sample systemd unit: $HEALTH_SERVICE"
else
  echo "✅ Systemd unit exists: $HEALTH_SERVICE"
fi
echo
echo "To enable services, run:"
echo "  sudo cp $RUNNER_SERVICE /etc/systemd/system/gmail-autonomy-runner.service"
echo "  sudo cp $HEALTH_SERVICE /etc/systemd/system/gmail-autonomy-health.service"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable gmail-autonomy-runner"
echo "  sudo systemctl enable gmail-autonomy-health"
echo "  sudo systemctl start gmail-autonomy-runner"
echo "  sudo systemctl start gmail-autonomy-health"
LOGROTATE_CONF="/etc/logrotate.d/gmail-autonomy"
TMP_LOGROTATE="gmail-autonomy.logrotate"
cat > "$TMP_LOGROTATE" <<EOF
$(pwd)/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
EOF
if [ -w "/etc/logrotate.d" ]; then
  sudo cp "$TMP_LOGROTATE" "$LOGROTATE_CONF"
  echo "🌀 Logrotate config installed at $LOGROTATE_CONF"
else
  echo "⚠️  No permission to write to /etc/logrotate.d. Please run:"
  echo "    sudo cp $TMP_LOGROTATE $LOGROTATE_CONF"
fi
rm -f "$TMP_LOGROTATE"
echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Place your Gmail API credentials.json in the config/ directory."
echo "2. Delete config/token.json if it exists (new scopes require re-authentication)."
echo "3. Review and update your .env or settings.json as needed."
echo "4. Copy and enable the systemd services as shown above."
echo "5. To start the main runner: sudo systemctl start gmail-autonomy-runner"
echo "6. To start the health check API: sudo systemctl start gmail-autonomy-health"
echo "7. Logs are in the 'logs/' directory and will be rotated automatically."
echo
echo "To rerun this setup, simply execute ./setup.sh again."
echo
echo "For more details, see README.md or claude.md."
```

## File: start_llmdiver.sh
```bash
DAEMON_SCRIPT="llmdiver_daemon.py"
PID_FILE="llmdiver.pid"
LOG_FILE="llmdiver_daemon.log"
start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "LLMdiver daemon is already running (PID: $PID)"
            return 1
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    echo "Starting LLMdiver daemon..."
    if ! command -v repomix &> /dev/null; then
        echo "❌ Error: repomix not found. Install with: npm install -g repomix"
        exit 1
    fi
    if ! python3 -c "import git, watchdog" 2>/dev/null; then
        echo "❌ Error: Missing Python dependencies. Install with: pip install gitpython watchdog"
        exit 1
    fi
    if ! curl -s http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
        echo "⚠️  Warning: LM Studio not accessible at http://127.0.0.1:1234"
        echo "   Make sure LM Studio is running with API enabled"
    fi
    mkdir -p config
    nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ LLMdiver daemon started successfully (PID: $PID)"
        echo "📋 Log file: $LOG_FILE"
        echo "🔍 Monitor with: tail -f $LOG_FILE"
        return 0
    else
        echo "❌ Failed to start daemon"
        rm -f "$PID_FILE"
        return 1
    fi
}
stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "LLMdiver daemon is not running"
        return 1
    fi
    PID=$(cat "$PID_FILE")
    echo "Stopping LLMdiver daemon (PID: $PID)..."
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        sleep 2
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Force killing daemon..."
            kill -9 "$PID"
        fi
        rm -f "$PID_FILE"
        echo "✅ LLMdiver daemon stopped"
    else
        echo "Daemon was not running, removing PID file"
        rm -f "$PID_FILE"
    fi
}
status_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ LLMdiver daemon is running (PID: $PID)"
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "📋 Recent log entries:"
                tail -n 5 "$LOG_FILE"
            fi
            if [ -d ".llmdiver" ]; then
                echo ""
                echo "📁 Recent analyses:"
                ls -lt .llmdiver/*.md 2>/dev/null | head -n 3
            fi
            return 0
        else
            echo "❌ LLMdiver daemon is not running (stale PID file)"
            return 1
        fi
    else
        echo "❌ LLMdiver daemon is not running"
        return 1
    fi
}
restart_daemon() {
    stop_daemon
    sleep 1
    start_daemon
}
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found"
    fi
}
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the LLMdiver daemon"
        echo "  stop    - Stop the LLMdiver daemon"
        echo "  restart - Restart the LLMdiver daemon"
        echo "  status  - Show daemon status and recent activity"
        echo "  logs    - Show live daemon logs"
        echo ""
        echo "Examples:"
        echo "  ./start_llmdiver.sh start"
        echo "  ./start_llmdiver.sh status"
        echo "  ./start_llmdiver.sh logs"
        exit 1
        ;;
esac
```

## File: start_qml.sh
```bash
echo "🚀 Starting Gmail Spam Bot QML Interface..."
echo "==============================================="
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed."
    exit 1
fi
echo "✓ Python3 found"
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi
echo "✓ Virtual environment found"
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "🔍 Checking PySide6 installation..."
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "📦 PySide6 not found. Installing..."
    pip install PySide6
fi
echo "✓ PySide6 ready"
echo "🏥 Starting health check server..."
if ! pgrep -f "health_check.py" > /dev/null; then
    python3 health_check.py &
    HEALTH_PID=$!
    echo "✓ Health check server started (PID: $HEALTH_PID)"
    sleep 2
else
    echo "✓ Health check server already running"
fi
echo "🧠 Checking LM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✓ LM Studio is running and accessible"
else
    echo "⚠️  LM Studio not detected. Some features may be limited."
    echo "   Please start LM Studio and load a model for full functionality."
fi
echo ""
echo "🎯 Launching QML Interface..."
echo "📱 Features:"
echo "   • Modern dark theme interface"
echo "   • Real-time LM Studio integration"
echo "   • Smart model switching (Phi-3, Llama-8B, CodeLlama)"
echo "   • Live email processing monitoring"
echo "   • Comprehensive audit log with restore"
echo "   • Advanced settings management"
echo ""
# Set environment variables for Qt
export QT_QPA_PLATFORM_PLUGIN_PATH="$VIRTUAL_ENV/lib/python*/site-packages/PySide6/Qt/plugins"
export QML_IMPORT_PATH="qml"
python3 qml_main.py
echo ""
echo "🛑 Shutting down..."
if [ ! -z "$HEALTH_PID" ]; then
    kill $HEALTH_PID 2>/dev/null
    echo "✓ Health check server stopped"
fi
echo "👋 Gmail Spam Bot QML interface closed."
```

## File: start_stable.sh
```bash
echo "🚀 Starting Gmail Cleaner with stability improvements..."
export PYTHONHASHSEED=0
export PYTHONMALLOC=malloc
export MALLOC_CHECK_=0
ulimit -s 16384
start_gui() {
    local attempt=1
    local max_attempts=3
    while [ $attempt -le $max_attempts ]; do
        echo "🖥️  Starting GUI (attempt $attempt/$max_attempts)..."
        python3 gmail_lm_cleaner.py 2>&1 | tee -a logs/gui_session.log
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "✅ GUI closed normally"
            break
        elif [ $exit_code -eq 139 ]; then
            echo "💥 Segmentation fault detected (exit code $exit_code)"
            echo "🔄 Attempting to restart GUI..."
            pkill -f "python.*gmail_lm_cleaner"
            sleep 2
            export QT_X11_NO_MITSHM=1
            export GDK_SYNCHRONIZE=1
            ((attempt++))
        else
            echo "❌ GUI exited with code $exit_code"
            break
        fi
        if [ $attempt -le $max_attempts ]; then
            echo "⏳ Waiting 5 seconds before retry..."
            sleep 5
        fi
    done
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ GUI failed to start after $max_attempts attempts"
        echo "💡 You can still monitor processing with:"
        echo "   tail -f logs/email_processing.log"
        echo "   python progress_monitor.py"
        return 1
    fi
}
if pgrep -f "bulk_processor.py" > /dev/null; then
    echo "✅ Bulk processor is already running"
    echo "📊 Current processing status:"
    python3 -c "
from gmail_api_utils import get_gmail_service
try:
    service = get_gmail_service()
    if service:
        inbox = service.users().labels().get(userId='me', id='INBOX').execute()
        print(f'   📧 Unread emails remaining: {inbox.get(\"messagesUnread\", \"Unknown\")}')
    else:
        print('   ⚠️  Could not connect to Gmail')
except Exception as e:
    print(f'   ❌ Error checking status: {e}')
"
else
    echo "⚠️  Bulk processor is not running"
    echo "🚀 Starting bulk processor in background..."
    nohup python3 bulk_processor.py > "bulk_processing_$(date +%H%M).log" 2>&1 &
    echo "✅ Bulk processor started"
fi
echo ""
echo "🖥️  Starting GUI interface..."
# Start the GUI
start_gui
echo ""
echo "👋 Gmail Cleaner session ended"
echo "📊 Processing continues in background if bulk processor is running"
echo ""
echo "📋 Useful commands:"
echo "   📈 Monitor progress:    python progress_monitor.py"
echo "   📝 Check logs:         tail -f logs/email_processing.log"
echo "   🔄 Restart GUI:        python gmail_lm_cleaner.py"
echo "   ⏹️  Stop processing:    pkill -f bulk_processor"
echo ""
```

## File: start.sh
```bash
echo "🚀 Gmail Intelligent Cleaner - Starting Up"
echo "=========================================="
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first:"
    echo "   sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi
echo "✓ Python3 found"
echo "📦 Checking Python dependencies..."
packages=(
    "google-auth"
    "google-auth-oauthlib"
    "google-auth-httplib2"
    "google-api-python-client"
    "google-generativeai"
    "python-dotenv"
    "requests"
    "PySide6"
)
missing_packages=()
for package in "${packages[@]}"; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done
if [ ${
    echo "📥 Installing missing packages: ${missing_packages[*]}"
    pip3 install "${missing_packages[@]}"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install packages. Trying with --user flag..."
        pip3 install --user "${missing_packages[@]}"
        if [ $? -ne 0 ]; then
            echo "❌ Package installation failed. Please run manually:"
            echo "   pip3 install ${missing_packages[*]}"
            exit 1
        fi
    fi
fi
echo "✓ All dependencies installed"
if [ ! -d "config" ]; then
    echo "📁 Creating config directory..."
    mkdir -p config
fi
if [ ! -f "config/credentials.json" ]; then
    echo "⚠️  config/credentials.json not found!"
    echo "   Please download your Gmail API credentials and place them as 'config/credentials.json'"
    echo "   Get them from: https://console.cloud.google.com/apis/credentials"
    echo ""
    read -p "Press Enter when you've added config/credentials.json, or Ctrl+C to exit..."
fi
# Check for token.json and warn about new scopes
if [ -f "config/token.json" ]; then
    echo "⚠️  Found existing token.json - you may need to re-authenticate"
    echo "   New scopes have been added (gmail.send for unsubscribe emails)"
    echo "   If you encounter auth errors, delete config/token.json and restart"
fi
if [ ! -f "config/settings.json" ]; then
    echo "📄 Creating default config/settings.json..."
    cat > config/settings.json << EOF
{
  "important_keywords": [
    "security alert", "account suspended", "verify your account", "confirm your identity",
    "password reset", "login attempt", "suspicious activity", "unauthorized access",
    "fraud alert", "payment failed", "invoice due", "tax notice", "bank statement",
    "urgent action required", "account expires", "verification code"
  ],
  "important_senders": [
    "security@", "alerts@", "fraud@", "admin@",
    "billing@", "accounts@", "statements@"
  ],
  "promotional_keywords": [
    "sale", "discount", "offer", "deal", "coupon", "promo", "marketing",
    "newsletter", "unsubscribe", "shop", "buy", "limited time", "free"
  ],
  "auto_delete_senders": [],
  "never_delete_senders": [],
  "max_emails_per_run": 50,
  "days_back": 7,
  "dry_run": false,
  "lm_studio_model": "meta-llama-3.1-8b-instruct"
}
EOF
fi
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   For Gemini auto-analysis, create a .env file with your API key:"
    echo "   cp .env.example .env"
    echo "   Then edit .env and add your Gemini API key from https://aistudio.google.com/app/apikey"
    echo "   (This is optional - the app works without Gemini)"
    echo ""
fi
# Check if LM Studio is running (optional)
echo "🤖 Checking LM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✓ LM Studio is running"
else
    echo "⚠️  LM Studio not detected on port 1234"
    echo "   The app will still work, but email analysis will be limited"
    echo "   Start LM Studio and load a model for full functionality"
fi
echo ""
echo "🎯 Starting Gmail Cleaner QML Interface..."
echo "   📱 Modern Qt/QML dark theme interface"
echo "   🧠 Smart LM Studio integration with model switching"
echo "   🚨 INBOX: Critical emails only (security alerts, personal messages)"
echo "   ⚡ PRIORITY: Important but not urgent (GitHub, Zillow, bank statements)"
echo "   📦 Other categories: Bills, Shopping, Newsletters, Social, Personal, Junk"
echo "   🔧 Filter-first processing for massive email backlogs"
echo "   🤖 Machine learning-like pattern recognition and rule suggestions"
echo "   📊 Real-time analytics with filter effectiveness tracking"
echo "   ✉️  Automated unsubscribe workflow (HTTP links + mailto handling)"
echo "   🛡️  Crash-proof UI with comprehensive exception handling"
echo ""
echo "   Close the QML window or press Ctrl+C here to stop"
echo ""
# Start health check server in background
echo "🏥 Starting health check server..."
if ! pgrep -f "health_check.py" > /dev/null; then
    python3 health_check.py &
    HEALTH_PID=$!
    echo "✓ Health check server started (PID: $HEALTH_PID)"
    sleep 2
else
    echo "✓ Health check server already running"
fi
echo "⚠️  Running in headless mode - QML interface will run in offscreen mode"
export QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"
export QML_IMPORT_PATH="qml"
python3 qml_main.py &
QML_PID=$!
echo "✓ QML interface launched (PID: $QML_PID)"
echo ""
echo "📱 QML Interface Features:"
echo "   • Smart Email Categorization with LM Studio"
echo "   • Real-time Processing Dashboard"
echo "   • Comprehensive Audit Logging"
echo "   • Advanced Settings Management"
echo ""
echo "🌐 Web Interface (if needed): http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all services"
wait $QML_PID
echo ""
echo "🛑 Shutting down..."
if [ ! -z "$HEALTH_PID" ]; then
    kill $HEALTH_PID 2>/dev/null
    echo "✓ Health check server stopped"
fi
echo ""
echo "👋 Gmail Cleaner stopped"
```

## File: stop.sh
```bash
echo "🛑 Gmail Intelligent Cleaner - Shutting Down"
echo "============================================"
echo "🔍 Stopping processes using PID files..."
stop_process_with_fallback() {
    local process_name="$1"
    local script_pattern="$2"
    if [ -f "pids/${process_name}.pid" ]; then
        pid=$(cat "pids/${process_name}.pid" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "   Found ${process_name} via PID file (PID: $pid) - stopping gracefully..."
            kill -TERM "$pid" 2>/dev/null
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo "   ✅ ${process_name} stopped gracefully"
                    rm -f "pids/${process_name}.pid" 2>/dev/null
                    return 0
                fi
                sleep 1
            done
            if kill -0 "$pid" 2>/dev/null; then
                echo "   ⚠️  Force killing ${process_name}..."
                kill -KILL "$pid" 2>/dev/null
                sleep 1
                rm -f "pids/${process_name}.pid" 2>/dev/null
            fi
        else
            echo "   ℹ️  Stale PID file for ${process_name}, cleaning up..."
            rm -f "pids/${process_name}.pid" 2>/dev/null
        fi
    fi
    fallback_pids=$(pgrep -f "$script_pattern" 2>/dev/null)
    if [ -n "$fallback_pids" ]; then
        echo "   Found ${process_name} via process search (PID: $fallback_pids) - stopping..."
        kill -TERM $fallback_pids 2>/dev/null
        sleep 2
        still_running=$(pgrep -f "$script_pattern" 2>/dev/null)
        if [ -n "$still_running" ]; then
            echo "   ⚠️  Force killing remaining ${process_name} processes..."
            kill -KILL $still_running 2>/dev/null
            sleep 1
        fi
        echo "   ✅ ${process_name} stopped"
    else
        echo "   ℹ️  No ${process_name} processes running"
    fi
}
echo "🔍 Stopping bulk processor..."
stop_process_with_fallback "bulk_processor" "bulk_processor.py"
echo "🔍 Stopping autonomous runner..."
stop_process_with_fallback "autonomous_runner" "autonomous_runner.py"
echo "🔍 Looking for other Gmail Cleaner processes..."
other_pids=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)
if [ -n "$other_pids" ]; then
    echo "🔄 Found other Gmail Cleaner processes: $other_pids"
    echo "   Sending termination signal..."
    kill -TERM $other_pids 2>/dev/null
    sleep 3
    still_running=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)
    if [ -n "$still_running" ]; then
        echo "⚠️  Processes still running, forcing shutdown..."
        kill -KILL $still_running 2>/dev/null
        sleep 1
    fi
    final_check=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)
    if [ -z "$final_check" ]; then
        echo "✓ Other Gmail Cleaner processes stopped successfully"
    else
        echo "❌ Some processes may still be running. Try running this script again."
        exit 1
    fi
else
    echo "ℹ️  No other Gmail Cleaner processes found running"
fi
echo "🤖 Cleaning up LM Studio processes..."
lm_processes=$(pgrep -f "lmstudio\|llama\|llamacpp" 2>/dev/null || true)
if [ -n "$lm_processes" ]; then
    echo "   Found LM Studio processes: $lm_processes"
    echo "   Sending termination signal to LM Studio..."
    pkill -f "lmstudio" 2>/dev/null || true
    pkill -f "llama" 2>/dev/null || true
    pkill -f "llamacpp" 2>/dev/null || true
    sleep 3
    if pgrep -f "lmstudio\|llama\|llamacpp" > /dev/null 2>&1; then
        echo "   Force stopping LM Studio processes..."
        killall -9 lmstudio 2>/dev/null || true
        killall -9 lmstudio-cli 2>/dev/null || true
        killall -9 llama-server 2>/dev/null || true
        killall -9 llamacpp 2>/dev/null || true
        pkill -9 -f "lmstudio" 2>/dev/null || true
        pkill -9 -f "llama" 2>/dev/null || true
        sleep 2
    fi
    remaining=$(pgrep -f "lmstudio\|llama\|llamacpp" 2>/dev/null || true)
    if [ -z "$remaining" ]; then
        echo "   ✅ LM Studio processes stopped successfully"
    else
        echo "   ⚠️  Some LM Studio processes may still be running: $remaining"
    fi
else
    echo "   ℹ️  No LM Studio processes found"
fi
echo "🔍 Checking LM Studio API status..."
if command -v curl > /dev/null 2>&1; then
    api_response=$(curl -s --connect-timeout 2 http://localhost:1234/v1/models 2>/dev/null || echo "offline")
    if [[ "$api_response" == *"offline"* ]] || [[ "$api_response" == "" ]]; then
        echo "   ✅ LM Studio API is offline"
    else
        echo "   ⚠️  LM Studio API may still be responding"
        echo "   💡 You may need to manually stop LM Studio app"
    fi
else
    echo "   ℹ️  curl not available, cannot test API status"
fi
echo "🧹 Cleaning up temporary files..."
temp_files=(
    "*.tmp"
    "*.log"
    "__pycache__"
    "*.pyc"
)
cleaned_any=false
for pattern in "${temp_files[@]}"; do
    if ls $pattern 1> /dev/null 2>&1; then
        rm -rf $pattern
        echo "   Removed: $pattern"
        cleaned_any=true
    fi
done
if [ "$cleaned_any" = false ]; then
    echo "   No temporary files to clean"
fi
echo ""
echo "📊 Current Status:"
if [ -f "config/settings.json" ]; then
    echo "   ✓ Settings file preserved: config/settings.json"
else
    echo "   ℹ️  No settings file found"
fi
if [ -f "config/token.json" ]; then
    echo "   ✓ Authentication token preserved: config/token.json"
else
    echo "   ℹ️  No authentication token found"
fi
if [ -f "config/credentials.json" ]; then
    echo "   ✓ Gmail credentials preserved: config/credentials.json"
else
    echo "   ⚠️  No Gmail credentials found"
fi
echo ""
echo "✅ Gmail Cleaner shutdown complete"
echo "   • Gmail Cleaner processes stopped"
echo "   • Bulk processor stopped"
echo "   • LM Studio processes cleaned up"
echo "   • Your settings and authentication are preserved"
echo ""
echo "🚀 To restart:"
echo "   ./start.sh        - Start with current settings"
echo "   ./start_stable.sh - Start with stability improvements"
echo ""
echo "🧪 Before restarting LM Studio:"
echo "   python test_lm_studio.py - Test LM Studio connectivity"
```

## File: test_automation.py
```python
def slow_function()
⋮----
result = []
⋮----
def mock_api_call()
def unused_function()
class TestClass
⋮----
def __init__(self)
def process_data(self)
```

## File: test_llmdiver.sh
```bash
echo "🧪 Testing LLMdiver Automation"
echo "================================="
if ./start_llmdiver.sh status >/dev/null 2>&1; then
    echo "✅ Daemon is running"
else
    echo "❌ Daemon not running - starting it..."
    ./start_llmdiver.sh start
    sleep 2
fi
echo ""
echo "📝 Creating test file with TODOs and issues..."
# Create a test file with obvious issues
cat > test_llmdiver_trigger.py << 'EOF'
#!/usr/bin/env python3
"""
Test file to trigger LLMdiver analysis
Contains various code issues for testing
"""
# TODO: This needs to be implemented properly
def broken_function():
    """This function has issues"""
    # FIXME: Infinite loop risk
    while True:
        pass
# Mock implementation - needs real code
def mock_data_processor():
    """Stub - replace with real implementation"""
    return {"mock": "data"}
def unused_helper():
    """This function is never called"""
    print("Dead code detected")
def risky_operation():
    result = 10 / 0
    return result
if __name__ == "__main__":
    print("Test file created - LLMdiver should detect issues")
EOF
echo "✅ Test file created: test_llmdiver_trigger.py"
echo ""
echo "🔍 Monitoring daemon logs (watch for file detection)..."
echo "   Press Ctrl+C to stop monitoring"
echo ""
# Show real-time logs
timeout 30 tail -f llmdiver_daemon.log || echo ""
echo ""
echo "📊 Checking results..."
# Check if analysis was created
if [ -d ".llmdiver" ] && [ -f ".llmdiver/latest_analysis.md" ]; then
    echo "✅ Analysis completed"
    echo "📁 Latest analysis:"
    ls -la .llmdiver/analysis_*.md | tail -n 1
    echo ""
    echo "📋 Analysis content:"
    echo "===================="
    head -n 20 .llmdiver/latest_analysis.md
else
    echo "⏳ Analysis still in progress or failed"
fi
echo ""
echo "🔄 Recent git commits:"
git log --oneline -3
echo ""
echo "🧹 Cleaning up test file..."
rm -f test_llmdiver_trigger.py
echo ""
echo "✅ Test completed! Check the logs above for automation results."
```

## File: test_lm_studio.py
```python
def test_lm_studio()
⋮----
response = requests.get('http://localhost:1234/v1/models', timeout=5)
⋮----
models = response.json()
⋮----
test_payload = {
start_time = time.time()
response = requests.post(
end_time = time.time()
⋮----
duration = end_time - start_time
result = response.json()
content = result['choices'][0]['message']['content']
```

## File: test_oauth_scopes.py
```python
def test_oauth_scopes()
⋮----
cleaner = GmailLMCleaner()
⋮----
profile = cleaner.service.users().getProfile(userId='me').execute()
⋮----
filters = cleaner.service.users().settings().filters().list(userId='me').execute()
filter_count = len(filters.get('filter', []))
⋮----
error_msg = str(e)
```

## File: test_real_categorization.py
```python
def parse_email_subjects(file_path)
⋮----
emails = []
⋮----
content = f.read()
email_pattern = r'\d+\.\s+Subject:\s+(.+?)\n\s+From:\s+(.+?)\n'
matches = re.findall(email_pattern, content)
⋮----
def test_categorization()
⋮----
email_file = Path("email_subjects.txt")
⋮----
emails = parse_email_subjects(email_file)
⋮----
subjects = [email['subject'] for email in emails]
senders = [email['sender'] for email in emails]
⋮----
results = lm_studio.categorize_emails_batch(subjects, senders)
⋮----
email = emails[i]
index = result.get('index', i + 1)
category = result.get('category', 'UNKNOWN')
```

## File: test-qml.sh
```bash
echo "🧪 Testing QML Interface on Pop!_OS..."
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "❌ No display detected. Make sure you're running in a GUI environment."
    exit 1
fi
echo "✅ Display detected: $DISPLAY $WAYLAND_DISPLAY"
echo "🔍 Checking PySide6 installation..."
if python3 -c "import PySide6" 2>/dev/null; then
    echo "✅ PySide6 is installed"
else
    echo "📦 Installing PySide6..."
    pip3 install --user PySide6
fi
echo "🧪 Testing basic Qt functionality..."
python3 -c "
from PySide6.QtWidgets import QApplication, QLabel
import sys
app = QApplication(sys.argv)
label = QLabel('✅ Qt Works!')
label.show()
print('Qt test window should appear...')
app.processEvents()
import time
time.sleep(2)
app.quit()
" || {
    echo "❌ Qt test failed. Installing missing dependencies..."
    sudo apt update
    sudo apt install -y qt6-base-dev libegl1 libgl1-mesa-glx python3-pyside6*
}
echo "🖥️  Ensuring visual mode..."
unset QT_QPA_PLATFORM
echo "🚀 Launching Gmail Cleaner QML Interface..."
echo "📱 You should see a modern dark-themed window with Gmail Cleaner interface"
echo ""
# Make sure we're in the right directory
cd "$(dirname "$0")"
# Launch with proper environment
QML_IMPORT_PATH="qml" python3 qml_main.py
```



## AI Analysis

Here is a consolidated version of the findings, prioritized by criticality:

**Critical Issues**

1. **Infinite loops and performance issues**: The code has several instances of infinite loops or performance issues, such as `time.sleep` calls with long intervals (e.g., 300 seconds) which can cause the program to hang indefinitely.
2. **Missing error handling**: Several methods do not handle potential exceptions that may occur during execution, leading to unexpected behavior or errors.
3. **Unreliable process termination**: The use of `pgrep -f` and `pkill -f` can be unreliable due to the way it matches patterns, potentially leading to incorrect process termination.

**High-Priority Issues**

1. **TODO comments and FIXME items**: The code has many TODO comments throughout the files, indicating that it is still in development or has known issues.
2. **Mock/Stub Implementations**: There are no mock or stub implementations in the provided code, making it difficult to test and maintain.
3. **Dead Code Candidates**: Several functions and methods appear to be dead code and can be removed.

**Medium-Priority Issues**

1. **Performance Concerns**: The code has several performance concerns, such as slow data processing and inefficient pagination handling.
2. **Architectural Improvements**: The code uses a mix of synchronous and asynchronous programming, which can make it difficult to reason about the program's behavior.
3. **Improper Authentication Mechanism**: The code appears to be using hardcoded credentials, which is not secure.

**Low-Priority Issues**

1. **Unused Functions**: Several functions are never called or used in the codebase.
2. **Slow Functionality**: Some functions appear to be slow due to inefficient algorithms or data structures.
3. **Improper Logging and Error Handling**: The code does not have proper logging and error handling mechanisms.

**Recommendations**

1. Address critical issues by implementing proper error handling, process termination mechanisms, and removing dead code.
2. Prioritize high-priority issues by implementing mock/stub implementations, refactoring the code to improve performance, and addressing TODO comments and FIXME items.
3. Address medium-priority issues by improving pagination handling, using a more robust authentication mechanism, and refactoring the code to use a consistent programming approach.
4. Address low-priority issues by removing unused functions, optimizing slow functionality, and implementing proper logging and error handling mechanisms.