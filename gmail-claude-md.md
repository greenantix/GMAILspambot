# Gmail Automation System - Claude Enhancement Guide

## 🚨 CRITICAL ISSUE TO FIX FIRST

### Current Error: "'subject'" KeyError
**Location**: `gmail_lm_cleaner.py` in `analyze_email_with_llm` method
**Error**: "An error occurred: "'subject'"

### Root Cause Analysis
The error occurs because the email_data dictionary doesn't have the expected 'subject' key when the LLM prompt template tries to format it. This happens in the organization prompt template formatting.

### Immediate Fix Required
```python
# In analyze_email_with_llm method, add validation before formatting:
def analyze_email_with_llm(self, email_data):
    # Validate email_data has required fields
    required_fields = ['subject', 'sender', 'body', 'date']
    for field in required_fields:
        if field not in email_data:
            return {"action": "KEEP", "reason": f"Missing required field: {field}"}
    
    # Ensure fields are strings and handle None values
    email_data = {
        'subject': str(email_data.get('subject', 'No Subject')),
        'sender': str(email_data.get('sender', 'Unknown Sender')),
        'body': str(email_data.get('body', ''))[:1000],
        'date': str(email_data.get('date', 'Unknown Date'))
    }
```

## 📋 PROJECT OVERVIEW

### Current System Architecture
- **Main Script**: `gmail_lm_cleaner.py` - Core email processing with GUI
- **LLM Integration**: Uses LM Studio (local) and Gemini API (analysis)
- **Email Processing**: Fetches emails, analyzes with LLM, categorizes into folders
- **GUI**: Tkinter-based interface with tabs for main control, settings, and rule management

### Key Components Needing Improvement
1. **Error Handling**: Missing validation in email data processing
2. **UI/UX**: Current Tkinter GUI is functional but not user-friendly
3. **LLM Prompts**: Need better structured prompts for consistent results
4. **Email Categorization**: Current logic is too rigid

## 🎯 PHASE 1: CORE FUNCTIONALITY FIX (Priority)

### 1.1 Fix Email Processing Pipeline

#### A. Enhanced Email Content Extraction
```python
def get_email_content(self, msg_id):
    """Fetch and decode email content with better error handling."""
    try:
        message = self.service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        # Safer header extraction
        headers = message.get('payload', {}).get('headers', [])
        header_dict = {h.get('name', '').lower(): h.get('value', '') for h in headers}
        
        # Extract with defaults
        email_data = {
            'id': msg_id,
            'subject': header_dict.get('subject', 'No Subject'),
            'sender': header_dict.get('from', 'Unknown Sender'),
            'date': header_dict.get('date', 'Unknown Date'),
            'body': self.extract_body(message.get('payload', {}))[:1000],
            'labels': message.get('labelIds', [])
        }
        
        # Validate all fields are strings
        for key in ['subject', 'sender', 'date', 'body']:
            if email_data[key] is None:
                email_data[key] = ''
            email_data[key] = str(email_data[key])
        
        return email_data
        
    except Exception as e:
        self.log(f"Error fetching email {msg_id}: {str(e)}")
        # Return minimal valid structure
        return {
            'id': msg_id,
            'subject': 'Error Loading Email',
            'sender': 'Unknown',
            'date': 'Unknown',
            'body': f'Error: {str(e)}',
            'labels': []
        }
```

#### B. Robust LLM Analysis
```python
def analyze_email_with_llm(self, email_data):
    """Enhanced LLM analysis with better error handling."""
    try:
        # Pre-validation
        if not isinstance(email_data, dict):
            return {"action": "KEEP", "reason": "Invalid email data format"}
        
        # Apply pre-filters first
        sender = email_data.get('sender', '').lower()
        
        if any(never_delete in sender for never_delete in self.settings['never_delete_senders']):
            return {"action": "KEEP", "reason": "Sender in never-delete list"}
        
        if any(auto_delete in sender for auto_delete in self.settings['auto_delete_senders']):
            return {"action": "JUNK", "reason": "Sender in auto-delete list"}
        
        # Check importance
        if self.is_important_email(email_data):
            return {"action": "INBOX", "reason": "Contains important keywords"}
        
        # Prepare safe data for LLM
        safe_email_data = {
            'subject': email_data.get('subject', 'No Subject')[:200],
            'sender': email_data.get('sender', 'Unknown')[:100],
            'body_preview': email_data.get('body', '')[:500],
            'date': email_data.get('date', 'Unknown')[:50]
        }
        
        # Build LLM prompt
        prompt = self.build_categorization_prompt(safe_email_data)
        
        # Call LLM with timeout
        decision = self.call_lm_studio(prompt, timeout=10)
        
        return self.validate_llm_decision(decision)
        
    except Exception as e:
        self.log(f"LLM analysis error: {str(e)}")
        return {"action": "KEEP", "reason": f"Analysis error: {str(e)}"}
```

