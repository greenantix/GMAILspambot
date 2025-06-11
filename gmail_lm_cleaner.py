#!/usr/bin/env python3
"""
Gmail Intelligent Cleaner with GUI
This script uses a local LLM via LM Studio to intelligently process and clean your Gmail inbox.
"""

import os
import json
import base64
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import threading
from dotenv import load_dotenv
import google.generativeai as genai
from gmail_api_utils import get_gmail_service, GmailLabelManager
from gemini_config_updater import update_label_schema, update_category_rules, update_label_action_mappings
from tools.filter_harvester import apply_existing_filters_to_backlog
from exceptions import (GmailAPIError, EmailProcessingError, LLMConnectionError, 
                       AuthenticationError, handle_exception_with_logging, wrap_gmail_api_call)
import logging
from logging.handlers import RotatingFileHandler

# If modifying these scopes, delete the token.json file.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]

# Load environment variables
load_dotenv()

# LM Studio configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"

# Gemini configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_ANALYSIS_PROMPT = """Analyze these email subjects and suggest email organization improvements.

EMAIL SUBJECTS:
{subjects_content}

Analyze the patterns and provide suggestions in this EXACT JSON format:

{{
  "categories": {{
    "SHOPPING": {{
      "keywords": ["order", "shipping", "purchase", "cart"],
      "senders": ["@amazon.com", "@ebay.com", "noreply@"],
      "description": "Order confirmations and shopping"
    }},
    "NEWSLETTERS": {{
      "keywords": ["newsletter", "digest", "weekly", "unsubscribe"],
      "senders": ["newsletter@", "news@"],
      "description": "Newsletters and updates"
    }},
    "BILLS": {{
      "keywords": ["invoice", "payment", "bill", "statement"],
      "senders": ["billing@", "accounts@"],
      "description": "Bills and financial documents"
    }}
  }},
  "insights": {{
    "top_senders": ["sender1@example.com", "sender2@example.com"],
    "common_keywords": ["keyword1", "keyword2"]
  }}
}}

Respond with ONLY valid JSON, no other text or explanation."""

# Settings configuration
DEFAULT_SETTINGS = {
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
    "dry_run": False,
    "lm_studio_model": "auto"
}

class EmailLearningEngine:
    def __init__(self, history_file='logs/categorization_history.json'):
        self.history_file = history_file
        self.logger = logging.getLogger("EmailLearningEngine")
        self.categorization_history = self.load_history()

    def load_history(self):
        """Load categorization history from a file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Error loading history file: {e}")
                return []
        return []

    def save_history(self):
        """Save categorization history to a file."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.categorization_history, f, indent=2)
        except IOError as e:
            self.logger.error(f"Error saving history file: {e}")

    def record_categorization(self, email_data, decision, user_override=None):
        """Track all categorization decisions and user corrections."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'email_id': email_data.get('id'),
            'subject': email_data.get('subject'),
            'sender': email_data.get('sender'),
            'llm_action': decision.get('action'),
            'llm_reason': decision.get('reason'),
            'confidence': decision.get('confidence'),
            'user_override': user_override
        }
        self.categorization_history.append(record)
        self.save_history() # Save after each record for persistence

    def suggest_rule_updates(self):
        """Analyze history to suggest new rules or modifications."""
        # Placeholder for future implementation
        self.logger.info("Analyzing history for rule update suggestions...")
        return {}

    def detect_new_patterns(self):
        """Identify emerging email patterns that need new categories."""
        # Placeholder for future implementation
        self.logger.info("Detecting new email patterns...")
        return []

