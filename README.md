# Gmail Intelligent Cleaner

A sophisticated Gmail automation system featuring machine learning-like pattern recognition, automated unsubscribe workflows, and intelligent email categorization. Built with a "human-in-the-loop" philosophy for safe, efficient inbox management.

## 🚀 Quick Start

### 1. Simple Startup (Recommended)
```bash
./start.sh
```

### 2. Full Setup for Production Use
```bash
./setup.sh
```

### 3. Simple Shutdown
```bash
./stop.sh
```

The startup script handles all dependencies, environment setup, and launches the application. The setup script prepares the system for autonomous operation with systemd services.

## ✨ Key Features

### 🤖 Intelligence Layer
- **Machine Learning-like Pattern Recognition**: Analyzes user corrections to suggest rule improvements
- **Real-time Analytics Dashboard**: Tracks filter effectiveness and processing statistics
- **Automated Rule Learning**: Detects new email patterns and suggests categorization rules
- **Confidence-based Decision Making**: Low-confidence emails go to REVIEW for human oversight

### 📧 Email Processing
- **Filter-First Strategy**: Applies existing Gmail filters before LLM analysis for efficiency
- **Bulk Backlog Processing**: Handles massive email backlogs (75k+ emails) efficiently
- **Crash-proof Operation**: Comprehensive exception handling prevents silent failures
- **Exponential Backoff**: Resilient API error handling with automatic retries

### ✉️ Unsubscribe Automation
- **HTTP Link Handling**: Automatically opens unsubscribe links in browser
- **Mailto Processing**: Sends automated unsubscribe emails via Gmail API
- **Smart Detection**: Extracts List-Unsubscribe headers from promotional emails
- **Bulk Operations**: Process multiple unsubscribe candidates at once

### 🛡️ Safety & Reliability
- **Dry Run Mode**: Test operations without making changes
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **UI Exception Handling**: Robust error recovery prevents UI freezing
- **State Persistence**: Saves progress and settings automatically

## 📋 Requirements

### Core Dependencies
1. **Python 3.8+**: Modern Python installation required
2. **Gmail API Credentials**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create OAuth client ID for desktop application
   - Download credentials and save as `config/credentials.json`
   - **Required Scopes**:
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/gmail.settings.basic`
     - `https://www.googleapis.com/auth/gmail.send` (for unsubscribe emails)