### 1.2 Improved LLM Prompting System

```python
def build_categorization_prompt(self, email_data):
    """Build a structured prompt for email categorization."""
    prompt = f"""Analyze this email and categorize it. Respond with ONLY valid JSON.

Email Details:
- Subject: {email_data['subject']}
- From: {email_data['sender']}
- Preview: {email_data['body_preview']}

Categories:
- INBOX: Urgent, important, action required
- BILLS: Invoices, statements, financial documents
- SHOPPING: Order confirmations, shipping, promotions
- NEWSLETTERS: Subscriptions, updates, digests
- SOCIAL: Social media notifications
- PERSONAL: Personal correspondence
- JUNK: Spam, unwanted emails

Response format:
{{"action": "CATEGORY_NAME", "reason": "Brief explanation"}}

Analyze and respond:"""
    return prompt

def call_lm_studio(self, prompt, timeout=30):
    """Call LM Studio with proper error handling."""
    try:
        payload = {
            "messages": [
                {"role": "system", "content": "You are an email categorization assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 100,
            "response_format": {"type": "json_object"}  # If supported
        }
        
        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"action": "KEEP", "reason": "Could not parse LLM response"}
        else:
            return {"action": "KEEP", "reason": f"LLM error: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"action": "KEEP", "reason": "LLM timeout"}
    except Exception as e:
        return {"action": "KEEP", "reason": f"LLM error: {str(e)}"}

def validate_llm_decision(self, decision):
    """Validate and sanitize LLM decision."""
    valid_actions = ["INBOX", "BILLS", "SHOPPING", "NEWSLETTERS", "SOCIAL", "PERSONAL", "JUNK", "KEEP"]
    
    if not isinstance(decision, dict):
        return {"action": "KEEP", "reason": "Invalid decision format"}
    
    action = decision.get('action', 'KEEP').upper()
    if action not in valid_actions:
        return {"action": "KEEP", "reason": f"Invalid action: {action}"}
    
    reason = str(decision.get('reason', 'No reason provided'))[:200]
    
    return {"action": action, "reason": reason}
```

## 🎨 PHASE 2: UI/UX IMPROVEMENTS

### 2.1 Modern Web-Based UI Alternative

Create a new `web_ui.py` using Flask and modern web technologies:

```python
from flask import Flask, render_template, jsonify, request
from gmail_lm_cleaner import GmailLMCleaner
import threading
import queue

app = Flask(__name__)
cleaner = None
task_queue = queue.Queue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    global cleaner
    try:
        cleaner = GmailLMCleaner()
        return jsonify({"status": "success", "message": "Connected to Gmail"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/process', methods=['POST'])
def process_emails():
    if not cleaner:
        return jsonify({"status": "error", "message": "Not connected to Gmail"})
    
    # Add task to queue
    task_id = str(uuid.uuid4())
    task_queue.put({
        "id": task_id,
        "type": "process",
        "params": request.json
    })
    
    return jsonify({"status": "queued", "task_id": task_id})

@app.route('/api/status/<task_id>')
def get_status(task_id):
    # Return task status
    pass

# Add WebSocket support for real-time updates
```

### 2.2 Enhanced Tkinter UI (Quick Fix)

```python
class ModernGmailCleanerGUI:
    def __init__(self):
        self.setup_modern_ui()
        
    def setup_modern_ui(self):
        """Create a more modern-looking Tkinter UI."""
        self.root = tk.Tk()
        self.root.title("Gmail Smart Organizer")
        self.root.geometry("1000x700")
        
        # Use ttk styles for modern look
        style = ttk.Style()
        style.theme_use('clam')  # More modern theme
        
        # Custom colors
        bg_color = "#f0f0f0"
        accent_color = "#4285f4"  # Google blue
        
        self.root.configure(bg=bg_color)
        
        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with status
        self.create_header(main_container)
        
        # Quick actions bar
        self.create_quick_actions(main_container)
        
        # Progress section
        self.create_progress_section(main_container)
        
        # Results section with better formatting
        self.create_results_section(main_container)
        
    def create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title = ttk.Label(header_frame, text="Gmail Smart Organizer", 
                         font=('Helvetica', 24, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Connection status with color indicator
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.pack(side=tk.RIGHT)
        
        self.status_indicator = tk.Canvas(self.status_frame, width=12, height=12)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.draw_status_indicator("red")
        
        self.status_label = ttk.Label(self.status_frame, text="Not Connected")
        self.status_label.pack(side=tk.LEFT)
        
    def draw_status_indicator(self, color):
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(2, 2, 10, 10, fill=color, outline="")
```

## 🚀 PHASE 3: TESTING & DEPLOYMENT IMPROVEMENTS

### 3.1 Add Comprehensive Logging

