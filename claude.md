# Gmail Autonomy Plan: Complete TODO Implementation

## 1. Executive Summary
Current state: Core components exist but lack integration. Key gaps:
- Gmail API label management (stubbed)
- Autonomous runner functions (stubbed)
- Component integration pipeline
- Real-time processing implementation

## 2. Gmail API Integration

### Label Management Implementation
```python
# gmail_api_utils.py - NEW FILE
from googleapiclient.errors import HttpError

class GmailLabelManager:
    def __init__(self, service):
        self.service = service
        self._label_cache = {}
    
    def refresh_label_cache(self):
        """Cache existing labels to avoid repeated API calls"""
        results = self.service.users().labels().list(userId='me').execute()
        self._label_cache = {label['name']: label['id'] 
                           for label in results.get('labels', [])}
    
    def create_label(self, label_name, label_color=None):
        """Create Gmail label with error handling"""
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
            return created['id']
        except HttpError as e:
            if e.resp.status == 409:  # Already exists
                self.refresh_label_cache()
                return self._label_cache.get(label_name)
            raise
    
    def delete_label(self, label_name):
        """Delete Gmail label by name"""
        label_id = self._label_cache.get(label_name)
        if not label_id:
            return False
            
        try:
            self.service.users().labels().delete(
                userId='me', id=label_id).execute()
            del self._label_cache[label_name]
            return True
        except HttpError:
            return False
    
    def rename_label(self, old_name, new_name):
        """Rename label via delete + create + reassign"""
        # Get emails with old label
        old_id = self._label_cache.get(old_name)
        if not old_id:
            return False
            
        # Find affected emails
        results = self.service.users().messages().list(
            userId='me', labelIds=[old_id]).execute()
        message_ids = [m['id'] for m in results.get('messages', [])]
        
        # Create new label
        new_id = self.create_label(new_name)
        
        # Batch update messages
        for msg_id in message_ids:
            self.service.users().messages().modify(
                userId='me', id=msg_id,
                body={'addLabelIds': [new_id], 
                      'removeLabelIds': [old_id]}
            ).execute()
        
        # Delete old label
        return self.delete_label(old_name)
```

### Update gemini_config_updater.py
```python
# Replace stub functions with actual implementation
def update_label_schema(label_schema, service, logger):
    """Implement actual Gmail label operations"""
    manager = GmailLabelManager(service)
    manager.refresh_label_cache()
    
    # Create labels with colors
    label_colors = {
        'BILLS': {'backgroundColor': '#fb4c2f', 'textColor': '#ffffff'},
        'SHOPPING': {'backgroundColor': '#ffad47', 'textColor': '#000000'},
        'NEWSLETTERS': {'backgroundColor': '#7986cb', 'textColor': '#ffffff'},
        'SOCIAL': {'backgroundColor': '#33b679', 'textColor': '#ffffff'},
        'PERSONAL': {'backgroundColor': '#673ab7', 'textColor': '#ffffff'}
    }
    
    for label in label_schema.get("create", []):
        try:
            color = label_colors.get(label)
            manager.create_label(label, color)
            logger.info(f"Created label '{label}'")
        except Exception as e:
            logger.error(f"Failed to create label '{label}': {e}")
    
    for label in label_schema.get("delete", []):
        if manager.delete_label(label):
            logger.info(f"Deleted label '{label}'")
        else:
            logger.warning(f"Could not delete label '{label}'")
    
    for old, new in label_schema.get("rename", {}).items():
        if manager.rename_label(old, new):
            logger.info(f"Renamed label '{old}' to '{new}'")
        else:
            logger.error(f"Failed to rename '{old}' to '{new}'")
```

## 3. Autonomous Runner Implementation

