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

class GmailLMCleaner:
    def __init__(self, credentials_file='credentials.json', token_file='token.json', settings_file='settings.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.settings_file = settings_file
        self.service = None
        self.settings = self.load_settings()
        self.llm_prompts = self.load_llm_prompts() # Load LLM prompts
        self.logger = self.setup_logging()
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
    
    def log_email_processing(self, email_id, subject, decision, reason):
        """Log email processing details."""
        self.logger.info(f"Processed: {email_id} | {subject[:50]}... | "
                        f"Decision: {decision} | Reason: {reason}")
    
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
        """Authenticate and create Gmail service instance."""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
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
    
    def is_important_email(self, email_data):
        """Check if email contains important keywords or is from important sender."""
        subject_lower = email_data.get('subject', '').lower()
        sender_lower = email_data.get('sender', '').lower()
        body_lower = email_data.get('body', '').lower()
        
        # Check important keywords
        for keyword in self.settings['important_keywords']:
            if keyword.lower() in subject_lower or keyword.lower() in body_lower:
                return True
        
        # Check important senders
        for sender_pattern in self.settings['important_senders']:
            if sender_pattern.lower() in sender_lower:
                return True
        
        return False
    
    def is_promotional_email(self, email_data):
        """Check if email is promotional."""
        subject_lower = email_data.get('subject', '').lower()
        body_lower = email_data.get('body', '').lower()
        
        promo_count = 0
        for keyword in self.settings['promotional_keywords']:
            if keyword.lower() in subject_lower or keyword.lower() in body_lower:
                return True
        
        return promo_count >= 2  # Require at least 2 promotional keywords
    
    def build_categorization_prompt(self, email_data):
        """Build a structured prompt for email categorization matching LM Studio system prompt."""
        prompt = f"""Analyze this email:
Subject: {email_data['subject']}
From: {email_data['sender']}
Preview: {email_data['body_preview']}"""
        return prompt

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
            
            # Add model selection if specified
            model_name = self.settings.get('lm_studio_model', 'auto')
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
            
            # Check importance
            if self.is_important_email(email_data):
                return {"action": "INBOX", "reason": "Contains important keywords"}
            
            # Check for promotional content
            if self.is_promotional_email(email_data):
                return {"action": "SHOPPING", "reason": "Promotional email"}
            
            # Prepare safe data for LLM
            safe_email_data = {
                'subject': str(email_data.get('subject', 'No Subject'))[:200],
                'sender': str(email_data.get('sender', 'Unknown'))[:100],
                'body_preview': str(email_data.get('body', ''))[:500],
                'date': str(email_data.get('date', 'Unknown'))[:50]
            }
            
            # Build LLM prompt
            prompt = self.build_categorization_prompt(safe_email_data)
            
            # Call LLM with timeout
            decision = self.call_lm_studio(prompt, timeout=10)
            
            return self.validate_llm_decision(decision)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"LLM analysis error: {str(e)}")
            else:
                print(f"LLM analysis error: {str(e)}")
            return {"action": "KEEP", "reason": f"Analysis error: {str(e)}"}
    
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
            if hasattr(self, 'logger'):
                self.logger.error(f"Error creating label {label_name}: {e}")
            else:
                print(f"Error creating label {label_name}: {e}")
            return None
 
    def execute_action(self, email_id, action, reason, log_callback=None):
        """Execute the decided action on the email."""
        try:
            if self.settings['dry_run']:
                if log_callback:
                    log_callback(f"  [DRY RUN] Would move to {action}: {reason}")
                return
            
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
                        'BILLS': '💰',
                        'SHOPPING': '🛒',
                        'NEWSLETTERS': '📰',
                        'SOCIAL': '👥',
                        'PERSONAL': '📧'
                    }
                    
                    emoji = folder_emoji.get(action, '📁')
                    
                    if log_callback:
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
                        decision['reason']
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
            gemini_prompts = self.llm_prompts.get("gemini", {})
            analysis_prompt_template = gemini_prompts.get("analysis_prompt", "")

            if not analysis_prompt_template:
                print("❌ Gemini analysis prompt not found in settings.")
                return None

            prompt = analysis_prompt_template.format(subjects_content=subjects_content)
            
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
 
class GmailCleanerGUI:
    def __init__(self):
        self.cleaner = None
        self.setup_ui()
        
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
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Rule & Label Management tab
        management_frame = ttk.Frame(notebook)
        notebook.add(management_frame, text="Rule & Label Management")
        
        self.setup_main_tab(main_frame)
        self.setup_settings_tab(settings_frame)
        self.setup_management_tab(management_frame)
        
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
        
        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Dry Run (don't actually modify emails)",
                       variable=self.dry_run_var).pack(anchor=tk.W)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
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
            self.status_label.config(text="✗ Connection failed")
            self.log(f"✗ Gmail connection failed: {e}")
            messagebox.showerror("Error", f"Failed to connect to Gmail: {e}")
    
    def process_emails(self):
        """Process emails in a separate thread."""
        if not self.cleaner:
            messagebox.showwarning("Warning", "Please connect to Gmail first")
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
        if not self.cleaner:
            messagebox.showwarning("Warning", "Please connect to Gmail first")
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
        if not self.cleaner:
            messagebox.showwarning("Warning", "Please connect to Gmail first")
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
                self.log("❌ Gemini analysis failed")
                return
            
            self.log("✅ Gemini analysis complete! Showing proposed changes...")
            
            # Show confirmation dialog with proposed changes
            self.root.after(0, lambda: self.show_confirmation_dialog(proposed_rules))
            
        except Exception as e:
            self.log(f"Error during auto-analysis: {e}")
    
    def setup_filters(self):
        """Setup Gmail filters based on current settings."""
        if not self.cleaner:
            messagebox.showwarning("Warning", "Please connect to Gmail first")
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
        if not self.cleaner:
            messagebox.showwarning("Warning", "Please connect to Gmail first")
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
 
def main():
    """Main function to run the GUI."""
    app = GmailCleanerGUI()
    app.run()
 
if __name__ == '__main__':
    main()