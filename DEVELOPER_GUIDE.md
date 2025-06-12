# Developer Guide - Gmail Intelligent Cleaner

This guide provides technical documentation for developers working on the Gmail Intelligent Cleaner system.

## 🏗️ System Architecture

### Core Components

#### 1. Main Application (`gmail_lm_cleaner.py`)
- **GmailLMCleaner**: Core business logic for email processing
- **EmailLearningEngine**: Machine learning-like pattern recognition
- **GmailCleanerGUI**: Tkinter-based user interface
- **Categories**: Email classification system

#### 2. API Layer (`gmail_api_utils.py`)
- **Gmail Service Management**: OAuth authentication and connection handling
- **Label Operations**: Create, modify, and manage Gmail labels
- **Batch Processing**: Efficient bulk operations with retry logic
- **Error Handling**: Wrapped API calls with comprehensive exception handling

#### 3. Filter System (`tools/filter_harvester.py`)
- **Filter Parsing**: Extract and structure existing Gmail filters
- **Action Application**: Apply filter rules to email batches
- **Performance Optimization**: Filter-first processing strategy

#### 4. Exception Hierarchy (`exceptions.py`)
- **GmailAPIError**: Gmail-specific API failures
- **EmailProcessingError**: Email analysis and categorization errors
- **LLMConnectionError**: LLM service communication issues
- **AuthenticationError**: OAuth and credential problems

#### 5. Automation Layer (`autonomous_runner.py`)
- **Job Scheduling**: Cron-based background task execution
- **Health Monitoring**: System status and performance tracking
- **State Persistence**: Maintain automation state across restarts

## 📊 Data Flow

### Email Processing Pipeline

1. **Initialization**
   ```
   User Request → Gmail Connection → Service Authentication
   ```

2. **Email Fetching**
   ```
   Gmail API → Message List → Batch Processing → Content Extraction
   ```

3. **Filter-First Processing**
   ```
   Raw Emails → Existing Filters → Categorized Emails → Remaining for LLM
   ```

4. **LLM Analysis**
   ```
   Email Content → LLM Service → Category Decision → Confidence Score
   ```

5. **Learning Loop**
   ```
   User Feedback → Pattern Analysis → Rule Suggestions → System Improvement
   ```

### Data Storage

#### Configuration Files
- `config/credentials.json`: OAuth credentials (never commit)
- `config/token.json`: Authentication tokens (never commit)
- `config/settings.json`: User preferences and system configuration
- `config/priority_patterns.json`: High-priority email patterns

#### Rule Files
- `rules/CATEGORY.json`: Category-specific filtering rules
- Template structure:
  ```json
  {
    "description": "Category description",
    "senders": ["@domain.com", "specific@email.com"],
    "keywords": ["keyword1", "keyword2"],
    "conditions": {"any": true},
    "actions": {"LABEL_AND_ARCHIVE": true}
  }
  ```

#### Analytics Data
- `logs/categorization_history.json`: Complete decision history
- `data/processing_stats.json`: Performance metrics
- `data/automation_state.json`: Background job state

## 🔧 Key Algorithms

### Pattern Recognition Engine

#### Suggestion Algorithm
The `suggest_rule_updates()` method implements:

1. **Override Pattern Analysis**
   ```python
   def suggest_rule_updates(self):
       # Analyze user corrections
       override_patterns = {}
       for record in self.categorization_history:
           if user_override != llm_action:
               pattern_key = f"{sender}|{llm_action}→{user_override}"
               override_patterns[pattern_key] += 1
       
       # Generate suggestions for patterns with count >= 3
       return suggestions
   ```

2. **Confidence Analysis**
   ```python
   # Track low-confidence decisions
   if confidence < 0.7:
       low_confidence_patterns[sender]['count'] += 1
   ```

#### Pattern Detection
The `detect_new_patterns()` method clusters emails by:
- **Domain clustering**: Group by sender domain
- **Subject clustering**: Group by keyword combinations
- **Frequency analysis**: Identify recurring patterns

### Filter Efficiency Algorithm

The system optimizes processing through:

1. **Filter-First Strategy**: Apply existing Gmail filters before LLM analysis
2. **Batch Processing**: Process emails in configurable batch sizes
3. **Exponential Backoff**: Handle API rate limits gracefully
4. **Pagination Management**: Robust handling of large email sets

## 🛠️ Development Patterns

### Error Handling Strategy

#### Exception Hierarchy
```python
try:
    # Gmail API operation
    result = wrap_gmail_api_call(api_operation)
except GmailAPIError as e:
    e.log_error(logger)
    # Handle Gmail-specific errors
except EmailProcessingError as e:
    # Handle processing-specific errors
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

#### UI Error Handling
```python
def _background_operation(self):
    try:
        # Background work
        self.process_emails()
    except Exception as e:
        # Thread-safe error display
        self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    finally:
        # Always restore UI state
        self.root.after(0, self.restore_ui_state)
```

### Threading Patterns

#### Background Processing
```python
def start_background_task(self):
    # Disable UI elements
    self.button.config(state='disabled')
    
    # Start background thread
    threading.Thread(
        target=self._background_worker,
        daemon=True
    ).start()

def _background_worker(self):
    try:
        # Long-running operation
        self.process_large_dataset()
    finally:
        # Restore UI from main thread
        self.root.after(0, self.restore_ui)
```

### Configuration Management

#### Settings Loading
```python
def load_settings(self):
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
        return self.validate_settings(settings)
    except (FileNotFoundError, json.JSONDecodeError):
        return self.get_default_settings()