### Replace Stub Functions
```python
# autonomous_runner.py - Update stub implementations

import subprocess
import shutil

def run_export_emails(export_dir, days_back=30, max_emails=2000):
    """Execute actual email export"""
    logger = get_logger(__name__)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    export_path = os.path.join(export_dir, f"emails_{timestamp}.txt")
    
    try:
        cmd = [
            sys.executable, "export_subjects.py",
            "--max-emails", str(max_emails),
            "--days-back", str(days_back),
            "--output", export_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Exported emails to {export_path}")
            return export_path
        else:
            logger.error(f"Export failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Export error: {e}")
        return None

def run_gemini_analysis(export_path, output_dir, api_key):
    """Execute Gemini analysis on exported emails"""
    logger = get_logger(__name__)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f"gemini_rules_{timestamp}.json")
    
    try:
        # Initialize Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Read export file
        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Gemini prompt for rule generation
        prompt = f"""Analyze these email subjects and generate filtering rules.

{content}

Generate a JSON response with:
1. label_schema: Labels to create/delete/rename
2. category_rules: Keywords and senders for each category
3. auto_operations: Retention policies and auto-delete lists

Categories: INBOX (urgent only), BILLS, SHOPPING, NEWSLETTERS, SOCIAL, PERSONAL, JUNK

Output ONLY valid JSON."""
        
        response = model.generate_content(prompt)
        rules = json.loads(response.text)
        
        # Save rules
        with open(output_path, 'w') as f:
            json.dump(rules, f, indent=2)
        
        logger.info(f"Gemini analysis saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return None

def process_new_emails(settings, batch_size=50):
    """Process new emails using LM Studio"""
    logger = get_logger(__name__)
    
    try:
        # Initialize Gmail cleaner with current settings
        from gmail_lm_cleaner import GmailLMCleaner
        cleaner = GmailLMCleaner(settings_file=SETTINGS_PATH)
        
        # Update cleaner settings from autonomous config
        cleaner.settings.update({
            'max_emails_per_run': batch_size,
            'dry_run': settings.get('automation', {}).get('dry_run', False),
            'days_back': 1  # Only process recent emails in real-time mode
        })
        
        # Process inbox
        processed_count = 0
        cleaner.process_inbox(log_callback=lambda msg: logger.info(msg))
        
        logger.info(f"Processed batch of {batch_size} emails")
        return True
        
    except Exception as e:
        logger.error(f"Email processing failed: {e}")
        return False
```

## 4. Enhanced Scheduling System

### Flexible Cron Parser
```python
# cron_utils.py - NEW FILE
from croniter import croniter
from datetime import datetime

class ScheduleManager:
    def __init__(self, settings):
        self.settings = settings
        self.schedules = {
            'batch_analysis': croniter(
                settings.get('automation', {}).get('batch_analysis_cron', '0 3 * * 0'),
                datetime.utcnow()
            ),
            'realtime_processing': croniter(
                settings.get('automation', {}).get('realtime_cron', '*/15 * * * *'),
                datetime.utcnow()
            ),
            'cleanup': croniter(
                settings.get('automation', {}).get('cleanup_cron', '0 4 * * *'),
                datetime.utcnow()
            )
        }
    
    def get_next_run(self, job_name):
        """Get next scheduled time for job"""
        return self.schedules[job_name].get_next(datetime)
    
    def should_run_now(self, job_name, last_run=None):
        """Check if job should run now"""
        if last_run is None:
            return True
        next_run = self.schedules[job_name].get_next(datetime)
        return datetime.utcnow() >= next_run
```