class GmailLMCleaner:
    def __init__(self, credentials_file='config/credentials.json', token_file='config/token.json', settings_file='config/settings.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.settings_file = settings_file
        self.service = None
        self.settings = self.load_settings()
        self.llm_prompts = self.load_llm_prompts() # Load LLM prompts
        self.logger = self.setup_logging()
        self.learning_engine = EmailLearningEngine()
        self.setup_gmail_service()
        
    def load_settings(self):
        """Load settings from file or create default."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults in case new settings were added
                    for key, value in DEFAULT_SETTINGS.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except:
                pass
        return DEFAULT_SETTINGS.copy()
    
    def setup_logging(self):
        """Setup comprehensive logging system."""
        logger = logging.getLogger("GmailCleaner")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler with rotation
        fh = RotatingFileHandler(
            'logs/email_processing.log', 
            maxBytes=10*1024*1024, 
            backupCount=5
        )
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
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def log_email_processing(self, email_id, subject, decision, reason, confidence=None):
        """Log email processing details with confidence scoring."""
        confidence_str = f" | Confidence: {confidence:.2f}" if confidence is not None else ""
        self.logger.info(f"Processed: {email_id} | {subject[:50]}... | "
                        f"Decision: {decision} | Reason: {reason}{confidence_str}")
    
    def load_llm_prompts(self):
        """Load LLM prompts from settings file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get("llm_prompts", {})
            except:
                pass
        return {}

    def save_settings(self):
        """Save current settings to file."""
        # When saving, ensure llm_prompts are also saved if they were modified
        # For this task, we assume llm_prompts are static after initial load
        # and only modify the main settings.
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
        
    def setup_gmail_service(self):
        """Authenticate and create Gmail service instance with auto-reconnection."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                creds = None
                
                if os.path.exists(self.token_file):
                    creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        try:
                            creds.refresh(Request())
                        except Exception as e:
                            if hasattr(self, 'logger'):
                                self.logger.warning(f"Token refresh failed: {e}, re-authenticating...")
                            # Delete expired token and re-authenticate
                            if os.path.exists(self.token_file):
                                os.remove(self.token_file)
                            creds = None
                    
                    if not creds:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, SCOPES)
                        creds = flow.run_local_server(port=0)
                    
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                
                self.service = build('gmail', 'v1', credentials=creds)
                
                # Test the connection
                try:
                    self.service.users().getProfile(userId='me').execute()
                    if hasattr(self, 'logger'):
                        self.logger.info("Gmail connection established successfully")
                    return  # Success, exit retry loop
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"Gmail connection test failed: {e}")
                    raise e
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"Gmail setup attempt {attempt + 1} failed: {e}, retrying...")
                    # Clean up and retry
                    if os.path.exists(self.token_file):
                        os.remove(self.token_file)
                else:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Gmail setup failed after {max_retries} attempts: {e}")
                    raise e

    def ensure_gmail_connection(self):
        """Ensure Gmail connection is active, reconnect if needed."""
        try:
            # Quick test to see if connection is alive
            self.service.users().getProfile(userId='me').execute()
            return True
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Gmail connection lost: {e}, reconnecting...")
            try:
                self.setup_gmail_service()
                return True
            except Exception as reconnect_error:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Reconnection failed: {reconnect_error}")
                return False
    
    def get_email_content(self, msg_id):
        """Fetch and decode email content."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h.get('name') == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h.get('name') == 'Date'), 'Unknown Date')
            
            body = self.extract_body(message.get('payload', {}))
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body[:1000] if body else '',
                'labels': message.get('labelIds', [])
            }
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error fetching email {msg_id}: {e}")
            else:
                print(f"Error fetching email {msg_id}: {e}")
            return None
    
    def extract_body(self, payload):
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def is_critical_email(self, email_data):
        """
        Check if email is INBOX-level critical (interrupts dinner).
        Enhanced with improved patterns and confidence scoring.
        """
        subject = email_data.get('subject', '').lower()
        sender = email_data.get('sender', '').lower()
        body = email_data.get('body', '').lower()
        
        # Ultra-high priority triggers - expanded and categorized
        critical_patterns = {
            'security_threats': [
                'security alert', 'account suspended', 'verify immediately', 'fraud detected',
                'unauthorized access', 'login attempt', 'suspicious activity', 'account compromised',
                'verify your identity', 'account locked', 'unusual activity detected'
            ],
            'payment_urgent': [
                'payment failed', 'card declined', 'payment overdue', 'invoice due',
                'subscription canceled', 'payment required', 'billing issue', 'auto-pay failed'
            ],
            'account_expiry': [
                'account expires', 'urgent action required', 'expires today', 'deadline',
                'expires in', 'renew now', 'service termination', 'final notice'
            ],
            'personal_emergency': [
                'emergency', 'urgent', 'asap', 'immediate action', 'time sensitive',
                'important notice', 'response required', 'confirm receipt'
            ]
        }
        
        # Critical sender patterns (only truly urgent stuff) - enhanced
        critical_senders = [
            # Security and fraud
            'security@', 'fraud@', 'alerts@', 'noreply@paypal.com', 'security-noreply@',
            'account-security@', 'suspicious-activity@', 'identity@',
            # Financial institutions (major ones only)
            'alerts@chase.com', 'alerts@bankofamerica.com', 'notifications@wellsfargo.com',
            'alerts@citi.com', 'security@discover.com', 'fraud@usbank.com',
            # Critical services
            'admin@', 'urgent@', 'critical@', 'emergency@', 'support@stripe.com',
            # Government and legal
            'noreply@irs.gov', '@ssa.gov', 'alerts@usps.com'
        ]
        
        # Confidence scoring
        confidence_score = 0.0
        reasons = []
        
        # Check for critical senders (high confidence)
        for critical_sender in critical_senders:
            if critical_sender in sender:
                confidence_score += 0.8
                reasons.append(f"Critical sender: {critical_sender}")
                break
        
        # Check for critical keywords with context scoring
        full_text = (subject + ' ' + body).lower()
        for category, keywords in critical_patterns.items():
            category_matches = 0
            for keyword in keywords:
                if keyword in full_text:
                    category_matches += 1
                    # Subject matches are more important than body matches
                    if keyword in subject:
                        confidence_score += 0.4
                        reasons.append(f"Critical keyword in subject: {keyword}")
                    else:
                        confidence_score += 0.2
                        reasons.append(f"Critical keyword in body: {keyword}")
            
            # Multiple keywords in same category increase confidence
            if category_matches >= 2:
                confidence_score += 0.3
                reasons.append(f"Multiple {category} indicators")
        
        # Check if it's a personal human (moderate confidence)
        if self.is_personal_human_sender(sender, email_data):
            confidence_score += 0.6
            reasons.append("Personal human sender")
        
        # Time-sensitive patterns boost
        time_sensitive_patterns = ['expires in 24', 'expires today', 'final notice', 'last chance']
        for pattern in time_sensitive_patterns:
            if pattern in full_text:
                confidence_score += 0.3
                reasons.append(f"Time-sensitive: {pattern}")
        
        # Return True if confidence is above threshold
        is_critical = confidence_score >= 0.7
        
        if is_critical and hasattr(self, 'logger'):
            self.logger.debug(f"Critical email detected (confidence: {confidence_score:.2f}): {reasons}")
        
        return is_critical

    def is_priority_email(self, email_data):
        """
        Check if email is PRIORITY-level (morning coffee review).
        Enhanced with configuration file integration and confidence scoring.
        """
        subject = email_data.get('subject', '').lower()
        sender = email_data.get('sender', '').lower()
        body = email_data.get('body', '').lower()
        
        # Load priority patterns from config file
        priority_patterns = self._load_priority_patterns()
        
        # Confidence scoring
        confidence_score = 0.0
        reasons = []
        
        # Check each priority pattern
        for pattern_name, pattern in priority_patterns.items():
            pattern_confidence = 0.0
            
            # Check senders with weighted scoring
            for sender_pattern in pattern.get('senders', []):
                if sender_pattern in sender:
                    # Exact domain match gets higher score
                    if sender_pattern.startswith('@') and sender.endswith(sender_pattern):
                        pattern_confidence += 0.8
                        reasons.append(f"Exact domain match: {sender_pattern}")
                    else:
                        pattern_confidence += 0.6
                        reasons.append(f"Sender pattern match: {sender_pattern}")
                    break
            
            # Check keywords with context scoring
            full_text = (subject + ' ' + body).lower()
            keyword_matches = 0
            for keyword in pattern.get('keywords', []):
                if keyword in full_text:
                    keyword_matches += 1
                    # Subject matches are more important
                    if keyword in subject:
                        pattern_confidence += 0.4
                        reasons.append(f"Priority keyword in subject: {keyword}")
                    else:
                        pattern_confidence += 0.2
                        reasons.append(f"Priority keyword in body: {keyword}")
            
            # Multiple keywords boost confidence
            if keyword_matches >= 2:
                pattern_confidence += 0.3
                reasons.append(f"Multiple {pattern_name} keywords")
            
            # Pattern-specific scoring bonuses
            if pattern_name == 'github' and 'security advisory' in full_text:
                pattern_confidence += 0.5
                reasons.append("GitHub security advisory (high priority)")
            elif pattern_name == 'financial_monitoring' and any(kw in full_text for kw in ['credit score', 'fraud alert', 'large purchase']):
                pattern_confidence += 0.4
                reasons.append("Financial monitoring alert")
            elif pattern_name == 'work_notifications' and 'deadline' in full_text:
                pattern_confidence += 0.4
                reasons.append("Work deadline notification")
            
            confidence_score += pattern_confidence
        
        # Additional priority indicators
        priority_indicators = [
            ('newsletter unsubscribe', 0.3, 'Newsletter management'),
            ('account statement', 0.4, 'Financial statement'),
            ('tax document', 0.6, 'Tax-related document'),
            ('insurance', 0.3, 'Insurance communication'),
            ('medical', 0.5, 'Medical communication'),
            ('appointment', 0.4, 'Appointment notification'),
            ('reservation confirmation', 0.4, 'Travel/booking confirmation'),
            ('tracking', 0.2, 'Package tracking'),
            ('receipt', 0.3, 'Purchase receipt')
        ]
        
        full_text = (subject + ' ' + body).lower()
        for indicator, score, description in priority_indicators:
            if indicator in full_text:
                confidence_score += score
                reasons.append(description)
        
        # Professional email patterns
        if self._is_professional_sender(sender):
            confidence_score += 0.3
            reasons.append("Professional sender domain")
        
        # Return True if confidence is above threshold
        is_priority = confidence_score >= 0.5
        
        if is_priority and hasattr(self, 'logger'):
            self.logger.debug(f"Priority email detected (confidence: {confidence_score:.2f}): {reasons}")
        
        return is_priority

    def _load_priority_patterns(self):
        """Load priority patterns from configuration file with fallback to defaults."""
        try:
            import json
            config_path = 'config/priority_patterns.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('priority_patterns', {})
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Could not load priority patterns config: {e}")
        
        # Fallback to default patterns if config fails
        return {
            'github': {
                'senders': ['notifications@github.com', 'noreply@github.com', '@github.com'],
                'keywords': ['pull request', 'issue', 'release', 'security advisory', 'mentioned you']
            },
            'real_estate': {
                'senders': ['@zillow.com', '@redfin.com', '@realtor.com', '@apartments.com'],
                'keywords': ['property alert', 'price changed', 'new listing', 'market update']
            },
            'financial_monitoring': {
                'senders': ['statements@', 'alerts@chase.com', '@bankofamerica.com', 'credit@'],
                'keywords': ['statement ready', 'credit report', 'account summary', 'balance alert']
            },
            'work_notifications': {
                'senders': ['@slack.com', '@atlassian.com', '@microsoft.com', '@asana.com'],
                'keywords': ['mentioned you', 'assigned', 'due date', 'project update']
            },
            'service_accounts': {
                'senders': ['@amazonaws.com', '@heroku.com', '@digitalocean.com', '@stripe.com'],
                'keywords': ['service update', 'billing', 'usage alert', 'deployment']
            }
        }
    
    def _is_professional_sender(self, sender):
        """Check if sender appears to be from a professional organization."""
        professional_domains = [
            '.edu', '.gov', '.org', '.mil',  # Institutional domains
            'hr@', 'admin@', 'office@', 'management@',  # Professional roles
            'legal@', 'compliance@', 'finance@'
        ]
        
        # Check for corporate email patterns (not free email services)
        free_email_domains = ['@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com', '@aol.com']
        is_not_free_email = not any(domain in sender for domain in free_email_domains)
        
        # Check for professional domain patterns
        has_professional_pattern = any(pattern in sender for pattern in professional_domains)
        
        return is_not_free_email or has_professional_pattern

    def is_personal_human_sender(self, sender, email_data):
        """
        Detect if sender is a real person (not automated).
        Enhanced with better heuristics and scoring.
        """
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        # Automated sender patterns (strong indicators it's NOT human)
        automated_patterns = [
            'noreply@', 'no-reply@', 'donotreply@', 'notifications@', 
            'support@', 'alerts@', 'admin@', 'info@', 'help@', 'service@',
            'automated@', 'system@', 'robot@', 'bot@', 'mailer@',
            'updates@', 'news@', 'marketing@', 'promo@', 'offers@'
        ]
        
        # Personal domain indicators (common personal email services)
        personal_domains = [
            '@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com',
            '@icloud.com', '@aol.com', '@protonmail.com', '@yandex.com'
        ]
        
        # Human-like patterns in content
        human_language_patterns = [
            'hi ', 'hello ', 'hey ', 'dear ', 'thanks', 'thank you',
            'regards', 'best', 'sincerely', 'cheers', 'hope you',
            'how are you', 'let me know', 'please let me', 'i hope',
            'looking forward', 'talk soon', 'speak soon'
        ]
        
        # Automated content patterns
        automated_content_patterns = [
            'unsubscribe', 'this is an automated', 'automatically generated',
            'do not reply', 'please do not reply', 'system generated',
            'no-reply', 'promotional email', 'marketing email'
        ]
        
        confidence_score = 0.0
        
        # Check for automated sender patterns (strong negative indicator)
        if any(pattern in sender for pattern in automated_patterns):
            confidence_score -= 0.8
        
        # Check for personal domains (moderate positive indicator)
        if any(domain in sender for domain in personal_domains):
            confidence_score += 0.4
        
        # Check for human-like language patterns
        full_text = (subject + ' ' + body).lower()
        human_patterns_found = sum(1 for pattern in human_language_patterns if pattern in full_text)
        if human_patterns_found > 0:
            confidence_score += min(0.6, human_patterns_found * 0.2)
        
        # Check for automated content patterns (negative indicator)
        automated_patterns_found = sum(1 for pattern in automated_content_patterns if pattern in full_text)
        if automated_patterns_found > 0:
            confidence_score -= min(0.6, automated_patterns_found * 0.3)
        
        # Check sender name patterns (first.last@domain suggests human)
        sender_local = sender.split('@')[0] if '@' in sender else sender
        if '.' in sender_local and not sender_local.startswith(('no', 'dont', 'do-not')):
            # Could be first.last format
            confidence_score += 0.3
        
        # Very short emails are less likely to be human (unless they're replies)
        text_length = len(subject) + len(body)
        if text_length < 50 and 're:' not in subject and 'fwd:' not in subject:
            confidence_score -= 0.2
        
        # Personal signatures or phone numbers suggest human
        if any(indicator in full_text for indicator in ['phone:', 'mobile:', 'cell:', 'sent from my']):
            confidence_score += 0.4
        
        # Return True if confidence suggests human sender
        is_human = confidence_score > 0.2
        
        if is_human and hasattr(self, 'logger'):
            self.logger.debug(f"Human sender detected (confidence: {confidence_score:.2f}): {sender}")
        
        return is_human

    def is_important_email(self, email_data):
        """Legacy method - now checks for critical OR priority."""
        return self.is_critical_email(email_data) or self.is_priority_email(email_data)
    
    def is_promotional_email(self, email_data):
        """Check if email is promotional."""
        subject_lower = email_data.get('subject', '').lower()
        body_lower = email_data.get('body', '').lower()
        
        promo_count = 0
        for keyword in self.settings['promotional_keywords']:
            if keyword.lower() in subject_lower or keyword.lower() in body_lower:
                return True
        
        return promo_count >= 2  # Require at least 2 promotional keywords
    
    def generate_dynamic_llm_prompt(self):
        """
        Generate LLM prompt based on current system state.
        
        Includes:
        - All existing Gmail labels
        - Category rules from JSON files
        - Recent categorization patterns
        - User corrections/feedback
        """
        try:
            # Get all current labels
            labels = self.get_all_gmail_labels()
            
            # Load all rule files
            rules = self.load_all_category_rules()
            
            # Build dynamic prompt
            categories_info = self.format_categories_with_descriptions(labels, rules)
            learned_patterns = self.get_learned_patterns()
            user_preferences = self.get_user_preferences()
            
            prompt_template = f"""Email categorization assistant. Respond ONLY with valid JSON.

VALID CATEGORIES: INBOX, PRIORITY, BILLS, SHOPPING, NEWSLETTERS, SOCIAL, PERSONAL, JUNK, REVIEW

RULES:
- INBOX: ONLY true security alerts and personal humans (NOT promotional emails claiming to be urgent)
- PRIORITY: Important but not urgent (GitHub, Zillow, bank statements, work notifications)
- BILLS: Receipts, invoices, financial documents
- SHOPPING: Orders, promotions, retail, credit offers, bonus offers
- NEWSLETTERS: News, updates, content
- SOCIAL: Social media, gaming, apps
- PERSONAL: Non-urgent personal messages, scheduling
- JUNK: Spam, irrelevant content, debt collection, aggressive marketing
- REVIEW: Uncertain emails (confidence < 0.7)

FORMAT: {{"action": "CATEGORY", "reason": "brief explanation", "confidence": 0.0-1.0}}

INBOX CRITERIA (be VERY strict):
✅ Real security breaches, login alerts from unknown devices, fraud alerts
✅ Personal emails from humans (not companies)
✅ Two-factor authentication codes, password resets you initiated

❌ NOT INBOX (move to appropriate category):
❌ Credit card offers, bonus offers, rate promotions → SHOPPING
❌ Account warnings from marketing companies → JUNK  
❌ "Important updates" from financial services → NEWSLETTERS
❌ Debt collection notices → JUNK
❌ Marketing emails claiming to be "urgent" → SHOPPING/JUNK

THINK: Is this a REAL emergency that requires immediate attention, or just marketing disguised as urgent?"""
            
            return prompt_template
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error generating dynamic prompt: {str(e)}")
            # Fallback to simple categories if dynamic generation fails
            return self.get_fallback_prompt()

    def get_all_gmail_labels(self):
        """Get all existing Gmail labels."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Filter out system labels and only return user-created ones relevant to categorization
            user_labels = []
            system_labels = ['INBOX', 'SENT', 'DRAFT', 'TRASH', 'SPAM', 'STARRED', 'IMPORTANT', 'UNREAD']
            category_labels = ['BILLS', 'SHOPPING', 'NEWSLETTERS', 'SOCIAL', 'PERSONAL', 'JUNK', 'REVIEW']
            
            for label in labels:
                label_name = label['name']
                if label_name in category_labels or (label_name not in system_labels and not label_name.startswith('Label_')):
                    user_labels.append({
                        'name': label_name,
                        'id': label['id'],
                        'type': label.get('type', 'user')
                    })
            
            return user_labels
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error getting Gmail labels: {str(e)}")
            return []

    def load_all_category_rules(self):
        """Load all category rules from settings and rule files."""
        all_rules = {}
        
        # Load from settings.json
        if hasattr(self, 'settings') and 'category_rules' in self.settings:
            all_rules.update(self.settings['category_rules'])
        
        # Load from individual rule files in rules/ directory
        rules_dir = 'rules'
        if os.path.exists(rules_dir):
            for filename in os.listdir(rules_dir):
                if filename.endswith('.json'):
                    category_name = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(rules_dir, filename), 'r') as f:
                            rule_data = json.load(f)
                            all_rules[category_name] = rule_data
                    except Exception as e:
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"Could not load rule file {filename}: {str(e)}")
        
        return all_rules

    def format_categories_with_descriptions(self, labels, rules):
        """Format categories with their descriptions and rules for the prompt."""
        formatted_categories = []
        
        # Standard categories with descriptions
        standard_categories = {
            'INBOX': 'Critical/urgent only - security alerts, personal humans, true emergencies that interrupt dinner',
            'PRIORITY': 'Important but not urgent - GitHub, Zillow, bank statements, work notifications for morning coffee review',
            'BILLS': 'Receipts, invoices, payment confirmations, bank statements, tax documents',
            'SHOPPING': 'Order confirmations, shipping updates, product launches, store promotions',
            'NEWSLETTERS': 'Newsletters, tech updates, news digests, educational content',
            'SOCIAL': 'Social media notifications, gaming updates, app notifications',
            'PERSONAL': 'Non-urgent personal messages, scheduling, real estate, housing',
            'JUNK': 'Obvious spam, irrelevant promotions, suspicious emails',
            'REVIEW': 'Uncertain emails requiring human review (confidence < 0.7)'
        }
        
        # Add custom labels from Gmail
        for label in labels:
            label_name = label['name']
            if label_name in standard_categories:
                description = standard_categories[label_name]
                
                # Add specific rules if available
                rule_details = ""
                if label_name in rules:
                    rule_data = rules[label_name]
                    keywords = rule_data.get('keywords', [])
                    senders = rule_data.get('senders', [])
                    
                    if keywords:
                        rule_details += f" | Keywords: {', '.join(keywords[:5])}"
                    if senders:
                        rule_details += f" | Senders: {', '.join(senders[:5])}"
                
                formatted_categories.append(f"- {label_name}: {description}{rule_details}")
            else:
                # Custom label - try to infer purpose
                formatted_categories.append(f"- {label_name}: Custom category (adapt based on context)")
        
        return "\n".join(formatted_categories)

    def get_learned_patterns(self):
        """Get learned patterns from email processing history."""
        # This would analyze processing logs and identify patterns
        # For now, return a placeholder that could be expanded
        patterns = [
            "- Emails with 'security@' senders are typically INBOX priority",
            "- Newsletters often arrive on specific days (Mondays/Tuesdays)",
            "- Shopping emails increase during sale periods",
            "- Bill-related emails often contain specific account numbers or amounts"
        ]
        
        # TODO: Implement actual pattern learning from logs
        # This could analyze the logs/email_processing.log file for patterns
        
        return "\n".join(patterns)

    def get_user_preferences(self):
        """Get user-specific preferences and corrections."""
        preferences = []
        
        # Load from settings
        if hasattr(self, 'settings'):
            important_keywords = self.settings.get('important_keywords', [])
            if important_keywords:
                preferences.append(f"- Important keywords: {', '.join(important_keywords[:10])}")
            
            promotional_keywords = self.settings.get('promotional_keywords', [])
            if promotional_keywords:
                preferences.append(f"- Promotional indicators: {', '.join(promotional_keywords[:10])}")
            
            never_delete = self.settings.get('never_delete_senders', [])
            if never_delete:
                preferences.append(f"- Never delete from: {', '.join(never_delete)}")
        
        # TODO: Load user corrections from a feedback log
        # preferences.append("- User corrections: [specific feedback patterns]")
        
        return "\n".join(preferences) if preferences else "- No specific preferences recorded yet"

    def get_fallback_prompt(self):
        """Fallback prompt if dynamic generation fails."""
        return """You are an email categorization assistant. Analyze this email and categorize it.

CATEGORIES:
- INBOX: Urgent/critical emails only
- BILLS: Financial/payment related
- SHOPPING: Commerce/retail related  
- NEWSLETTERS: Information/updates
- SOCIAL: Social/gaming/apps
- PERSONAL: Personal correspondence
- JUNK: Spam/irrelevant
- REVIEW: Uncertain emails

Respond in JSON format:
{"action": "CATEGORY_NAME", "reason": "brief reason", "confidence": 0.0-1.0}"""

    def build_categorization_prompt(self, email_data):
        """Build a dynamic prompt for email categorization using current system state."""
        try:
            # Generate the dynamic base prompt
            base_prompt = self.generate_dynamic_llm_prompt()
            
            # Add specific email data
            email_prompt = f"""
EMAIL TO ANALYZE:
Subject: {email_data['subject']}
From: {email_data['sender']}
Date: {email_data.get('date', 'Unknown')}
Body Preview: {email_data['body_preview']}

Please categorize this email following the rules above."""
            
            return base_prompt + email_prompt
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error building categorization prompt: {str(e)}")
            
            # Fallback to simple prompt
            return f"""Analyze this email:
Subject: {email_data['subject']}
From: {email_data['sender']}
Preview: {email_data['body_preview']}