```

## 🚀 Adding New Features

### 1. New Email Categories

1. **Create Rule File**: Add `rules/NEWCATEGORY.json`
2. **Update GUI**: Add category to dropdown lists
3. **Modify LLM Prompt**: Include new category in analysis prompt
4. **Test Integration**: Verify end-to-end categorization

### 2. New Learning Patterns

1. **Extend Learning Engine**:
   ```python
   def detect_custom_pattern(self, emails):
       # Custom pattern detection logic
       patterns = []
       for email in emails:
           # Analysis implementation
           pass
       return patterns
   ```

2. **Update Analytics**: Add new pattern types to dashboard

3. **Modify Suggestions**: Include new patterns in rule suggestions

### 3. New Automation Jobs

1. **Define Job Class**:
   ```python
   class CustomJob:
       def __init__(self, config):
           self.schedule = config.get('schedule', '0 */4 * * *')
       
       def check_prerequisites(self):
           # Verify job can run
           return True, None
       
       def execute(self):
           # Job implementation
           pass
   ```

2. **Register in Runner**:
   ```python
   jobs = {
       'custom_job': CustomJob(job_config)
   }
   ```

## 🧪 Testing Strategies

### Unit Testing
```python
def test_email_categorization():
    cleaner = GmailLMCleaner()
    email_data = {
        'subject': 'Security Alert',
        'sender': 'security@bank.com',
        'body': 'Suspicious login detected'
    }
    
    result = cleaner.categorize_email(email_data)
    assert result['action'] == 'INBOX'
    assert result['confidence'] > 0.8
```

### Integration Testing
```python
def test_filter_application():
    # Test filter-first processing
    service = get_test_gmail_service()
    email_ids = ['msg1', 'msg2', 'msg3']
    
    result = apply_existing_filters_to_backlog(service, email_ids)
    assert result['processed_count'] > 0
    assert len(result['remaining_ids']) < len(email_ids)
```

### Performance Testing
```python
def test_bulk_processing():
    # Test large email processing
    start_time = time.time()
    process_email_backlog(query="is:unread", batch_size=100)
    duration = time.time() - start_time
    
    # Verify reasonable performance
    assert duration < 300  # 5 minutes max
```

## 🔍 Debugging Guide

### Common Issues

#### 1. Authentication Problems
```bash
# Check token validity
python3 test_oauth_scopes.py

# Re-authenticate
rm config/token.json
python3 gmail_lm_cleaner.py
```

#### 2. LLM Connection Issues
```bash
# Test LM Studio connection
curl http://localhost:1234/v1/models

# Check Gemini API
python3 -c "import google.generativeai as genai; genai.configure(api_key='KEY'); print('OK')"
```

#### 3. Performance Problems
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Monitor resource usage
htop
```

### Logging Configuration

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Log Analysis
```bash
# Monitor real-time logs
tail -f logs/email_processing.log

# Search for errors
grep -i error logs/*.log

# Analyze performance
grep "Processing time" logs/email_processing.log
```

## 📈 Performance Optimization

### Gmail API Efficiency
- **Batch Requests**: Use batch operations for multiple emails
- **Field Selection**: Request only needed fields (`id`, `threadId`)
- **Rate Limiting**: Implement exponential backoff
- **Caching**: Cache label mappings and filter rules

### Memory Management
- **Streaming**: Process emails in batches, not all at once
- **Cleanup**: Explicitly close file handles and clear large objects
- **Monitoring**: Track memory usage in long-running operations

### UI Responsiveness
- **Threading**: Move all blocking operations to background threads
- **Progress Updates**: Use callbacks for user feedback
- **State Management**: Maintain UI state consistency

## 🔧 Build & Deployment

### Local Development Setup
```bash
# Clone and setup
git clone <repository>
cd gmail-intelligent-cleaner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python3 gmail_lm_cleaner.py
```

### Production Deployment
```bash
# Setup system
./setup.sh

# Configure systemd
sudo cp systemd_units/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gmail-autonomy-runner
sudo systemctl start gmail-autonomy-runner

# Monitor
sudo systemctl status gmail-autonomy-runner
sudo journalctl -u gmail-autonomy-runner -f
```

## 📚 Code Style Guidelines

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Document all public methods with docstrings
- Prefer explicit error handling over generic catches

### Naming Conventions
- Classes: `PascalCase` (e.g., `EmailLearningEngine`)
- Functions: `snake_case` (e.g., `process_email_backlog`)
- Constants: `UPPER_CASE` (e.g., `MAX_RETRIES`)
- Private methods: `_leading_underscore` (e.g., `_apply_filter`)

### Documentation Standards
```python
def process_email_batch(self, emails: List[Dict], dry_run: bool = False) -> Dict[str, Any]:
    """
    Process a batch of emails through the categorization pipeline.
    
    Args:
        emails: List of email dictionaries with id, subject, sender
        dry_run: If True, don't make actual changes
    
    Returns:
        Dictionary with processing statistics and results
        
    Raises:
        EmailProcessingError: If batch processing fails
        GmailAPIError: If Gmail API operations fail
    """
```

## 🔮 Future Improvements

### Planned Features
1. **Advanced ML Integration**: TensorFlow/PyTorch models for classification
2. **Multi-Account Support**: Handle multiple Gmail accounts
3. **Custom Webhooks**: Integration with external services
4. **Mobile Interface**: Web-based mobile UI
5. **Cloud Deployment**: Docker containerization and cloud hosting

### Technical Debt
1. **Test Coverage**: Expand unit and integration test suite
2. **Performance Profiling**: Optimize bottlenecks in large-scale processing
3. **Configuration Validation**: Stricter validation of user settings
4. **Error Recovery**: More sophisticated failure recovery mechanisms

---

This developer guide is a living document. Update it as the system evolves and new patterns emerge.