### Update autonomous_runner.py Main Loop
```python
def main():
    # Initialize components
    settings = load_settings(SETTINGS_PATH)
    init_logging(log_dir=settings.get("paths", {}).get("logs", "logs"))
    logger = get_logger(__name__)
    
    # Initialize scheduler
    scheduler = ScheduleManager(settings)
    
    # Track last runs
    state = {
        'last_batch_analysis': None,
        'last_realtime': None,
        'last_cleanup': None
    }
    
    # Load state from file if exists
    state_file = os.path.join(settings.get("paths", {}).get("data", "."), "automation_state.json")
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            saved_state = json.load(f)
            for key in state:
                if key in saved_state:
                    state[key] = datetime.fromisoformat(saved_state[key])
    
    while True:
        try:
            # Batch Analysis Job
            if scheduler.should_run_now('batch_analysis', state['last_batch_analysis']):
                logger.info("Starting batch analysis job")
                
                export_path = run_export_emails(
                    settings.get("paths", {}).get("exports", "exports"),
                    days_back=settings.get("automation", {}).get("analysis_days_back", 30)
                )
                
                if export_path and os.getenv('GEMINI_API_KEY'):
                    gemini_output = run_gemini_analysis(
                        export_path,
                        settings.get("paths", {}).get("exports", "exports"),
                        os.getenv('GEMINI_API_KEY')
                    )
                    
                    if gemini_output:
                        run_gemini_config_updater(gemini_output, SETTINGS_PATH)
                
                state['last_batch_analysis'] = datetime.utcnow()
            
            # Real-time Processing Job
            if scheduler.should_run_now('realtime_processing', state['last_realtime']):
                logger.info("Starting real-time processing")
                process_new_emails(settings, batch_size=50)
                state['last_realtime'] = datetime.utcnow()
            
            # Cleanup Job
            if scheduler.should_run_now('cleanup', state['last_cleanup']):
                logger.info("Starting cleanup job")
                cleanup_old_emails(settings)
                state['last_cleanup'] = datetime.utcnow()
            
            # Save state
            with open(state_file, 'w') as f:
                json.dump({k: v.isoformat() if v else None for k, v in state.items()}, f)
            
            # Sleep until next job
            next_runs = [
                scheduler.get_next_run('batch_analysis'),
                scheduler.get_next_run('realtime_processing'),
                scheduler.get_next_run('cleanup')
            ]
            sleep_until = min(next_runs)
            sleep_seconds = max(1, (sleep_until - datetime.utcnow()).total_seconds())
            
            logger.debug(f"Sleeping for {sleep_seconds:.0f} seconds until next job")
            time.sleep(min(sleep_seconds, 60))  # Wake at least every minute
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(60)  # Error recovery delay
```

## 5. Email Cleanup Implementation

### Add Retention Policy Enforcement
```python
# email_cleanup.py - NEW FILE
def cleanup_old_emails(settings):
    """Delete emails based on retention policies"""
    logger = get_logger(__name__)
    
    try:
        from gmail_lm_cleaner import GmailLMCleaner
        cleaner = GmailLMCleaner()
        
        # Load retention rules
        rules_path = os.path.join(
            settings.get("paths", {}).get("rules", "rules"),
            "auto_operations.json"
        )
        
        if not os.path.exists(rules_path):
            logger.warning("No retention rules found")
            return
        
        with open(rules_path, 'r') as f:
            auto_ops = json.load(f)
        
        delete_after = auto_ops.get("delete_after_days", {})
        
        for label, days in delete_after.items():
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            query = f'label:{label} before:{cutoff_date}'
            
            results = cleaner.service.users().messages().list(
                userId='me', q=query, maxResults=500
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                logger.info(f"Deleting {len(messages)} old {label} emails")
                
                for msg in messages:
                    try:
                        cleaner.service.users().messages().trash(
                            userId='me', id=msg['id']
                        ).execute()
                    except Exception as e:
                        logger.error(f"Failed to delete {msg['id']}: {e}")
        
        # Empty trash for very old items
        trash_cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y/%m/%d')
        trash_query = f'in:trash before:{trash_cutoff}'
        
        results = cleaner.service.users().messages().list(
            userId='me', q=trash_query, maxResults=1000
        ).execute()
        
        for msg in results.get('messages', []):
            cleaner.service.users().messages().delete(
                userId='me', id=msg['id']
            ).execute()
        
        logger.info("Cleanup complete")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
```

## 6. Audit Tool Gmail API Integration

