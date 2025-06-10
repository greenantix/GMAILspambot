# Gmail Autonomy Plan: Gemini + LM Studio Integration

## 1. Objective
Split AI workload for optimal performance and cost:
- **Gemini**: Periodic batch analysis (weekly/monthly) to generate filtering rules and label schemas
- **LM Studio**: Real-time email categorization using Gemini-generated rules
- **Automation**: Scheduled processing with minimal human intervention

## 2. Initial Gemini Batch Analysis

### Export Process
```bash
# Export last 30 days of emails (cron: 0 3 * * 0)
python3 export_subjects.py --max-emails 2000 --days-back 30 --output analysis_$(date +%Y%m%d).txt
```

### Gemini Analysis Request
- Submit exported file to Gemini with structured prompt
- Request output format:
```json
{
  "label_schema": {
    "create": ["BILLS", "SHOPPING", "NEWSLETTERS"],
    "delete": ["OLD_PROMO_2023"],
    "rename": {"MISC": "PERSONAL"}
  },
  "category_rules": {
    "BILLS": {
      "keywords": ["invoice", "receipt", "statement"],
      "senders": ["billing@", "payments@"],
      "action": "LABEL_AND_ARCHIVE"
    }
  },
  "auto_operations": {
    "delete_after_days": {"NEWSLETTERS": 30, "SHOPPING": 90},
    "auto_delete_senders": ["noreply@spam.com"],
    "never_touch": ["security@bank.com"]
  }
}
```

## 3. Apply Gemini Output to Settings

### Automated Configuration Update
```python
# gemini_config_updater.py
def apply_gemini_config(gemini_output, settings_path="settings.json"):
    # 1. Parse Gemini JSON response
    rules = json.loads(gemini_output)
    
    # 2. Update settings structure
    settings = {
        "important_keywords": rules["category_rules"]["INBOX"]["keywords"],
        "important_senders": rules["category_rules"]["INBOX"]["senders"],
        "category_rules": rules["category_rules"],
        "auto_delete_senders": rules["auto_operations"]["auto_delete_senders"],
        "never_delete_senders": rules["auto_operations"]["never_touch"],
        "label_actions": {
            label: rule["action"] 
            for label, rule in rules["category_rules"].items()
        }
    }
    
    # 3. Create/delete Gmail labels via API
    create_labels(rules["label_schema"]["create"])
    delete_labels(rules["label_schema"]["delete"])
```

### Label Action Mappings
- `KEEP_INBOX`: No modification
- `LABEL_ONLY`: Add label, keep in inbox
- `LABEL_AND_ARCHIVE`: Add label, remove from inbox
- `TRASH`: Move to trash immediately
- `DELETE_AFTER_X`: Add expiration metadata

## 4. LM Studio Workflow

### Email Processing Logic
```python
def process_email_with_llm(email_data, category_rules):
    # 1. Pre-filter using Gemini rules
    for category, rules in category_rules.items():
        if matches_rules(email_data, rules):
            return {"action": rules["action"], "label": category}
    
    # 2. LM Studio categorization for unknowns
    prompt = f"""
    Categorize this email using ONLY these labels: {list(category_rules.keys())}
    Email: {email_data['subject']} from {email_data['sender']}
    
    Rules:
    - INBOX: Only urgent/security alerts
    - Default to most appropriate category
    - When uncertain, use PERSONAL
    """
    
    # 3. Execute label action from mapping
    return llm_categorize(prompt)
```

### Conservative Defaults
- Unknown senders → `PERSONAL` label
- Failed LLM calls → Keep in inbox
- Parse errors → Log and skip
- Rate limits → Exponential backoff

## 5. Scheduled Automation

### Systemd Service Setup
```ini
# /etc/systemd/system/gmail-autonomy.service
[Unit]
Description=Gmail Autonomous Organizer
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/path/to/greenantix-gmailspambot
ExecStart=/usr/bin/python3 autonomous_runner.py
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

### Autonomous Runner Script
```python
# autonomous_runner.py
while True:
    # 1. Check if Gemini analysis needed (weekly)
    if needs_analysis():
        export_and_analyze()
        apply_gemini_config()
    
    # 2. Process new emails (every 15 min)
    process_new_emails(dry_run=False, batch_size=50)
    
    # 3. Cleanup old emails based on retention rules
    cleanup_expired_emails()
    
    time.sleep(900)  # 15 minutes
```

### Cron Alternative
```bash
# crontab -e
# Weekly Gemini analysis
0 2 * * 0 /path/to/start.sh --mode analyze

# Email processing every 30 minutes
*/30 * * * * /path/to/start.sh --mode process --batch 25
```

## 6. Monitoring & Logging

### Structured Logging
```python
# log_config.py
LOGS = {
    "operations": "/var/log/gmail-bot/operations.log",
    "errors": "/var/log/gmail-bot/errors.log", 
    "audit": "/var/log/gmail-bot/audit.log"
}

# Log format
{
    "timestamp": "2025-01-10T14:30:00Z",
    "email_id": "18abc123",
    "action": "LABEL_AND_ARCHIVE",
    "label": "SHOPPING",
    "confidence": 0.92,
    "dry_run": false
}
```

### Error Handling
- Gmail API failures → Retry with backoff
- Label creation errors → Fallback to existing labels
- LM Studio timeouts → Skip to next email
- Gemini API limits → Cache last analysis for 7 days

### Monitoring Dashboard
```bash
# monitor.sh
tail -f /var/log/gmail-bot/operations.log | \
  jq 'select(.action == "ERROR") | {time: .timestamp, error: .message}'
```

## 7. Human Control

### GUI Overrides
- **Force Analysis**: Trigger Gemini analysis on-demand
- **Dry Run Toggle**: Test changes without executing
- **Rule Editor**: Modify category_rules post-Gemini
- **Undo Actions**: Restore emails from audit log

### Manual Intervention Points
```python
# Override mechanisms in settings.json
{
  "manual_overrides": {
    "force_inbox": ["boss@company.com"],
    "blocked_actions": ["DELETE"],
    "require_confirmation": ["TRASH", "DELETE_AFTER_X"]
  }
}
```

### Audit Commands
```bash
# Review today's actions
python3 audit_tool.py --date today --action TRASH

# Restore mistakenly processed emails
python3 audit_tool.py --restore --email-id 18abc123

# Export processing stats
python3 audit_tool.py --stats --format csv > monthly_report.csv
```

## 8. Future Extensions

### Gemini Model Refinement
- Track user corrections (moved emails back to inbox)
- Submit correction data to Gemini for rule refinement
- A/B test new rules on subset before full deployment

### LM Studio Optimization
- Fine-tune local model on categorized email dataset
- Implement confidence thresholds for auto-actions
- Model swap based on email language/domain

### Advanced Features
- **Smart Unsubscribe**: Detect and execute unsubscribe links
- **Attachment Handling**: Extract and organize attachments by type
- **Multi-Account**: Process multiple Gmail accounts in parallel
- **Webhooks**: Notify external systems of important emails
- **NLP Summaries**: Daily digest of important emails via Gemini