### Optional Enhancements
3. **LM Studio** (Recommended for best analysis):
   - Download from [LM Studio](https://lmstudio.ai/)
   - Install **Llama-3.1-8B-Instruct** or compatible model
   - Start local server on port 1234

4. **Gemini API** (Alternative LLM):
   - Get API key from [AI Studio](https://aistudio.google.com/app/apikey)
   - Add to `.env` file: `GEMINI_API_KEY=your_key_here`

## 🏛️ System Architecture

### Tiered Importance System
Emails are processed through a safety-first categorization system:

- **INBOX**: Critical emails only (security alerts, personal messages)
- **PRIORITY**: Important but not urgent (GitHub, Zillow, bank statements)
- **Other Categories**: Bills, Shopping, Newsletters, Social, Personal, Junk

### Processing Pipeline
1. **Filter Application**: Existing Gmail filters process emails first
2. **Pattern Recognition**: Learning engine analyzes previous decisions
3. **LLM Analysis**: AI categorizes remaining emails with confidence scoring
4. **Human Review**: Low-confidence decisions go to REVIEW for user input
5. **Learning Loop**: User corrections improve future categorization

### Intelligence Features
- **Pattern Detection**: Identifies new email types needing custom rules
- **Rule Suggestions**: Recommends filter updates based on user behavior
- **Analytics Dashboard**: Real-time visualization of processing effectiveness
- **Automated Optimization**: Continuously improves categorization accuracy

## 🖥️ Configuration

### Basic Settings (`config/settings.json`)
```json
{
  "important_keywords": ["security alert", "account suspended", "verify"],
  "important_senders": ["security@", "alerts@", "admin@"],
  "promotional_keywords": ["sale", "discount", "unsubscribe"],
  "max_emails_per_run": 50,
  "days_back": 7,
  "dry_run": false
}
```

### Environment Variables (`.env`)
```bash
GEMINI_API_KEY=your_api_key_here
LM_STUDIO_URL=http://localhost:1234
LOG_LEVEL=INFO
```

### Priority Patterns (`config/priority_patterns.json`)
Defines high-priority senders and keywords for PRIORITY categorization.

## 🔧 Autonomous Operation

### Systemd Setup (Production)
```bash
# Run the setup script
./setup.sh

# Enable and start services
sudo cp systemd_units/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gmail-autonomy-runner
sudo systemctl start gmail-autonomy-runner
```

### Monitoring
- **Logs**: `logs/` directory with automatic rotation
- **Health Check**: Built-in HTTP health check endpoint
- **State Tracking**: `data/automation_state.json` tracks job execution

## 🎯 Usage Guide

### GUI Operations
1. **Connect**: Establish Gmail API connection
2. **Process Emails**: Run categorization on new emails
3. **Bulk Cleanup**: Process large email backlogs efficiently
4. **Auto-Analyze**: Use AI to suggest new filtering rules
5. **Unsubscribe**: Automated unsubscribe from promotional emails
6. **Analytics**: View processing statistics and effectiveness

### Command Line Tools
- **`autonomous_runner.py`**: Background automation
- **`bulk_processor.py`**: Large-scale email processing
- **`tools/filter_harvester.py`**: Gmail filter management
- **`health_check.py`**: System monitoring endpoint

## 📊 Analytics Dashboard

The built-in analytics provide insights into:
- **Category Distribution**: Email volume by category
- **Filter Effectiveness**: Gmail vs LLM processing efficiency
- **Learning Progress**: Rule suggestion accuracy over time
- **User Satisfaction**: Override rates and confidence metrics
- **Processing Statistics**: Volume, speed, and error rates

## 🔒 Security & Privacy

- **Local Processing**: LLM analysis runs locally (LM Studio)
- **OAuth Authentication**: Secure Gmail API access
- **No Data Upload**: Email content never leaves your machine
- **Audit Logging**: Complete operation history
- **Dry Run Mode**: Test changes safely before applying

## 🛠️ Development

### Architecture Overview
- **`gmail_lm_cleaner.py`**: Main application and GUI
- **`gmail_api_utils.py`**: Gmail API utilities and wrappers
- **`exceptions.py`**: Custom exception hierarchy
- **`log_config.py`**: Centralized logging configuration
- **`tools/`**: Specialized processing utilities

### Adding Features
1. Extend `EmailLearningEngine` for new pattern types
2. Add rule templates in `rules/` directory
3. Update GUI components in `GmailCleanerGUI` class
4. Implement new job types in `autonomous_runner.py`

### Testing
```bash
# Run syntax checks
python3 -m py_compile gmail_lm_cleaner.py

# Test OAuth scopes
python3 test_oauth_scopes.py

# Validate API connections
python3 health_check.py
```

## 📚 Troubleshooting

### Common Issues
1. **Authentication Errors**: Delete `config/token.json` and re-authenticate
2. **LM Studio Connection**: Ensure model is loaded and server is running
3. **Large Backlogs**: Use bulk processing mode for 10k+ emails
4. **UI Freezing**: Check logs for background thread exceptions

### Error Recovery
- Automatic retry with exponential backoff
- UI state restoration after errors
- Comprehensive exception logging
- Graceful degradation when services unavailable

## 🤝 Contributing

1. Follow existing code patterns and style
2. Add comprehensive error handling
3. Update documentation for new features
4. Test with various email volumes and types
5. Maintain backwards compatibility

## 📝 License

This project is intended for personal Gmail automation. Ensure compliance with Gmail API terms of service and your organization's email policies.

---

**Last Updated**: December 2024  
**Version**: Production-ready with intelligence features