```python
import logging
from datetime import datetime

class EmailProcessingLogger:
    def __init__(self, log_file="email_processing.log"):
        self.logger = logging.getLogger("GmailCleaner")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def log_email_processing(self, email_id, subject, decision, reason):
        self.logger.info(f"Processed: {email_id} | {subject[:50]}... | "
                        f"Decision: {decision} | Reason: {reason}")
```

### 3.2 Add Unit Tests

```python
import unittest
from unittest.mock import Mock, patch

class TestGmailLMCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = GmailLMCleaner()
        
    def test_email_validation(self):
        # Test with valid email data
        valid_email = {
            'id': '123',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'date': '2024-01-01',
            'body': 'Test body'
        }
        result = self.cleaner.validate_email_data(valid_email)
        self.assertTrue(result)
        
    def test_llm_decision_validation(self):
        # Test valid decision
        valid_decision = {"action": "INBOX", "reason": "Important"}
        result = self.cleaner.validate_llm_decision(valid_decision)
        self.assertEqual(result['action'], 'INBOX')
        
        # Test invalid decision
        invalid_decision = {"action": "INVALID", "reason": "Test"}
        result = self.cleaner.validate_llm_decision(invalid_decision)
        self.assertEqual(result['action'], 'KEEP')
```

## 📊 PHASE 4: MONITORING & ANALYTICS

### 4.1 Add Email Processing Analytics

```python
class EmailAnalytics:
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'categories': {},
            'errors': 0,
            'processing_times': []
        }
    
    def record_processing(self, category, processing_time):
        self.stats['total_processed'] += 1
        self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
        self.stats['processing_times'].append(processing_time)
    
    def get_summary(self):
        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times']) if self.stats['processing_times'] else 0
        return {
            'total': self.stats['total_processed'],
            'by_category': self.stats['categories'],
            'error_rate': self.stats['errors'] / self.stats['total_processed'] if self.stats['total_processed'] > 0 else 0,
            'avg_processing_time': avg_time
        }
```

## 🔧 IMPLEMENTATION CHECKLIST

### Immediate Actions (Fix Current Error):
1. [ ] Add email data validation in `get_email_content()`
2. [ ] Add try-catch blocks around prompt formatting
3. [ ] Validate all required fields before LLM analysis
4. [ ] Add default values for missing fields

### Short-term Improvements (1-2 days):
1. [ ] Implement robust error handling throughout
2. [ ] Add comprehensive logging
3. [ ] Improve LLM prompt structure
4. [ ] Add email processing queue
5. [ ] Create basic unit tests

### Medium-term Enhancements (1 week):
1. [ ] Build web-based UI alternative
2. [ ] Add email analytics dashboard
3. [ ] Implement batch processing
4. [ ] Add configuration validation
5. [ ] Create user documentation

### Long-term Goals (Phase 2):
1. [ ] Add scheduling and automation
2. [ ] Implement ML-based learning from user corrections
3. [ ] Add multi-account support
4. [ ] Create mobile app companion
5. [ ] Add email templates and auto-responses

## 🐛 DEBUGGING TIPS

### For the current "'subject'" error:
1. Add print statements before the prompt formatting:
   ```python
   print(f"Email data keys: {email_data.keys()}")
   print(f"Email data: {email_data}")
   ```

2. Check if the email is being fetched correctly:
   ```python
   # In process_inbox, after get_email_content
   if not email_data:
       self.log(f"Failed to get content for email {msg['id']}")
       continue
   ```

3. Validate the prompt template exists:
   ```python
   if not organization_prompt_template:
       self.log("Organization prompt template not found!")
       return {"action": "KEEP", "reason": "Missing prompt template"}
   ```

## 📝 SAMPLE WORKING CONFIGURATION

### settings.json (minimal working config)
```json
{
  "llm_prompts": {
    "lm_studio": {
      "system_message": "You are an email categorization assistant. Always respond with valid JSON.",
      "organization_prompt": "Categorize this email:\nSubject: {subject}\nFrom: {sender}\n\nRespond with JSON: {{\"action\": \"CATEGORY\", \"reason\": \"explanation\"}}"
    }
  },
  "important_keywords": ["urgent", "important", "action required"],
  "important_senders": ["boss@company.com"],
  "never_delete_senders": ["family@gmail.com"],
  "auto_delete_senders": ["spam@spammer.com"],
  "max_emails_per_run": 50,
  "days_back": 7,
  "dry_run": true
}
```

## 🚦 QUICK START COMMANDS

```bash
# Test the fix
python3 -c "from gmail_lm_cleaner import GmailLMCleaner; c = GmailLMCleaner(); print('Connected successfully')"

# Run with debugging
python3 -u gmail_lm_cleaner.py 2>&1 | tee debug.log

# Test email fetching
python3 debug_export.py
```

Remember: Start with fixing the immediate error, then progressively improve the system. The current error is likely due to missing or malformed email data when the LLM prompt tries to format it.