### Implement Restore Functionality
```python
# Update audit_tool.py restore_action function
def restore_action(entry: Dict[str, Any], service, logger):
    """Restore email to previous state using Gmail API"""
    email_id = entry.get('email_id')
    action = entry.get('action')
    label = entry.get('label')
    
    if not email_id:
        logger.error("No email_id in audit entry")
        return False
    
    try:
        if action == 'TRASH':
            # Untrash the email
            service.users().messages().untrash(
                userId='me', id=email_id
            ).execute()
            logger.info(f"Untrashed email {email_id}")
            
        elif action == 'LABEL_AND_ARCHIVE':
            # Move back to inbox and remove label
            label_id = get_label_id(service, label)
            if label_id:
                service.users().messages().modify(
                    userId='me', id=email_id,
                    body={
                        'addLabelIds': ['INBOX'],
                        'removeLabelIds': [label_id]
                    }
                ).execute()
                logger.info(f"Restored {email_id} to inbox, removed {label}")
            
        elif action == 'DELETE':
            logger.warning(f"Cannot restore permanently deleted email {email_id}")
            return False
            
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            logger.error(f"Email {email_id} not found")
        else:
            logger.error(f"Restore failed: {e}")
        return False
```

## 7. Enhanced Settings Structure

### Update settings.json Format
```json
{
  "automation": {
    "enabled": true,
    "dry_run": false,
    "batch_analysis_cron": "0 3 * * 0",
    "realtime_cron": "*/15 * * * *",
    "cleanup_cron": "0 4 * * *",
    "analysis_days_back": 30,
    "realtime_batch_size": 50
  },
  "paths": {
    "logs": "logs",
    "exports": "exports",
    "rules": "rules",
    "data": "data"
  },
  "gmail": {
    "max_results_per_query": 500,
    "rate_limit_delay": 0.1
  },
  "gemini": {
    "model": "gemini-1.5-flash",
    "temperature": 0.1,
    "max_retries": 3
  },
  "lm_studio": {
    "url": "http://localhost:1234/v1/chat/completions",
    "timeout": 30,
    "temperature": 0.1
  },
  "retention": {
    "default_days": 365,
    "min_days": 7,
    "permanent_labels": ["BILLS", "IMPORTANT"]
  },
  "audit": {
    "enabled": true,
    "retention_days": 90,
    "audit_log_path": "logs/audit.log"
  }
}
```

## 8. System Health Monitoring

### Add Health Check Endpoint
```python
# health_check.py - NEW FILE
from flask import Flask, jsonify
import psutil
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """System health endpoint for monitoring"""
    try:
        # Check process
        pid = os.getpid()
        process = psutil.Process(pid)
        
        # Check Gmail connection
        from gmail_lm_cleaner import GmailLMCleaner
        cleaner = GmailLMCleaner()
        labels = cleaner.service.users().labels().list(userId='me').execute()
        
        # Check LM Studio
        import requests
        lm_status = requests.get('http://localhost:1234/v1/models', timeout=5)
        
        return jsonify({
            'status': 'healthy',
            'uptime': process.create_time(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'gmail': 'connected',
            'lm_studio': 'online' if lm_status.ok else 'offline',
            'last_batch': get_last_run_time('batch_analysis'),
            'last_process': get_last_run_time('realtime_processing')
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
```

## 9. Installation & Deployment

### Complete Setup Script
```bash
#!/bin/bash
# setup.sh - Complete installation

# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv supervisor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client google-generativeai python-dotenv \
    requests croniter flask psutil

# Create directory structure
mkdir -p logs exports rules data

# Set permissions
chmod +x *.py *.sh

# Install as systemd service
sudo cp gmail-autonomy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gmail-autonomy

# Setup log rotation
echo "/path/to/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}" | sudo tee /etc/logrotate.d/gmail-autonomy

echo "✅ Setup complete. Run 'sudo systemctl start gmail-autonomy' to begin"
```