Respond with JSON: {{"action": "CATEGORY", "reason": "explanation", "confidence": 0.0-1.0}}"""

    def call_lm_studio(self, prompt, timeout=30):
        """Call LM Studio with proper error handling."""
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
            
            # Add model selection - use Llama-3.1-8B
            model_name = self.settings.get('lm_studio_model', 'meta-llama-3.1-8b-instruct')
            if model_name and model_name != 'auto':
                payload['model'] = model_name
            
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
                raise LLMConnectionError(
                    f"LM Studio request failed with status {response.status_code}",
                    service_name="LM Studio",
                    endpoint=LM_STUDIO_URL
                )
                
        except requests.exceptions.Timeout:
            raise LLMConnectionError(
                "LM Studio request timed out",
                service_name="LM Studio", 
                endpoint=LM_STUDIO_URL
            )
        except requests.exceptions.ConnectionError:
            raise LLMConnectionError(
                "Could not connect to LM Studio",
                service_name="LM Studio",
                endpoint=LM_STUDIO_URL
            )
        except LLMConnectionError:
            raise  # Re-raise our custom exception
        except Exception as e:
            raise LLMConnectionError(
                f"LM Studio error: {str(e)}",
                service_name="LM Studio",
                endpoint=LM_STUDIO_URL
            ) from e

    def validate_llm_decision(self, decision):
        """Validate and sanitize LLM decision with confidence scoring."""
        valid_actions = ["INBOX", "PRIORITY", "BILLS", "SHOPPING", "NEWSLETTERS", "SOCIAL", "PERSONAL", "JUNK", "KEEP", "REVIEW"]
        
        if not isinstance(decision, dict):
            return {"action": "KEEP", "reason": "Invalid decision format", "confidence": 0.0}
        
        action = decision.get('action', 'KEEP').upper()
        if action not in valid_actions:
            return {"action": "KEEP", "reason": f"Invalid action: {action}", "confidence": 0.0}
        
        reason = str(decision.get('reason', 'No reason provided'))[:200]
        
        # Handle confidence scoring
        confidence = decision.get('confidence', 0.5)
        try:
            confidence = float(confidence)
            # Ensure confidence is between 0.0 and 1.0
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5  # Default to medium confidence
        
        # Automatic REVIEW routing for low confidence
        if confidence < 0.7 and action not in ['KEEP', 'REVIEW']:
            return {
                "action": "REVIEW", 
                "reason": f"Low confidence ({confidence:.2f}) for {action}: {reason}", 
                "confidence": confidence,
                "original_action": action
            }
        
        return {"action": action, "reason": reason, "confidence": confidence}
    
    def harvest_existing_filters(self):
        """Extract existing Gmail filters for bulk application."""
        try:
            filters = self.service.users().settings().filters().list(userId='me').execute()
            filter_list = filters.get('filter', [])
            
            processed_filters = []
            for gmail_filter in filter_list:
                criteria = gmail_filter.get('criteria', {})
                action = gmail_filter.get('action', {})
                
                # Convert to our format
                filter_rule = {
                    'id': gmail_filter.get('id'),
                    'criteria': criteria,
                    'action': action,
                    'query': self.build_query_from_criteria(criteria)
                }
                processed_filters.append(filter_rule)
            
            return processed_filters
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error harvesting filters: {str(e)}")
            return []

    def build_query_from_criteria(self, criteria):
        """Convert filter criteria to Gmail search query."""
        query_parts = []
        
        if criteria.get('from'):
            query_parts.append(f"from:{criteria['from']}")
        if criteria.get('to'):
            query_parts.append(f"to:{criteria['to']}")
        if criteria.get('subject'):
            query_parts.append(f"subject:\"{criteria['subject']}\"")
        if criteria.get('query'):
            query_parts.append(criteria['query'])
        if criteria.get('hasWords'):
            query_parts.append(criteria['hasWords'])
        
        return ' '.join(query_parts)

    def apply_existing_filters_to_backlog(self, log_callback=None, max_emails_per_filter=1000):
        """Apply existing Gmail filters to unread emails first (before AI processing)."""
        if log_callback:
            log_callback("🔧 Applying existing Gmail filters to backlog...")
        
        try:
            # Get existing filters
            filters = self.harvest_existing_filters()
            if not filters:
                if log_callback:
                    log_callback("   No existing filters found")
                return 0
            
            total_processed = 0
            
            for i, filter_rule in enumerate(filters):
                if not filter_rule.get('query'):
                    continue
                
                try:
                    # Find messages matching this filter
                    query = f"is:unread in:inbox {filter_rule['query']}"
                    
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=max_emails_per_filter
                    ).execute()
                    
                    messages = results.get('messages', [])
                    if not messages:
                        continue
                    
                    if log_callback:
                        log_callback(f"   Filter {i+1}/{len(filters)}: Found {len(messages)} matching emails")
                    
                    # Apply filter actions in batches
                    batch_size = 100
                    for j in range(0, len(messages), batch_size):
                        batch = messages[j:j+batch_size]
                        message_ids = [msg['id'] for msg in batch]
                        
                        # Build modify request
                        modify_request = {}
                        if filter_rule['action'].get('addLabelIds'):
                            modify_request['addLabelIds'] = filter_rule['action']['addLabelIds']
                        if filter_rule['action'].get('removeLabelIds'):
                            modify_request['removeLabelIds'] = filter_rule['action']['removeLabelIds']
                        
                        # Apply batch modification
                        if modify_request:
                            self.service.users().messages().batchModify(
                                userId='me',
                                body={
                                    'ids': message_ids,
                                    **modify_request
                                }
                            ).execute()
                            
                            total_processed += len(batch)
                
                except Exception as e:
                    if log_callback:
                        log_callback(f"   ⚠️ Error applying filter: {str(e)[:100]}")
                    continue
            
            if log_callback:
                log_callback(f"✅ Applied existing filters to {total_processed} emails")
            
            return total_processed
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error in filter application: {str(e)}")
            return 0

    def setup_gmail_filters(self, log_callback=None):
        """Set up Gmail filters based on category rules for automatic processing."""
        if log_callback:
            log_callback("🔧 Setting up Gmail filters for automatic categorization...")
        
        try:
            category_rules = self.settings.get('category_rules', {})
            filters_created = 0
            
            for category, rules in category_rules.items():
                if category == 'INBOX':  # Skip INBOX - we want these to stay
                    continue
                    
                # Create label if it doesn't exist
                label_id = self.create_label_if_not_exists(category)
                if not label_id:
                    if log_callback:
                        log_callback(f"   ⚠️ Skipping {category} - couldn't create label")
                    continue
                
                # Create filters for sender patterns (only specific, non-generic patterns)
                senders = rules.get('senders', [])
                # Filter out overly broad patterns that could cause issues
                specific_senders = [s for s in senders if not s.startswith('@gmail.com') and not s.startswith('@outlook.com') and not s.startswith('@yahoo.com') and len(s) > 3]
                
                for sender_pattern in specific_senders[:5]:  # Limit to 5 per category to avoid spam
                    try:
                        filter_criteria = {
                            'from': sender_pattern
                        }
                        
                        filter_action = {
                            'addLabelIds': [label_id],
                            'removeLabelIds': ['INBOX']  # Remove from inbox for non-inbox categories
                        }
                        
                        # For JUNK category, also mark as spam
                        if category == 'JUNK':
                            filter_action['markAsSpam'] = True
                        
                        filter_body = {
                            'criteria': filter_criteria,
                            'action': filter_action
                        }
                        
                        # Check if filter already exists to avoid duplicates
                        existing_filters = self.service.users().settings().filters().list(userId='me').execute()
                        filter_exists = False
                        
                        for existing_filter in existing_filters.get('filter', []):
                            if existing_filter.get('criteria', {}).get('from') == sender_pattern:
                                filter_exists = True
                                break
                        
                        if not filter_exists:
                            # Create filter with retry logic
                            success = self._create_filter_with_retry(filter_body)
                            if success:
                                filters_created += 1
                                if log_callback:
                                    log_callback(f"   ✅ Created filter: {sender_pattern} → {category}")
                            else:
                                if log_callback and filters_created == 0:  # Only log scope issues once
                                    log_callback(f"   ⚠️ Filter creation failed - check OAuth permissions")
                                    
                    except Exception as e:
                        error_msg = str(e)
                        if '403' in error_msg and 'insufficient' in error_msg.lower():
                            if log_callback and filters_created == 0:  # Only log scope issues once
                                log_callback(f"   ❌ Insufficient permissions for filter creation")
                                log_callback(f"   💡 Re-authenticate with gmail.settings.basic scope")
                            break  # Stop trying if we have scope issues
                        continue
                
                # Create filters for subject keywords (top 3 most specific, avoid generic words)
                keywords = rules.get('keywords', [])
                generic_words = ['update', 'notification', 'message', 'email', 'info', 'news']
                specific_keywords = [kw for kw in keywords if len(kw) > 8 and kw.lower() not in generic_words][:3]  # Longer, more specific keywords
                
                for keyword in specific_keywords:
                    try:
                        filter_criteria = {
                            'subject': keyword
                        }
                        
                        filter_action = {
                            'addLabelIds': [label_id],
                            'removeLabelIds': ['INBOX']
                        }
                        
                        if category == 'JUNK':
                            filter_action['markAsSpam'] = True
                        
                        filter_body = {
                            'criteria': filter_criteria,
                            'action': filter_action
                        }
                        
                        # Check if filter already exists
                        existing_filters = self.service.users().settings().filters().list(userId='me').execute()
                        filter_exists = False
                        
                        for existing_filter in existing_filters.get('filter', []):
                            if existing_filter.get('criteria', {}).get('subject') == keyword:
                                filter_exists = True
                                break
                        
                        if not filter_exists:
                            # Create filter with retry logic
                            success = self._create_filter_with_retry(filter_body)
                            if success:
                                filters_created += 1
                                if log_callback:
                                    log_callback(f"   ✅ Created filter: subject '{keyword}' → {category}")
                    
                    except Exception as e:
                        error_msg = str(e)
                        if '403' in error_msg and 'insufficient' in error_msg.lower():
                            if log_callback and filters_created == 0:  # Only log scope issues once
                                log_callback(f"   ❌ Insufficient permissions for filter creation")
                            break  # Stop trying if we have scope issues
                        continue
            
            if log_callback:
                log_callback(f"✅ Gmail filters setup complete! Created {filters_created} new filters")
                log_callback("   Future emails will be automatically categorized")
                
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error setting up Gmail filters: {str(e)}")
    
    def _create_filter_with_retry(self, filter_body, max_retries=3):
        """Create a Gmail filter with retry logic for rate limiting."""
        import time
        
        for attempt in range(max_retries):
            try:
                self.service.users().settings().filters().create(
                    userId='me',
                    body=filter_body
                ).execute()
                return True
            except Exception as e:
                error_msg = str(e)
                if '403' in error_msg:
                    return False  # Permission issue, don't retry
                elif '429' in error_msg or 'rate' in error_msg.lower():
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                elif attempt < max_retries - 1:
                    time.sleep(1)  # Brief pause for other errors
                    continue
                return False
        return False
    
    def apply_suggested_filters(self, suggested_filters, log_callback=None):
        """Apply Gmail filters suggested by Gemini analysis."""
        if log_callback:
            log_callback("🔧 Creating Gmail filters from Gemini suggestions...")
        
        filters_created = 0
        
        try:
            for category, filters in suggested_filters.items():
                if category == 'INBOX':  # Skip INBOX filters
                    continue
                
                # Create label if it doesn't exist
                label_id = self.create_label_if_not_exists(category)
                if not label_id:
                    if log_callback:
                        log_callback(f"   ⚠️ Skipping {category} - couldn't create label")
                    continue
                
                for filter_spec in filters:
                    try:
                        # Build filter criteria
                        criteria = {}
                        if 'from' in filter_spec:
                            criteria['from'] = filter_spec['from']
                        if 'subject' in filter_spec:
                            criteria['subject'] = filter_spec['subject']
                        
                        # Build filter action based on action type
                        action = {}
                        action_type = filter_spec.get('action', 'label_and_archive')
                        
                        if action_type == 'label_and_archive':
                            action = {
                                'addLabelIds': [label_id],
                                'removeLabelIds': ['INBOX']
                            }
                        elif action_type == 'label_only':
                            action = {
                                'addLabelIds': [label_id]
                            }
                        elif action_type == 'spam':
                            action = {
                                'addLabelIds': [label_id],
                                'removeLabelIds': ['INBOX'],
                                'markAsSpam': True
                            }
                        
                        # Check if filter already exists
                        existing_filters = self.service.users().settings().filters().list(userId='me').execute()
                        filter_exists = False
                        
                        for existing_filter in existing_filters.get('filter', []):
                            existing_criteria = existing_filter.get('criteria', {})
                            if (existing_criteria.get('from') == criteria.get('from') and 
                                existing_criteria.get('subject') == criteria.get('subject')):
                                filter_exists = True
                                break
                        
                        if not filter_exists:
                            filter_body = {
                                'criteria': criteria,
                                'action': action
                            }
                            
                            # Create filter with retry logic
                            success = self._create_filter_with_retry(filter_body)
                            if success:
                                filters_created += 1
                                
                                # Create descriptive log message
                                filter_desc = []
                                if 'from' in criteria:
                                    filter_desc.append(f"from:{criteria['from']}")
                                if 'subject' in criteria:
                                    filter_desc.append(f"subject:{criteria['subject']}")
                                
                                if log_callback:
                                    log_callback(f"   ✅ Created filter: {' AND '.join(filter_desc)} → {category}")
                            else:
                                if log_callback and filters_created == 0:  # Only log scope issues once
                                    log_callback(f"   ❌ Filter creation failed - check OAuth permissions")
                        
                    except Exception as e:
                        error_msg = str(e)
                        if '403' in error_msg and 'insufficient' in error_msg.lower():
                            if log_callback and filters_created == 0:  # Only log scope issues once
                                log_callback(f"   ❌ Insufficient permissions for filter creation")
                            break  # Stop trying if we have scope issues
                        continue
            
            if log_callback:
                log_callback(f"✅ Created {filters_created} Gmail filters from Gemini suggestions")
                if filters_created > 0:
                    log_callback("   Future emails will be automatically categorized!")
                    
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error applying suggested filters: {str(e)}")
    
    def get_available_models(self):
        """Get list of available models from LM Studio."""
        try:
            response = requests.get(LM_STUDIO_MODELS_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['id'] for model in data.get('data', [])]
                return models
            return []
        except requests.exceptions.RequestException:
            return []
    
    def analyze_email_with_llm(self, email_data):
        """Enhanced LLM analysis with better error handling."""
        try:
            # Pre-validation
            if not isinstance(email_data, dict):
                return {"action": "KEEP", "reason": "Invalid email data format"}
            
            # Validate email_data has required fields
            required_fields = ['subject', 'sender', 'body', 'date']
            for field in required_fields:
                if field not in email_data:
                    return {"action": "KEEP", "reason": f"Missing required field: {field}"}
            
            # Pre-filter based on settings
            sender = email_data.get('sender', '').lower()
            
            if any(never_delete in sender for never_delete in self.settings['never_delete_senders']):
                return {"action": "KEEP", "reason": "Sender in never-delete list"}
            
            if any(auto_delete in sender for auto_delete in self.settings['auto_delete_senders']):
                return {"action": "JUNK", "reason": "Sender in auto-delete list"}
            
            # Check for critical emails (INBOX level)
            if self.is_critical_email(email_data):
                return {"action": "INBOX", "reason": "Critical email requiring immediate attention", "confidence": 0.9}
            
            # Check for priority emails (important but not urgent)
            if self.is_priority_email(email_data):
                return {"action": "PRIORITY", "reason": "Important account activity for morning review", "confidence": 0.8}
            
            # Check for promotional content
            if self.is_promotional_email(email_data):
                return {"action": "SHOPPING", "reason": "Promotional email", "confidence": 0.7}
            
            # Prepare safe data for LLM
            safe_email_data = {
                'subject': str(email_data.get('subject', 'No Subject'))[:200],
                'sender': str(email_data.get('sender', 'Unknown'))[:100],
                'body_preview': str(email_data.get('body', ''))[:500],
                'date': str(email_data.get('date', 'Unknown'))[:50]
            }
            
            # Build LLM prompt
            prompt = self.build_categorization_prompt(safe_email_data)
            
            # Call LLM with longer timeout for stability
            try:
                decision = self.call_lm_studio(prompt, timeout=30)
                return self.validate_llm_decision(decision)
            except LLMConnectionError as e:
                e.log_error(self.logger if hasattr(self, 'logger') else logging.getLogger())
                return {"action": "KEEP", "reason": "LLM service unavailable", "confidence": 0.0}
            
        except Exception as e:
            email_id = email_data.get('id', 'unknown')
            email_subject = email_data.get('subject', 'No Subject')
            
            error = EmailProcessingError(
                "Failed to analyze email with LLM",
                email_id=email_id,
                email_subject=email_subject,
                processing_step="llm_analysis"
            )
            error.log_error(self.logger if hasattr(self, 'logger') else logging.getLogger())
            return {"action": "KEEP", "reason": f"Analysis error: {str(e)}", "confidence": 0.0}
    
    def create_label_if_not_exists(self, label_name):
        """Create a Gmail label if it doesn't exist."""
        try:
            # Get existing labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # Create new label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            return created_label['id']
            
        except Exception as e:
            # Check if it's a label conflict error - try to find existing label
            if "Label name exists or conflicts" in str(e):
                # Re-fetch labels to find the existing one
                try:
                    results = self.service.users().labels().list(userId='me').execute()
                    labels = results.get('labels', [])
                    for label in labels:
                        if label['name'] == label_name:
                            if hasattr(self, 'logger'):
                                self.logger.debug(f"Found existing label {label_name}")
                            return label['id']
                except:
                    pass
            
            if hasattr(self, 'logger'):
                self.logger.error(f"Error creating label {label_name}: {e}")
            else:
                print(f"Error creating label {label_name}: {e}")
            return None
 
    def execute_action(self, email_id, action, reason, log_callback=None):
        """Execute the decided action on the email."""
        try:
            
            if action == "JUNK":
                # Move to trash
                self.service.users().messages().trash(
                    userId='me',
                    id=email_id
                ).execute()
                if log_callback:
                    log_callback(f"  🗑️ Moved to trash: {reason}")
                
            elif action == "INBOX":
                # Keep in inbox, add important label
                self.service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'addLabelIds': ['IMPORTANT']}
                ).execute()
                if log_callback:
                    log_callback(f"  📥 Kept in inbox: {reason}")
                
            else:
                # Move to appropriate folder/label
                label_id = self.create_label_if_not_exists(action)
                
                if label_id:
                    # Remove from inbox and add to category label
                    self.service.users().messages().modify(
                        userId='me',
                        id=email_id,
                        body={
                            'removeLabelIds': ['INBOX'],
                            'addLabelIds': [label_id]
                        }
                    ).execute()
                    
                    folder_emoji = {
                        'PRIORITY': '⚡',
                        'BILLS': '💰',
                        'SHOPPING': '🛒',
                        'NEWSLETTERS': '📰',
                        'SOCIAL': '👥',
                        'PERSONAL': '📧',
                        'REVIEW': '🤔'
                    }
                    
                    emoji = folder_emoji.get(action, '📁')
                    
                    if log_callback:
                        if action == 'REVIEW':
                            log_callback(f"  {emoji} Moved to REVIEW (needs human review): {reason}")
                        else:
                            log_callback(f"  {emoji} Moved to {action}: {reason}")
                else:
                    if log_callback:
                        log_callback(f"  ✗ Failed to create label for {action}")
                
        except Exception as e:
            if log_callback:
                log_callback(f"  ✗ Error executing action: {e}")
    
    def process_inbox(self, log_callback=None):
        """Process emails from the inbox in newest to oldest order."""
        if log_callback:
            log_callback(f"🔍 Processing inbox emails (newest first)...")
        
        # Focus on inbox only, newest first - no date restriction unless specified
        if self.settings.get('days_back', 0) > 0:
            date_after = (datetime.now() - timedelta(days=self.settings['days_back'])).strftime('%Y/%m/%d')
            query = f'in:inbox after:{date_after}'
            if log_callback:
                log_callback(f"   Filtering to last {self.settings['days_back']} days")
        else:
            query = 'in:inbox'
            if log_callback:
                log_callback(f"   Processing all inbox emails")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.settings['max_emails_per_run']
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                if log_callback:
                    log_callback('No messages found.')
                return
            
            if log_callback:
                log_callback(f"📧 Found {len(messages)} emails to process\n")
            
            for i, msg in enumerate(messages, 1):
                if log_callback:
                    log_callback(f"[{i}/{len(messages)}] Processing email...")
                
                email_data = self.get_email_content(msg['id'])
                if not email_data:
                    continue
                
                if log_callback:
                    subject_text = email_data.get('subject', 'No Subject')[:60]
                    sender_text = email_data.get('sender', 'Unknown Sender')
                    log_callback(f"  Subject: {subject_text}...")
                    log_callback(f"  From: {sender_text}")
                
                decision = self.analyze_email_with_llm(email_data)
                
                # Log the processing details
                if hasattr(self, 'logger'):
                    self.log_email_processing(
                        email_data['id'],
                        email_data.get('subject', 'No Subject'),
                        decision['action'],
                        decision['reason'],
                        decision.get('confidence')
                    )
                
                self.execute_action(
                    email_data['id'],
                    decision['action'],
                    decision['reason'],
                    log_callback
                )
            
            if log_callback:
                log_callback("\n✅ Email processing complete!")
            
        except Exception as e:
            if log_callback:
                log_callback(f'An error occurred: {e}')
        finally:
            # After processing, suggest rule updates based on the session
            self.learning_engine.suggest_rule_updates()
            self.learning_engine.detect_new_patterns()
    
    def process_email_backlog(self, batch_size=100, older_than_days=0, log_callback=None, progress_callback=None, pause_callback=None):
        """
        Process all unread emails to get to inbox zero.
        
        Features:
        - Process emails in batches to avoid rate limits
        - Show progress with ability to pause/resume
        - Log all actions for review
        - Option to process only emails older than X days
        - Returns processing statistics
        """
        if log_callback:
            log_callback("🚀 Starting bulk unread email cleanup...")
        
        # Build query for unread emails
        query_parts = ['is:unread', 'in:inbox']
        
        if older_than_days > 0:
            date_before = (datetime.now() - timedelta(days=older_than_days)).strftime('%Y/%m/%d')
            query_parts.append(f'before:{date_before}')
            if log_callback:
                log_callback(f"📅 Processing unread emails older than {older_than_days} days")
        else:
            if log_callback:
                log_callback("📧 Processing ALL unread emails")
        
        query = ' '.join(query_parts)
        
        # Initialize statistics
        stats = {
            'total_found': 0,
            'total_processed': 0,
            'by_category': {},
            'errors': 0,
            'batch_count': 0,
            'start_time': datetime.now()
        }
        
        try:
            # Ensure Gmail connection before starting
            if not self.ensure_gmail_connection():
                if log_callback:
                    log_callback("❌ Failed to establish Gmail connection")
                return stats
            
            # Get total count first for accurate progress
            if log_callback:
                log_callback(f"🔍 Getting total unread email count...")
            
            total_messages = 0
            try:
                # Get the number of unread messages in the inbox.
                # This is a reliable count for the most common use case.
                # If the query is more complex (e.g., with 'older_than'), this count is an approximation.
                inbox_label_data = self.service.users().labels().get(userId='me', id='INBOX').execute()
                total_messages = inbox_label_data.get('messagesUnread', 0)
                
                stats['total_found'] = total_messages
                if log_callback:
                    log_callback(f"📊 Found {total_messages} unread emails in the inbox.")
                if progress_callback:
                    progress_callback(0, total_messages) # Update progress bar immediately
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ Could not get unread count from INBOX label: {e}. Will count as emails are fetched.")
                stats['total_found'] = 0 # We'll count as we go

            # Efficient batch processing: fetch large chunks, process in smaller batches
            next_page_token = None
            processed_count = 0
            fetch_size = min(500, batch_size * 10)  # Fetch larger chunks efficiently
            
            if log_callback:
                log_callback(f"🚀 Processing 75k+ emails efficiently!")
                log_callback(f"📊 Fetching {fetch_size} emails per API call, processing {batch_size} at a time")
            
            while True:
                try:
                    # Fetch large chunk of email IDs efficiently
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=fetch_size,  # Fetch efficiently
                        pageToken=next_page_token
                    ).execute()
                except Exception as e:
                    if log_callback:
                        log_callback(f"❌ Error fetching email batch: {e}")
                    stats['errors'] += 1
                    break

                messages = results.get('messages', [])
                if not messages:
                    if log_callback:
                        log_callback("✅ No more emails to process")
                    break
                
                if log_callback:
                    log_callback(f"📥 Fetched {len(messages)} emails, applying existing filters first...")
                
                # Apply existing Gmail filters before LLM processing
                email_ids = [msg['id'] for msg in messages]
                filter_result = apply_existing_filters_to_backlog(
                    self.service, 
                    email_ids,
                    progress_callback=lambda msg, prog: log_callback(f"🔧 {msg}") if log_callback else None
                )
                
                # Update statistics with filter results
                filter_processed = filter_result['processed_count']
                remaining_ids = filter_result['remaining_ids']
                filter_stats = filter_result['filter_stats']
                
                if log_callback:
                    log_callback(f"🔧 Filters processed {filter_processed} emails, {len(remaining_ids)} need LLM analysis")
                    if filter_stats:
                        for filter_id, count in filter_stats.items():
                            log_callback(f"  📋 Filter {filter_id}: {count} emails")
                
                # Create filtered message list for LLM processing
                messages_for_llm = [msg for msg in messages if msg['id'] in remaining_ids]
                
                # Update processed count with filter results
                processed_count += filter_processed
                stats['total_processed'] += filter_processed
                stats['by_category']['FILTERED'] = stats['by_category'].get('FILTERED', 0) + filter_processed
                
                if log_callback:
                    log_callback(f"📊 Processing {len(messages_for_llm)} emails with LLM (after filter pre-processing)")
                
                # Process remaining emails in smaller batches
                for i in range(0, len(messages_for_llm), batch_size):
                    sub_batch = messages_for_llm[i:i+batch_size]
                    stats['batch_count'] += 1
                    
                    if log_callback:
                        log_callback(f"\n📦 Batch {stats['batch_count']}: Processing {len(sub_batch)} emails")
                    
                    # Process each email in this sub-batch
                    for msg in sub_batch:
                        try:
                            # Check for pause
                            if pause_callback and pause_callback():
                                if log_callback:
                                    log_callback("⏸️ Processing paused by user")
                                return stats
                            
                            processed_count += 1
                            
                            # Update progress 
                            if progress_callback:
                                progress_callback(processed_count, total_messages if total_messages > 0 else processed_count)
                            
                            # Get email content
                            email_data = self.get_email_content(msg['id'])
                            if not email_data:
                                stats['errors'] += 1
                                continue
                            
                            # Log email being processed (every 10th to avoid spam)
                            if log_callback and processed_count % 10 == 0:
                                subject_preview = email_data.get('subject', 'No Subject')[:50]
                                log_callback(f"  📧 [{processed_count}] {subject_preview}...")
                            
                            # Analyze email
                            decision = self.analyze_email_with_llm(email_data)
                            action = decision['action']
                            reason = decision['reason']
                            
                            # Update statistics
                            stats['by_category'][action] = stats['by_category'].get(action, 0) + 1
                            stats['total_processed'] += 1
                            
                            # Log decision
                            self.log_email_processing(
                                email_data['id'],
                                email_data.get('subject', 'No Subject'),
                                action,
                                reason,
                                decision.get('confidence')
                            )
                            
                            # Execute action
                            self.execute_action(
                                email_data['id'],
                                action,
                                reason,
                                None  # Skip detailed action logging to speed up
                            )
                            
                        except Exception as e:
                            stats['errors'] += 1
                            if log_callback and processed_count % 50 == 0:  # Only log errors occasionally
                                log_callback(f"    ❌ Error processing email: {str(e)[:100]}")
                            continue
                    
                    # Sub-batch complete
                    if log_callback:
                        percentage = (processed_count / total_messages * 100) if total_messages > 0 else 100
                        log_callback(f"✅ Batch {stats['batch_count']}: {processed_count} total processed ({percentage:.1f}%)")
                
                # Update final stats for this chunk
                stats['total_found'] = processed_count
                
                # Check for next page
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    if log_callback:
                        log_callback("🎯 All emails fetched and processed!")
                    break
                
                # Very brief pause to avoid rate limits
                import time
                time.sleep(0.5)
            
            # Final statistics
            elapsed = datetime.now() - stats['start_time']
            stats['duration'] = elapsed.total_seconds()
            
            if log_callback:
                log_callback(f"\n🎉 Bulk processing complete!")
                log_callback(f"📊 Processing Summary:")
                log_callback(f"   Total found: {stats['total_found']}")
                log_callback(f"   Successfully processed: {stats['total_processed']}")
                log_callback(f"   Errors: {stats['errors']}")
                log_callback(f"   Duration: {elapsed}")
                log_callback(f"   Rate: {stats['total_processed']/stats['duration']:.1f} emails/second")
                
                log_callback(f"\n📈 Category Breakdown:")
                for category, count in stats['by_category'].items():
                    percentage = (count / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0
                    log_callback(f"   {category}: {count} ({percentage:.1f}%)")
            
            return stats
            
        except Exception as e:
            stats['errors'] += 1
            if log_callback:
                log_callback(f'❌ Bulk processing error: {e}')
            self.logger.exception("Bulk processing error")
            return stats
        finally:
            # After processing, suggest rule updates based on the session
            self.learning_engine.suggest_rule_updates()
            self.learning_engine.detect_new_patterns()
    
    def export_subjects(self, max_emails=1000, days_back=30, output_file='email_subjects.txt'):
        """Export email subjects for analysis."""
        print(f"🔍 Exporting up to {max_emails} email subjects from the last {days_back} days...")
        
        # Use absolute path if not already absolute
        if not os.path.isabs(output_file):
            output_file = os.path.abspath(output_file)
        
        print(f"📁 Output file: {output_file}")
        
        date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query = f'in:inbox after:{date_after}'
        print(f"📧 Query: {query}")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_emails
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print('No messages found.')
                return output_file # Return output_file even if no messages
            
            print(f"📧 Found {len(messages)} emails to export")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Email Subjects Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total emails: {len(messages)}\n")
                f.write("=" * 80 + "\n\n")
                f.flush()  # Force write to disk
                
                print(f"📝 Writing to file: {output_file}")
                
                for i, msg in enumerate(messages, 1):
                    try:
                        message = self.service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='metadata',
                            metadataHeaders=['Subject', 'From', 'Date']
                        ).execute()
                        
                        headers = message['payload']['headers']
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                        
                        f.write(f"{i:4d}. Subject: {subject}\n")
                        f.write(f"      From: {sender}\n")
                        f.write(f"      Date: {date}\n\n")
                        f.flush()  # Flush after each write
                        
                        if i % 100 == 0:
                            print(f"  Processed {i}/{len(messages)} emails...")
                            
                    except Exception as e:
                        print(f"  Error processing email {i}: {e}")
                        continue
            
            print(f"✅ Export complete! Saved to {output_file}")
            print(f"\nYou can now upload this file to Gemini and ask:")
            print(f"'Analyze these {len(messages)} email subjects and create better filtering rules'")
            print(f"'Categorize them into: INBOX (urgent only), BILLS, SHOPPING, NEWSLETTERS, SOCIAL, PERSONAL, JUNK'")
            return output_file # Return the path to the exported file
            
        except Exception as e:
            print(f'Export error: {e}')
            return None # Return None on error
    
    def test_gemini_connection(self):
        """Test if Gemini API key is working with a simple request."""
        try:
            if not GEMINI_API_KEY:
                return False
            
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Create model (using latest Gemini model)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with a simple request
            response = model.generate_content("Test connection - respond with OK")
            
            # Check if we got a valid response
            if response and response.text:
                return True
            else:
                return False
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Gemini connection test failed: {str(e)}")
            return False

    def analyze_with_gemini(self, subjects_file='email_subjects.txt'):
        """Use Gemini to analyze email subjects and generate filtering rules."""
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not found in .env file")
            return None
        
        if not os.path.exists(subjects_file):
            print(f"❌ Subjects file {subjects_file} not found")
            return None
        
        print("🤖 Analyzing email subjects with Gemini...")
        
        try:
            # Read the subjects file
            with open(subjects_file, 'r', encoding='utf-8') as f:
                subjects_content = f.read()
            
            # Create the analysis prompt
            prompt = GEMINI_ANALYSIS_PROMPT.format(subjects_content=subjects_content)
            
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Generate response
            response = model.generate_content(prompt)
            
            # Parse JSON response - handle potential markdown code blocks
            try:
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                elif response_text.startswith('```'):
                    response_text = response_text[3:]   # Remove ```
                
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove trailing ```
                
                response_text = response_text.strip()
                
                rules = json.loads(response_text)
                print("✅ Gemini analysis complete!")
                return rules
            except json.JSONDecodeError:
                print("❌ Failed to parse Gemini response as JSON")
                print("Raw response:", response.text[:500] + "...")
                return None
                
        except Exception as e:
            print(f"❌ Gemini analysis error: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Gemini analysis failed: {str(e)}")
            return None
    
    def apply_gemini_rules(self, rules, log_callback=None):
        """Apply filtering rules generated by Gemini with integrated config updater logic."""
        if not rules:
            if log_callback:
                log_callback("❌ No rules to apply")
            else:
                print("❌ No rules to apply")
            return
        
        if log_callback:
            log_callback("🔧 Applying Gemini-generated filtering rules...")
        else:
            print("🔧 Applying Gemini-generated filtering rules...")
        
        try:
            # Import logger for gemini_config_updater functions
            from log_config import get_logger
            logger = get_logger(__name__)
            
            # Update label schema if specified
            if 'label_schema' in rules:
                try:
                    # Use existing authenticated service instead of creating new one
                    gmail_label_manager = GmailLabelManager(self.service)
                    gmail_label_manager.refresh_label_cache()
                    update_label_schema(gmail_label_manager, rules['label_schema'], logger)
                    if log_callback:
                        log_callback("✅ Label schema updated")
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Label schema update failed: {e}")
                    logger.error(f"Label schema update failed: {e}")
            
            # Update category rules
            if 'category_rules' in rules:
                try:
                    rules_dir = "rules"
                    update_category_rules(rules['category_rules'], rules_dir, logger)
                    if log_callback:
                        log_callback("✅ Category rules updated")
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Category rules update failed: {e}")
                    logger.error(f"Category rules update failed: {e}")
            
            # Update important keywords and senders
            if 'important_keywords' in rules:
                self.settings['important_keywords'] = rules['important_keywords']
            
            if 'important_senders' in rules:
                self.settings['important_senders'] = rules['important_senders']
            
            # Store category rules for advanced filtering in settings
            if 'category_rules' in rules:
                self.settings['category_rules'] = rules['category_rules']
            
            # Update auto-delete list
            if 'auto_delete_senders' in rules:
                self.settings['auto_delete_senders'] = rules['auto_delete_senders']
            
            # Update label action mappings in settings
            if 'category_rules' in rules:
                try:
                    updated = update_label_action_mappings(self.settings, rules['category_rules'], logger)
                    if updated and log_callback:
                        log_callback("✅ Label action mappings updated")
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Label action mappings update failed: {e}")
                    logger.error(f"Label action mappings update failed: {e}")
            
            # Apply suggested Gmail filters from Gemini
            if 'suggested_gmail_filters' in rules:
                try:
                    self.apply_suggested_filters(rules['suggested_gmail_filters'], log_callback)
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Gmail filters creation failed: {e}")
                    logger.error(f"Gmail filters creation failed: {e}")
            
            # Save updated settings
            self.save_settings()
            
            if log_callback:
                log_callback("✅ Filtering rules updated and saved!")
            else:
                print("✅ Filtering rules updated and saved!")
                
        except Exception as e:
            error_msg = f"❌ Error applying Gemini rules: {e}"
            if log_callback:
                log_callback(error_msg)
            else:
                print(error_msg)
            raise
    
    def export_and_analyze(self, max_emails=1000, days_back=30):
        """Export subjects and automatically analyze with Gemini."""
        print("🚀 Starting automatic email analysis...")
        
        # Export subjects
        self.export_subjects(max_emails, days_back)
        
        # Analyze with Gemini
        rules = self.analyze_with_gemini()
        
        if rules:
            # Apply the rules
            self.apply_gemini_rules(rules)
            print("\n🎉 Automatic analysis complete!")
            print("Your email filtering rules have been updated based on Gemini's analysis.")
        else:
            print("\n⚠️ Analysis failed, but subjects have been exported to email_subjects.txt")
            print("You can manually upload this file to Gemini for analysis.")
            
    def analyze_unsubscribe_candidates(self, log_callback=None):
        """
        Identify emails that user never reads.
        
        Criteria:
        - Never opened (using Gmail API read status)
        - High frequency + low engagement
        """
        if log_callback:
            log_callback("🕵️ Analyzing for unsubscribe candidates...")

        candidates = {}
        try:
            # Query for unread promotional-looking emails
            query = "is:unread category:promotions"
            results = self.service.users().messages().list(userId='me', q=query, maxResults=500).execute()
            messages = results.get('messages', [])

            if log_callback:
                log_callback(f"Found {len(messages)} unread promotional emails to analyze.")

            for msg in messages:
                email_data = self.get_email_content(msg['id'])
                if email_data:
                    sender = email_data['sender']
                    if sender in candidates:
                        candidates[sender]['count'] += 1
                    else:
                        candidates[sender] = {'count': 1, 'example_subject': email_data['subject']}
            
            # Filter for high-frequency senders
            unsubscribe_list = []
            for sender, data in candidates.items():
                if data['count'] > 5: # Arbitrary threshold for "high frequency"
                    unsubscribe_list.append(f"Sender: {sender} (unread count: {data['count']})")
            
            if log_callback:
                log_callback(f"Found {len(unsubscribe_list)} potential unsubscribe candidates.")
            
            return unsubscribe_list

        except Exception as e:
            if log_callback:
                log_callback(f"Error analyzing unsubscribe candidates: {e}")
            return []
            
    def auto_evolve_system(self, log_callback=None):
        """
        Run the auto-evolution process to improve filtering rules over time.
        """
        if log_callback:
            log_callback("🤖 Starting auto-evolution process...")

        # 1. Analyze categorization history for patterns and suggest updates
        suggested_updates = self.learning_engine.suggest_rule_updates()
        if suggested_updates:
            if log_callback:
                log_callback(f"   🔍 Found {len(suggested_updates)} potential rule updates.")
            # In a real implementation, you'd present these to the user for confirmation
            # For now, we'll just log them.
            self.logger.info(f"Suggested rule updates: {json.dumps(suggested_updates, indent=2)}")

        # 2. Detect new, uncategorized patterns
        new_patterns = self.learning_engine.detect_new_patterns()
        if new_patterns:
            if log_callback:
                log_callback(f"   ✨ Detected {len(new_patterns)} new email patterns.")
            self.logger.info(f"Detected new patterns: {new_patterns}")

        # 3. Monitor filter effectiveness (placeholder)
        if log_callback:
            log_callback("   📊 Monitoring filter effectiveness (placeholder)...")

        # 4. Suggest filter adjustments (placeholder)
        if log_callback:
            log_callback("   🔧 Suggesting filter adjustments (placeholder)...")

        if log_callback:
            log_callback("✅ Auto-evolution process complete.")
 
class GmailCleanerGUI:
    def __init__(self):
        self.cleaner = None
        self.setup_ui()
        
        # Auto-connect to Gmail on startup
        self.root.after(1000, self.auto_connect_gmail)  # Connect after UI loads
    
    def auto_connect_gmail(self):
        """Automatically connect to Gmail on startup."""
        try:
            self.log("🚀 Auto-connecting to Gmail...")
            self.connect_gmail()
        except Exception as e:
            self.log(f"⚠️ Auto-connect failed: {e}")
            self.log("   You can manually connect using the 'Connect to Gmail' button")
        
    def setup_ui(self):
        """Create the GUI interface."""
        self.root = tk.Tk()
        self.root.title("Gmail Intelligent Cleaner")
        self.root.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Main")
        
        # Backlog Cleanup tab
        backlog_frame = ttk.Frame(notebook)
        notebook.add(backlog_frame, text="Backlog Cleanup")
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Rule & Label Management tab
        management_frame = ttk.Frame(notebook)
        notebook.add(management_frame, text="Rule & Label Management")
        
        # Analytics tab
        analytics_frame = ttk.Frame(notebook)
        notebook.add(analytics_frame, text="Analytics")
        
        # Unsubscribe tab
        unsubscribe_frame = ttk.Frame(notebook)
        notebook.add(unsubscribe_frame, text="Unsubscribe")
        
        self.setup_main_tab(main_frame)
        self.setup_backlog_tab(backlog_frame)
        self.setup_settings_tab(settings_frame)
        self.setup_management_tab(management_frame)
        self.setup_analytics_tab(analytics_frame)
        self.setup_unsubscribe_tab(unsubscribe_frame)
        
    def setup_main_tab(self, parent):
        """Setup the main control tab."""
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Not connected to Gmail")
        self.status_label.pack(anchor=tk.W)
        
        # Control frame
        control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Connect to Gmail", command=self.connect_gmail).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Setup Gmail Filters", command=self.setup_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Process Emails", command=self.process_emails).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Export Subjects", command=self.export_subjects).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Auto-Analyze with Gemini", command=self.auto_analyze).pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Dry Run (don't actually modify emails)",
                       variable=self.dry_run_var).pack(anchor=tk.W)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_backlog_tab(self, parent):
        """Setup the backlog cleanup tab."""
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Backlog Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.backlog_status_label = ttk.Label(status_frame, text="Ready to process unread emails")
        self.backlog_status_label.pack(anchor=tk.W)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(parent, text="Processing Options", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Batch size
        batch_frame = ttk.Frame(config_frame)
        batch_frame.pack(fill=tk.X, pady=2)
        ttk.Label(batch_frame, text="Batch size:").pack(side=tk.LEFT)
        self.batch_size_var = tk.StringVar(value="50")
        batch_spinbox = ttk.Spinbox(batch_frame, from_=10, to=500, width=10, textvariable=self.batch_size_var)
        batch_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(batch_frame, text="emails per batch").pack(side=tk.LEFT, padx=5)
        
        # Age filter
        age_frame = ttk.Frame(config_frame)
        age_frame.pack(fill=tk.X, pady=2)
        ttk.Label(age_frame, text="Process emails older than:").pack(side=tk.LEFT)
        self.older_than_var = tk.StringVar(value="0")
        age_spinbox = ttk.Spinbox(age_frame, from_=0, to=365, width=10, textvariable=self.older_than_var)
        age_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(age_frame, text="days (0 = all unread)").pack(side=tk.LEFT, padx=5)
        
        # Processing mode
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill=tk.X, pady=2)
        ttk.Label(mode_frame, text="Processing mode:").pack(side=tk.LEFT)
        self.processing_mode_var = tk.StringVar(value="hybrid")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.processing_mode_var, 
                                 values=["filters_only", "hybrid", "ai_only"], width=15, state="readonly")
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # Mode descriptions
        mode_desc_frame = ttk.Frame(config_frame)
        mode_desc_frame.pack(fill=tk.X, pady=2)
        mode_descriptions = {
            "filters_only": "Apply existing Gmail filters only (fastest)",
            "hybrid": "Apply filters first, then AI for remaining emails (recommended)", 
            "ai_only": "Use AI for all emails (most thorough)"
        }
        self.mode_desc_label = ttk.Label(mode_desc_frame, text=mode_descriptions["hybrid"], foreground="blue")
        self.mode_desc_label.pack(anchor=tk.W, padx=20)
        
        def update_mode_description(*args):
            mode = self.processing_mode_var.get()
            self.mode_desc_label.config(text=mode_descriptions.get(mode, ""))
        
        self.processing_mode_var.trace('w', update_mode_description)
        
        # Dry run option
        self.backlog_dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="Dry Run (preview actions without executing)", 
                       variable=self.backlog_dry_run_var).pack(anchor=tk.W, pady=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_backlog_button = ttk.Button(button_frame, text="Start Cleanup", command=self.start_backlog_cleanup)
        self.start_backlog_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_backlog_button = ttk.Button(button_frame, text="Pause", command=self.pause_backlog_cleanup, state=tk.DISABLED)
        self.pause_backlog_button.pack(side=tk.LEFT, padx=5)
        
        self.resume_backlog_button = ttk.Button(button_frame, text="Resume", command=self.resume_backlog_cleanup, state=tk.DISABLED)
        self.resume_backlog_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_backlog_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_backlog_cleanup, state=tk.DISABLED)
        self.cancel_backlog_button.pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress bar
        self.backlog_progress_var = tk.DoubleVar()
        self.backlog_progress_bar = ttk.Progressbar(progress_frame, variable=self.backlog_progress_var, maximum=100)
        self.backlog_progress_bar.pack(fill=tk.X, pady=2)
        
        # Progress labels
        self.backlog_progress_label = ttk.Label(progress_frame, text="0 / 0 emails processed (0%)")
        self.backlog_progress_label.pack(anchor=tk.W, pady=2)
        
        self.backlog_rate_label = ttk.Label(progress_frame, text="Processing rate: 0 emails/sec")
        self.backlog_rate_label.pack(anchor=tk.W, pady=2)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a frame with columns for category stats
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log frame for backlog processing
        backlog_log_frame = ttk.LabelFrame(parent, text="Processing Log", padding=10)
        backlog_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.backlog_log_text = scrolledtext.ScrolledText(backlog_log_frame, height=10)
        self.backlog_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Initialize processing state
        self.processing_paused = False
        self.processing_cancelled = False
        self.current_stats = None
        
    def setup_settings_tab(self, parent):
        """Setup the settings configuration tab."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Important Keywords
        keywords_frame = ttk.LabelFrame(scrollable_frame, text="Important Keywords", padding=10)
        keywords_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(keywords_frame, text="Emails containing these keywords will always be kept:").pack(anchor=tk.W)
        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=5)
        self.keywords_text.pack(fill=tk.X, pady=5)
        
        # Important Senders
        senders_frame = ttk.LabelFrame(scrollable_frame, text="Important Sender Patterns", padding=10)
        senders_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(senders_frame, text="Emails from senders matching these patterns will be kept:").pack(anchor=tk.W)
        self.senders_text = scrolledtext.ScrolledText(senders_frame, height=3)
        self.senders_text.pack(fill=tk.X, pady=5)
        
        # Never Delete
        never_delete_frame = ttk.LabelFrame(scrollable_frame, text="Never Delete Senders", padding=10)
        never_delete_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(never_delete_frame, text="Never delete emails from these exact senders:").pack(anchor=tk.W)
        self.never_delete_text = scrolledtext.ScrolledText(never_delete_frame, height=3)
        self.never_delete_text.pack(fill=tk.X, pady=5)
        
        # Processing Options
        proc_frame = ttk.LabelFrame(scrollable_frame, text="Processing Options", padding=10)
        proc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(proc_frame, text="Days back to process:").pack(anchor=tk.W)
        self.days_var = tk.StringVar(value="7")
        ttk.Entry(proc_frame, textvariable=self.days_var, width=10).pack(anchor=tk.W, pady=2)
        
        ttk.Label(proc_frame, text="Max emails per run:").pack(anchor=tk.W)
        self.max_emails_var = tk.StringVar(value="50")
        ttk.Entry(proc_frame, textvariable=self.max_emails_var, width=10).pack(anchor=tk.W, pady=2)
        
        # LM Studio Model Selection
        model_frame = ttk.Frame(proc_frame)
        model_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model_frame, text="LM Studio Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="auto")
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly", width=20)
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(model_frame, text="Refresh Models", command=self.refresh_models).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Load Settings", command=self.load_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT, padx=5)
        
        # OAuth Management Section
        oauth_frame = ttk.LabelFrame(scrollable_frame, text="OAuth & Authentication", padding=10)
        oauth_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(oauth_frame, text="Re-authenticate with Gmail if you've updated OAuth restrictions:").pack(anchor=tk.W)
        oauth_button_frame = ttk.Frame(oauth_frame)
        oauth_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(oauth_button_frame, text="🔄 Re-login to Gmail", command=self.relogin_gmail).pack(side=tk.LEFT, padx=5)
        ttk.Button(oauth_button_frame, text="🔧 Reset OAuth Token", command=self.reset_oauth_token).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_management_tab(self, parent):
        """Setup the Rule & Label Management tab."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Label Action Mappings Section
        mappings_frame = ttk.LabelFrame(scrollable_frame, text="Label Action Mappings", padding=10)
        mappings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(mappings_frame, text="Configure what happens to emails with each label:").pack(anchor=tk.W)
        
        # Frame for the mappings table
        self.mappings_table_frame = ttk.Frame(mappings_frame)
        self.mappings_table_frame.pack(fill=tk.X, pady=5)
        
        # Gmail Label Manager Section
        labels_frame = ttk.LabelFrame(scrollable_frame, text="Gmail Label Manager", padding=10)
        labels_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(labels_frame, text="Manage Gmail labels directly:").pack(anchor=tk.W)
        
        # Buttons for label operations
        label_buttons_frame = ttk.Frame(labels_frame)
        label_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(label_buttons_frame, text="Refresh Labels", command=self.refresh_labels).pack(side=tk.LEFT, padx=5)
        ttk.Button(label_buttons_frame, text="Create New Label", command=self.create_new_label).pack(side=tk.LEFT, padx=5)
        
        # Frame for the labels list
        self.labels_list_frame = ttk.Frame(labels_frame)
        self.labels_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Rule Viewer Section
        rules_frame = ttk.LabelFrame(scrollable_frame, text="Rule Viewer/Editor", padding=10)
        rules_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(rules_frame, text="Select a label to view/edit its rules:").pack(anchor=tk.W)
        
        # Rule selection
        rule_select_frame = ttk.Frame(rules_frame)
        rule_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rule_select_frame, text="Label:").pack(side=tk.LEFT)
        self.rule_label_var = tk.StringVar()
        self.rule_label_combo = ttk.Combobox(rule_select_frame, textvariable=self.rule_label_var, state="readonly")
        self.rule_label_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.rule_label_combo.bind('<<ComboboxSelected>>', self.load_rule_details)
        
        ttk.Button(rule_select_frame, text="Load Rule", command=self.load_rule_details).pack(side=tk.LEFT, padx=5)
        
        # Rule details display
        self.rule_details_text = scrolledtext.ScrolledText(rules_frame, height=10)
        self.rule_details_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize components
        self.gmail_label_manager = None
        self.setup_label_mappings_table()
        self.refresh_labels()
        
    def log(self, message):
        """Add message to log."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def connect_gmail(self):
        """Connect to Gmail service."""
        try:
            self.log("Connecting to Gmail...")
            self.cleaner = GmailLMCleaner()
            self.status_label.config(text="✓ Connected to Gmail")
            self.log("✓ Gmail connection successful")
            
            # Initialize management tab components after successful connection
            if hasattr(self, 'setup_label_mappings_table'):
                self.setup_label_mappings_table()
            if hasattr(self, 'refresh_labels'):
                self.refresh_labels()
                
        except Exception as e:
            self.status_label.config(text="❌ Connection failed")
            self.log(f"❌ Gmail connection failed: {e}")
            messagebox.showerror("Error", f"Failed to connect to Gmail: {e}")

    def ensure_cleaner_connection(self):
        """Ensure cleaner has active Gmail connection."""
        if not hasattr(self, 'cleaner') or self.cleaner is None:
            self.log("🔄 No Gmail connection, establishing...")
            self.connect_gmail()
            return hasattr(self, 'cleaner') and self.cleaner is not None
        
        # Test existing connection
        if not self.cleaner.ensure_gmail_connection():
            self.log("🔄 Gmail connection lost, reconnecting...")
            self.connect_gmail()
            return hasattr(self, 'cleaner') and self.cleaner is not None
        
        return True
    
    def process_emails(self):
        """Process emails in a separate thread."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        self.cleaner.settings['dry_run'] = self.dry_run_var.get()
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in thread to avoid freezing UI
        threading.Thread(target=self._process_emails_thread, daemon=True).start()
    
    def _process_emails_thread(self):
        """Thread function for processing emails."""
        try:
            self.cleaner.process_inbox(log_callback=self.log)
        except Exception as e:
            self.log(f"Error processing emails: {e}")
    
    def export_subjects(self):
        """Export email subjects for analysis."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start export in thread to avoid freezing UI
        threading.Thread(target=self._export_subjects_thread, daemon=True).start()
    
    def _export_subjects_thread(self):
        """Thread function for exporting subjects."""
        try:
            self.log("🔍 Starting email subjects export...")
            self.cleaner.export_subjects(max_emails=1000, days_back=30)
            self.log("✅ Export complete! Check email_subjects.txt file")
            self.log("\nUpload this file to Gemini and ask:")
            self.log("'Analyze these email subjects and create better filtering rules'")
            self.log("'Categorize into: INBOX, BILLS, SHOPPING, NEWSLETTERS, SOCIAL, PERSONAL, JUNK'")
        except Exception as e:
            self.log(f"Error exporting subjects: {e}")
    
    def auto_analyze(self):
        """Auto-analyze emails with Gemini and update settings."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        if not GEMINI_API_KEY:
            messagebox.showerror("Error", "GEMINI_API_KEY not found in .env file")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start auto-analysis in thread to avoid freezing UI
        threading.Thread(target=self._auto_analyze_thread, daemon=True).start()
    
    def _auto_analyze_thread(self):
        """Thread function for auto-analyzing with Gemini."""
        try:
            self.log("🚀 Starting automatic email analysis with Gemini...")
            
            # Test Gemini API key first
            self.log("🔑 Testing Gemini API key...")
            if not self.cleaner.test_gemini_connection():
                self.log("❌ Gemini API key test failed - check your .env file")
                return
            self.log("✅ Gemini API key validated")
            
            # Export subjects first
            self.log("📤 Exporting email subjects...")
            subjects_file = self.cleaner.export_subjects(max_emails=1000, days_back=30)
            
            if not subjects_file:
                self.log("❌ Failed to export subjects")
                return
            
            # Analyze with Gemini
            self.log("🤖 Analyzing with Gemini...")
            proposed_rules = self.cleaner.analyze_with_gemini(subjects_file)
            
            if not proposed_rules:
                self.log("❌ Gemini analysis failed - this may be due to OAuth authentication issues")
                self.log("💡 Try re-authenticating in the Settings tab or check your network connection")
                return
            
            self.log("✅ Gemini analysis complete! Showing proposed changes...")
            
            # Show confirmation dialog with proposed changes
            self.root.after(0, lambda: self.show_confirmation_dialog(proposed_rules))
            
        except Exception as e:
            self.log(f"Error during auto-analysis: {e}")
    
    def setup_filters(self):
        """Setup Gmail filters based on current settings."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start filter setup in thread to avoid freezing UI
        threading.Thread(target=self._setup_filters_thread, daemon=True).start()
    
    def _setup_filters_thread(self):
        """Thread function for setting up Gmail filters."""
        try:
            self.log("🔧 Setting up Gmail filters based on current rules...")
            self.cleaner.setup_gmail_filters(log_callback=self.log)
        except Exception as e:
            self.log(f"Error setting up filters: {e}")
    
    def start_backlog_cleanup(self):
        """Start the backlog cleanup process."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        # Update cleaner settings
        self.cleaner.settings['dry_run'] = self.backlog_dry_run_var.get()
        
        # Reset state
        self.processing_paused = False
        self.processing_cancelled = False
        
        # Update UI state
        self.start_backlog_button.config(state=tk.DISABLED)
        self.pause_backlog_button.config(state=tk.NORMAL)
        self.cancel_backlog_button.config(state=tk.NORMAL)
        self.resume_backlog_button.config(state=tk.DISABLED)
        
        # Clear logs and reset progress
        self.backlog_log_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
        self.backlog_progress_var.set(0)
        self.backlog_progress_label.config(text="Starting cleanup...")
        self.backlog_status_label.config(text="Processing emails...")
        
        # Start processing in thread
        threading.Thread(target=self._backlog_cleanup_thread, daemon=True).start()
    
    def pause_backlog_cleanup(self):
        """Pause the backlog cleanup process."""
        self.processing_paused = True
        self.pause_backlog_button.config(state=tk.DISABLED)
        self.resume_backlog_button.config(state=tk.NORMAL)
        self.backlog_status_label.config(text="Paused...")
    
    def resume_backlog_cleanup(self):
        """Resume the backlog cleanup process."""
        self.processing_paused = False
        self.pause_backlog_button.config(state=tk.NORMAL)
        self.resume_backlog_button.config(state=tk.DISABLED)
        self.backlog_status_label.config(text="Processing emails...")
    
    def cancel_backlog_cleanup(self):
        """Cancel the backlog cleanup process."""
        self.processing_cancelled = True
        self.processing_paused = False
        
        # Reset UI state
        self.start_backlog_button.config(state=tk.NORMAL)
        self.pause_backlog_button.config(state=tk.DISABLED)
        self.resume_backlog_button.config(state=tk.DISABLED)
        self.cancel_backlog_button.config(state=tk.DISABLED)
        self.backlog_status_label.config(text="Cancelled")
    
    def _backlog_cleanup_thread(self):
        """Thread function for backlog cleanup processing."""
        self.log(f"Backlog cleanup thread started. Paused: {self.processing_paused}, Cancelled: {self.processing_cancelled}")
        try:
            # Get parameters
            batch_size = int(self.batch_size_var.get())
            older_than_days = int(self.older_than_var.get())
            self.log(f"Batch size: {batch_size}, Older than: {older_than_days} days")
            
            # Define callbacks
            def log_callback(message):
                self.root.after(0, lambda: self._update_backlog_log(message))
            
            def progress_callback(current, total):
                self.root.after(0, lambda: self._update_backlog_progress(current, total))
            
            def pause_callback():
                return self.processing_paused or self.processing_cancelled
            
            # Get processing mode
            processing_mode = self.processing_mode_var.get()
            self.log(f"Processing mode: {processing_mode}")
            
            total_stats = {
                'filter_processed': 0,
                'ai_processed': 0,
                'total_processed': 0,
                'errors': 0
            }
            
            # Apply existing filters first (if not ai_only mode)
            if processing_mode in ["filters_only", "hybrid"]:
                self.log("Phase 1: Applying existing Gmail filters...")
                filter_processed = self.cleaner.apply_existing_filters_to_backlog(
                    log_callback=log_callback
                )
                total_stats['filter_processed'] = filter_processed
                total_stats['total_processed'] += filter_processed
                
                if processing_mode == "filters_only":
                    self.log(f"Filter-only mode complete. Processed {filter_processed} emails.")
                    self.root.after(0, lambda: self._update_final_stats(total_stats))
                    return
            
            # AI processing for remaining emails (if not filters_only mode)
            if processing_mode in ["hybrid", "ai_only"]:
                phase_name = "Phase 2: AI processing remaining emails" if processing_mode == "hybrid" else "AI processing all emails"
                self.log(f"{phase_name}...")
                
                stats = self.cleaner.process_email_backlog(
                    batch_size=batch_size,
                    older_than_days=older_than_days,
                    log_callback=log_callback,
                    progress_callback=progress_callback,
                    pause_callback=pause_callback
                )
                
                total_stats['ai_processed'] = stats.get('total_processed', 0)
                total_stats['total_processed'] += stats.get('total_processed', 0)
                total_stats['errors'] += stats.get('errors', 0)
                total_stats.update(stats)  # Include category breakdown
            self.log(f"All processing complete. Total stats: {total_stats}")
            
            # Update final stats
            self.root.after(0, lambda: self._update_final_stats(total_stats))
            
        except Exception as e:
            error_msg = f"Backlog cleanup error: {e}"
            self.log(error_msg)
            self.root.after(0, lambda: self._update_backlog_log(error_msg))
        finally:
            # Reset UI state
            self.log("Backlog cleanup thread finished.")
            self.root.after(0, self._cleanup_finished)
    
    def _update_backlog_log(self, message):
        """Update the backlog log in the GUI thread."""
        self.backlog_log_text.insert(tk.END, message + "\n")
        self.backlog_log_text.see(tk.END)
        self.root.update()
    
    def _update_backlog_progress(self, current, total):
        """Update the progress bar and labels."""
        if total > 0:
            percentage = (current / total) * 100
            self.backlog_progress_var.set(percentage)
            self.backlog_progress_label.config(text=f"{current} / {total} emails processed ({percentage:.1f}%)")
            
            # Calculate rate if we have stats
            if hasattr(self, 'current_stats') and self.current_stats:
                elapsed = (datetime.now() - self.current_stats['start_time']).total_seconds()
                if elapsed > 0:
                    rate = current / elapsed
                    self.backlog_rate_label.config(text=f"Processing rate: {rate:.1f} emails/sec")
    
    def _update_final_stats(self, stats):
        """Update the final statistics display."""
        self.current_stats = stats
        
        # Clear and update stats text
        self.stats_text.delete(1.0, tk.END)
        
        stats_text = f"📊 Processing Summary:\n"
        stats_text += f"Total found: {stats['total_found']}\n"
        stats_text += f"Successfully processed: {stats['total_processed']}\n"
        stats_text += f"Errors: {stats['errors']}\n"
        
        if 'duration' in stats:
            stats_text += f"Duration: {stats['duration']:.1f} seconds\n"
            if stats['duration'] > 0:
                rate = stats['total_processed'] / stats['duration']
                stats_text += f"Rate: {rate:.1f} emails/second\n"
        
        stats_text += f"\n📈 Category Breakdown:\n"
        for category, count in stats['by_category'].items():
            percentage = (count / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0
            stats_text += f"{category}: {count} ({percentage:.1f}%)\n"
        
        self.stats_text.insert(tk.END, stats_text)
    
    def _cleanup_finished(self):
        """Reset UI state when cleanup is finished."""
        self.start_backlog_button.config(state=tk.NORMAL)
        self.pause_backlog_button.config(state=tk.DISABLED)
        self.resume_backlog_button.config(state=tk.DISABLED)
        self.cancel_backlog_button.config(state=tk.DISABLED)
        
        if self.processing_cancelled:
            self.backlog_status_label.config(text="Cancelled")
        else:
            self.backlog_status_label.config(text="Cleanup complete")
    
    def show_confirmation_dialog(self, proposed_rules):
        """Show confirmation dialog with proposed changes from Gemini."""
        # Create confirmation window
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Confirm Gemini Analysis Results")
        confirm_window.geometry("800x600")
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(confirm_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(main_frame, text="Gemini Analysis Results", font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        # Check if we have valid proposed rules
        if not proposed_rules or not isinstance(proposed_rules, dict):
            # Show error message
            error_frame = ttk.Frame(main_frame)
            error_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(error_frame, text="❌ No Analysis Results Available", 
                     font=('TkDefaultFont', 14, 'bold'), foreground="red").pack(pady=20)
            
            error_text = scrolledtext.ScrolledText(error_frame, height=10, wrap=tk.WORD)
            error_text.pack(fill=tk.BOTH, expand=True, pady=10)
            
            error_message = """Gemini analysis failed or returned no results.

Possible causes:
• OAuth authentication expired (try re-login in Settings)
• Gemini API key issues
• Network connectivity problems
• No email data to analyze

Solutions:
1. Go to Settings tab and click "🔄 Re-login to Gmail"
2. Check your internet connection
3. Verify GEMINI_API_KEY in .env file
4. Try exporting subjects first, then running analysis

Debug Information:
- Current proposed_rules value: """ + str(proposed_rules)
            
            error_text.insert(1.0, error_message)
            error_text.config(state=tk.DISABLED)
            
            # Just a close button
            ttk.Button(main_frame, text="Close", command=confirm_window.destroy).pack(pady=10)
            return
        
        # Create notebook for organized display
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Important Keywords tab
        if 'important_keywords' in proposed_rules:
            keywords_frame = ttk.Frame(notebook)
            notebook.add(keywords_frame, text="Important Keywords")
            
            ttk.Label(keywords_frame, text="Proposed important keywords:").pack(anchor=tk.W, pady=5)
            keywords_text = scrolledtext.ScrolledText(keywords_frame, height=8)
            keywords_text.pack(fill=tk.BOTH, expand=True, pady=5)
            keywords_text.insert(1.0, "\n".join(proposed_rules['important_keywords']))
        
        # Important Senders tab
        if 'important_senders' in proposed_rules:
            senders_frame = ttk.Frame(notebook)
            notebook.add(senders_frame, text="Important Senders")
            
            ttk.Label(senders_frame, text="Proposed important sender patterns:").pack(anchor=tk.W, pady=5)
            senders_text = scrolledtext.ScrolledText(senders_frame, height=8)
            senders_text.pack(fill=tk.BOTH, expand=True, pady=5)
            senders_text.insert(1.0, "\n".join(proposed_rules['important_senders']))
        
        # Category Rules tab
        if 'category_rules' in proposed_rules:
            categories_frame = ttk.Frame(notebook)
            notebook.add(categories_frame, text="Category Rules")
            
            ttk.Label(categories_frame, text="Proposed category rules:").pack(anchor=tk.W, pady=5)
            categories_text = scrolledtext.ScrolledText(categories_frame, height=15)
            categories_text.pack(fill=tk.BOTH, expand=True, pady=5)
            categories_text.insert(1.0, json.dumps(proposed_rules['category_rules'], indent=2))
        
        # Auto-delete Senders tab
        if 'auto_delete_senders' in proposed_rules:
            delete_frame = ttk.Frame(notebook)
            notebook.add(delete_frame, text="Auto-Delete Senders")
            
            ttk.Label(delete_frame, text="Proposed auto-delete senders:").pack(anchor=tk.W, pady=5)
            delete_text = scrolledtext.ScrolledText(delete_frame, height=8)
            delete_text.pack(fill=tk.BOTH, expand=True, pady=5)
            delete_text.insert(1.0, "\n".join(proposed_rules['auto_delete_senders']))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_changes():
            try:
                self.cleaner.apply_gemini_rules(proposed_rules, log_callback=self.log)
                
                # Refresh UI components
                self.load_settings()
                if hasattr(self, 'setup_label_mappings_table'):
                    self.setup_label_mappings_table()
                if hasattr(self, 'refresh_labels'):
                    self.refresh_labels()
                
                confirm_window.destroy()
                messagebox.showinfo("Success", "Gemini rules applied successfully!\n\nYour filtering rules have been updated.")
            except Exception as e:
                self.log(f"❌ Error applying rules: {e}")
                messagebox.showerror("Error", f"Failed to apply rules: {e}")
        
        def cancel_changes():
            self.log("❌ User cancelled Gemini rule application")
            confirm_window.destroy()
        
        ttk.Button(buttons_frame, text="Apply Changes", command=apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=cancel_changes).pack(side=tk.RIGHT, padx=5)
        
        # Warning label
        warning_label = ttk.Label(main_frame, 
                                text="⚠️ Review all proposed changes carefully before applying.", 
                                foreground="orange")
        warning_label.pack(pady=5)
    
    def refresh_models(self):
        """Refresh the list of available LM Studio models."""
        if not self.cleaner:
            self.cleaner = GmailLMCleaner()
        
        models = self.cleaner.get_available_models()
        model_options = ["auto"] + models
        
        self.model_combo['values'] = model_options
        if not models:
            self.model_combo['values'] = ["auto", "No models available"]

    def relogin_gmail(self):
        """Force re-authentication with Gmail."""
        try:
            self.log("🔄 Starting Gmail re-authentication...")
            
            # Delete existing token
            token_path = "config/token.json"
            if os.path.exists(token_path):
                os.remove(token_path)
                self.log("   ✅ Existing token deleted")
            
            # Reset cleaner connection
            self.cleaner = None
            
            # Reconnect
            if self.ensure_cleaner_connection():
                self.log("✅ Gmail re-authentication successful!")
                messagebox.showinfo("Success", "Gmail re-authentication completed successfully!")
            else:
                self.log("❌ Gmail re-authentication failed")
                messagebox.showerror("Error", "Failed to re-authenticate with Gmail")
                
        except Exception as e:
            self.log(f"❌ Error during re-authentication: {e}")
            messagebox.showerror("Error", f"Re-authentication failed: {e}")

    def reset_oauth_token(self):
        """Reset the OAuth token without immediate re-authentication."""
        try:
            token_path = "config/token.json"
            if os.path.exists(token_path):
                # Backup the token first
                backup_path = f"config/token_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import shutil
                shutil.copy2(token_path, backup_path)
                
                # Delete current token
                os.remove(token_path)
                self.log(f"✅ OAuth token reset successfully (backup saved to {backup_path})")
                messagebox.showinfo("Success", f"OAuth token reset successfully!\nBackup saved to: {backup_path}")
                
                # Clear cleaner connection
                self.cleaner = None
            else:
                self.log("⚠️ No OAuth token found to reset")
                messagebox.showwarning("Warning", "No OAuth token file found")
                
        except Exception as e:
            self.log(f"❌ Error resetting OAuth token: {e}")
            messagebox.showerror("Error", f"Failed to reset OAuth token: {e}")
    
    def load_settings(self):
        """Load settings into UI."""
        if not self.cleaner:
            self.cleaner = GmailLMCleaner()
        
        settings = self.cleaner.settings
        
        self.keywords_text.delete(1.0, tk.END)
        self.keywords_text.insert(1.0, "\n".join(settings['important_keywords']))
        
        self.senders_text.delete(1.0, tk.END)
        self.senders_text.insert(1.0, "\n".join(settings['important_senders']))
        
        self.never_delete_text.delete(1.0, tk.END)
        self.never_delete_text.insert(1.0, "\n".join(settings['never_delete_senders']))
        
        self.days_var.set(str(settings['days_back']))
        self.max_emails_var.set(str(settings['max_emails_per_run']))
        
        # Load model selection
        model_setting = settings.get('lm_studio_model', 'auto')
        self.model_var.set(model_setting)
        self.refresh_models()
        
        # Auto-refresh management tab components if they exist
        if hasattr(self, 'setup_label_mappings_table'):
            try:
                self.setup_label_mappings_table()
            except Exception as e:
                pass  # Silently fail if management tab not initialized yet
        
        self.log("Settings loaded")
    
    def save_settings(self):
        """Save settings from UI."""
        if not self.cleaner:
            self.cleaner = GmailLMCleaner()
        
        # Update settings from UI
        self.cleaner.settings['important_keywords'] = [
            k.strip() for k in self.keywords_text.get(1.0, tk.END).strip().split('\n') if k.strip()
        ]
        self.cleaner.settings['important_senders'] = [
            s.strip() for s in self.senders_text.get(1.0, tk.END).strip().split('\n') if s.strip()
        ]
        self.cleaner.settings['never_delete_senders'] = [
            s.strip() for s in self.never_delete_text.get(1.0, tk.END).strip().split('\n') if s.strip()
        ]
        
        try:
            self.cleaner.settings['days_back'] = int(self.days_var.get())
            self.cleaner.settings['max_emails_per_run'] = int(self.max_emails_var.get())
        except ValueError:
            messagebox.showerror("Error", "Days back and max emails must be numbers")
            return
        
        # Save model selection
        self.cleaner.settings['lm_studio_model'] = self.model_var.get()
        
        self.cleaner.save_settings()
        self.log("Settings saved")
        messagebox.showinfo("Success", "Settings saved successfully")
    
    def reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            if not self.cleaner:
                self.cleaner = GmailLMCleaner()
            self.cleaner.settings = DEFAULT_SETTINGS.copy()
            self.load_settings()
            self.log("Settings reset to defaults")
    
    def setup_label_mappings_table(self):
        """Setup the label action mappings table."""
        # Clear existing widgets
        for widget in self.mappings_table_frame.winfo_children():
            widget.destroy()
        
        if not self.cleaner:
            ttk.Label(self.mappings_table_frame, text="Connect to Gmail first to load mappings").pack()
            return
        
        # Load settings to get label_action_mappings
        self.cleaner.settings = self.cleaner.load_settings()
        mappings = self.cleaner.settings.get('label_action_mappings', {})
        
        # Header
        header_frame = ttk.Frame(self.mappings_table_frame)
        header_frame.pack(fill=tk.X, pady=2)
        ttk.Label(header_frame, text="Label", width=20).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Action", width=20).pack(side=tk.LEFT)
        
        # Action options
        action_options = ["KEEP", "LABEL_AND_ARCHIVE", "TRASH", "IMPORTANT"]
        
        self.mapping_vars = {}
        for label, action in mappings.items():
            row_frame = ttk.Frame(self.mappings_table_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=label, width=20).pack(side=tk.LEFT)
            
            action_var = tk.StringVar(value=action)
            self.mapping_vars[label] = action_var
            action_combo = ttk.Combobox(row_frame, textvariable=action_var, 
                                      values=action_options, state="readonly", width=18)
            action_combo.pack(side=tk.LEFT, padx=5)
            action_combo.bind('<<ComboboxSelected>>', lambda e, l=label: self.update_label_mapping(l))
        
        # Save button
        ttk.Button(self.mappings_table_frame, text="Save All Mappings", 
                  command=self.save_all_mappings).pack(pady=10)
    
    def update_label_mapping(self, label):
        """Update a single label mapping."""
        if not self.cleaner:
            return
        
        new_action = self.mapping_vars[label].get()
        if 'label_action_mappings' not in self.cleaner.settings:
            self.cleaner.settings['label_action_mappings'] = {}
        
        self.cleaner.settings['label_action_mappings'][label] = new_action
        self.log(f"Updated {label} -> {new_action}")
    
    def save_all_mappings(self):
        """Save all label mappings to settings file."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
        
        try:
            self.cleaner.save_settings()
            self.log("All label mappings saved successfully")
            messagebox.showinfo("Success", "Label mappings saved successfully")
        except Exception as e:
            self.log(f"Error saving mappings: {e}")
            messagebox.showerror("Error", f"Failed to save mappings: {e}")
    
    def refresh_labels(self):
        """Refresh the Gmail labels list."""
        if not self.cleaner:
            self.log("Connect to Gmail first to refresh labels")
            return
        
        try:
            # Initialize Gmail label manager if not already done
            if not self.gmail_label_manager:
                gmail_service = get_gmail_service()
                if gmail_service:
                    self.gmail_label_manager = GmailLabelManager(gmail_service)
                else:
                    self.log("Failed to get Gmail service")
                    return
            
            # Refresh label cache
            self.gmail_label_manager.refresh_label_cache()
            labels = self.gmail_label_manager.list_labels()
            
            # Clear existing widgets
            for widget in self.labels_list_frame.winfo_children():
                widget.destroy()
            
            # Create header
            header_frame = ttk.Frame(self.labels_list_frame)
            header_frame.pack(fill=tk.X, pady=2)
            ttk.Label(header_frame, text="Label Name", width=30).pack(side=tk.LEFT)
            ttk.Label(header_frame, text="Actions", width=30).pack(side=tk.LEFT)
            
            # List labels with action buttons
            for label_name, label_id in labels.items():
                # Skip system labels
                if label_name in ['INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH', 'IMPORTANT', 'STARRED', 'UNREAD']:
                    continue
                
                row_frame = ttk.Frame(self.labels_list_frame)
                row_frame.pack(fill=tk.X, pady=1)
                
                ttk.Label(row_frame, text=label_name, width=30).pack(side=tk.LEFT)
                
                actions_frame = ttk.Frame(row_frame)
                actions_frame.pack(side=tk.LEFT)
                
                ttk.Button(actions_frame, text="Rename", width=8,
                          command=lambda ln=label_name: self.rename_label(ln)).pack(side=tk.LEFT, padx=2)
                ttk.Button(actions_frame, text="Delete", width=8,
                          command=lambda ln=label_name: self.delete_label(ln)).pack(side=tk.LEFT, padx=2)
            
            # Update rule combo box
            label_names = [name for name in labels.keys() 
                          if name not in ['INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH', 'IMPORTANT', 'STARRED', 'UNREAD']]
            self.rule_label_combo['values'] = label_names
            
            self.log(f"Refreshed {len(labels)} Gmail labels")
            
        except Exception as e:
            self.log(f"Error refreshing labels: {e}")
            messagebox.showerror("Error", f"Failed to refresh labels: {e}")
    
    def create_new_label(self):
        """Create a new Gmail label."""
        if not self.gmail_label_manager:
            messagebox.showwarning("Warning", "Please refresh labels first")
            return
        
        label_name = simpledialog.askstring("Create Label", "Enter label name:")
        if label_name:
            try:
                label_id = self.gmail_label_manager.create_label(label_name)
                if label_id:
                    self.log(f"Created label: {label_name}")
                    messagebox.showinfo("Success", f"Label '{label_name}' created successfully")
                    self.refresh_labels()
                    self.setup_label_mappings_table()  # Refresh mappings table
                else:
                    messagebox.showerror("Error", f"Failed to create label '{label_name}'")
            except Exception as e:
                self.log(f"Error creating label: {e}")
                messagebox.showerror("Error", f"Failed to create label: {e}")
    
    def rename_label(self, old_name):
        """Rename a Gmail label."""
        if not self.gmail_label_manager:
            messagebox.showwarning("Warning", "Please refresh labels first")
            return
        
        new_name = simpledialog.askstring("Rename Label", f"Enter new name for '{old_name}':")
        if new_name:
            if messagebox.askyesno("Confirm Rename", f"Rename '{old_name}' to '{new_name}'?\n\nThis will update all emails with this label."):
                try:
                    if self.gmail_label_manager.rename_label(old_name, new_name):
                        self.log(f"Renamed label: {old_name} -> {new_name}")
                        messagebox.showinfo("Success", f"Label renamed successfully")
                        self.refresh_labels()
                        self.setup_label_mappings_table()  # Refresh mappings table
                    else:
                        messagebox.showerror("Error", f"Failed to rename label")
                except Exception as e:
                    self.log(f"Error renaming label: {e}")
                    messagebox.showerror("Error", f"Failed to rename label: {e}")
    
    def delete_label(self, label_name):
        """Delete a Gmail label."""
        if not self.gmail_label_manager:
            messagebox.showwarning("Warning", "Please refresh labels first")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete label '{label_name}'?\n\nThis will remove the label from all emails."):
            try:
                if self.gmail_label_manager.delete_label(label_name):
                    self.log(f"Deleted label: {label_name}")
                    messagebox.showinfo("Success", f"Label '{label_name}' deleted successfully")
                    self.refresh_labels()
                    self.setup_label_mappings_table()  # Refresh mappings table
                else:
                    messagebox.showerror("Error", f"Failed to delete label '{label_name}'")
            except Exception as e:
                self.log(f"Error deleting label: {e}")
                messagebox.showerror("Error", f"Failed to delete label: {e}")
    
    def load_rule_details(self, event=None):
        """Load and display rule details for selected label."""
        label_name = self.rule_label_var.get()
        if not label_name:
            return
        
        try:
            rules_dir = "rules"
            rule_file = os.path.join(rules_dir, f"{label_name}.json")
            
            if os.path.exists(rule_file):
                with open(rule_file, 'r') as f:
                    rule_data = json.load(f)
                
                # Format the rule data for display
                formatted_data = json.dumps(rule_data, indent=2)
                
                self.rule_details_text.delete(1.0, tk.END)
                self.rule_details_text.insert(1.0, formatted_data)
                
                self.log(f"Loaded rule details for {label_name}")
            else:
                self.rule_details_text.delete(1.0, tk.END)
                self.rule_details_text.insert(1.0, f"No rule file found for '{label_name}'\n\nRule file would be: {rule_file}")
                
        except Exception as e:
            self.log(f"Error loading rule details: {e}")
            self.rule_details_text.delete(1.0, tk.END)
            self.rule_details_text.insert(1.0, f"Error loading rule details: {e}")
    
    def run(self):
        """Start the GUI."""
        self.load_settings()
        self.root.mainloop()
        
    def setup_analytics_tab(self, parent):
        """Setup the analytics dashboard tab."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Category Distribution
        dist_frame = ttk.LabelFrame(scrollable_frame, text="Category Distribution", padding=10)
        dist_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Placeholder for pie chart
        self.dist_canvas = tk.Canvas(dist_frame, width=300, height=200, bg='white')
        self.dist_canvas.pack()
        self.dist_canvas.create_text(150, 100, text="Category Distribution Pie Chart (placeholder)")

        # Filter Effectiveness
        effectiveness_frame = ttk.LabelFrame(scrollable_frame, text="Filter Effectiveness", padding=10)
        effectiveness_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(effectiveness_frame, text="Effectiveness scores (placeholder):").pack(anchor=tk.W)
        self.effectiveness_text = scrolledtext.ScrolledText(effectiveness_frame, height=5)
        self.effectiveness_text.pack(fill=tk.X, pady=5)
        self.effectiveness_text.insert(1.0, "SHOPPING Filter: 95%\nBILLS Filter: 98%\n")

        # Suggested Optimizations
        optimizations_frame = ttk.LabelFrame(scrollable_frame, text="Suggested Optimizations", padding=10)
        optimizations_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(optimizations_frame, text="Suggested optimizations (placeholder):").pack(anchor=tk.W)
        self.optimizations_text = scrolledtext.ScrolledText(optimizations_frame, height=5)
        self.optimizations_text.pack(fill=tk.X, pady=5)
        self.optimizations_text.insert(1.0, "Suggestion: Create a new label for 'Project X' based on recent emails.\n")
        
        # Auto-Evolve Button
        evolve_frame = ttk.LabelFrame(scrollable_frame, text="Auto-Evolution", padding=10)
        evolve_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(evolve_frame, text="Run Auto-Evolution", command=self.run_auto_evolution).pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_unsubscribe_tab(self, parent):
        """Setup the unsubscribe assistant tab."""
        # Control frame
        control_frame = ttk.LabelFrame(parent, text="Actions", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Find Unsubscribe Candidates", command=self.find_unsubscribe_candidates).pack(side=tk.LEFT, padx=5)
        
        # Candidates frame
        candidates_frame = ttk.LabelFrame(parent, text="Unsubscribe Candidates", padding=10)
        candidates_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.unsubscribe_text = scrolledtext.ScrolledText(candidates_frame, height=15)
        self.unsubscribe_text.pack(fill=tk.BOTH, expand=True)

    def find_unsubscribe_candidates(self):
        """Find and display unsubscribe candidates."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
            
        self.unsubscribe_text.delete(1.0, tk.END)
        self.log("Finding unsubscribe candidates...")
        
        def log_callback(message):
            self.root.after(0, lambda: self.log(message))

        def find_candidates_thread():
            candidates = self.cleaner.analyze_unsubscribe_candidates(log_callback=log_callback)
            self.root.after(0, lambda: self.display_unsubscribe_candidates(candidates))

        threading.Thread(target=find_candidates_thread, daemon=True).start()

    def display_unsubscribe_candidates(self, candidates):
        """Display unsubscribe candidates in the text area."""
        self.unsubscribe_text.delete(1.0, tk.END)
        if candidates:
            self.unsubscribe_text.insert(tk.END, "\n".join(candidates))
        else:
            self.unsubscribe_text.insert(tk.END, "No unsubscribe candidates found.")
        self.log("Unsubscribe analysis complete.")

    def run_auto_evolution(self):
        """Run the auto-evolution process."""
        if not self.ensure_cleaner_connection():
            messagebox.showwarning("Warning", "Failed to establish Gmail connection")
            return
            
        self.log("Running auto-evolution process...")
        
        def log_callback(message):
            self.root.after(0, lambda: self.log(message))

        def auto_evolve_thread():
            self.cleaner.auto_evolve_system(log_callback=log_callback)

        threading.Thread(target=auto_evolve_thread, daemon=True).start()
 
def main():
    """Main function to run the GUI."""
    app = GmailCleanerGUI()
    app.run()

if __name__ == '__main__':
    main()