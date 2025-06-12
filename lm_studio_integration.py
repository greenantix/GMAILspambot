#!/usr/bin/env python3
"""
LM Studio Integration for Gmail Spam Bot
Smart model switching for different tasks with automatic loading/unloading
"""

import json
import requests
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from log_config import get_logger

logger = get_logger(__name__)

class LMStudioManager:
    """Manages LM Studio models with smart switching for different tasks"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234", timeout: int = 60):
        self.base_url = base_url
        self.timeout = timeout
        self.current_model = None
        self.models = {
            # Fast models for email categorization
            "fast": {
                "name": "phi-3-mini-4k-instruct",
                "context_window": 4096,
                "use_case": "Quick email categorization, simple classification"
            },
            "medium": {
                "name": "meta-llama-3.1-8b-instruct", 
                "context_window": 8192,
                "use_case": "Standard email processing, moderate complexity"
            },
            # Large context for bulk analysis
            "large": {
                "name": "meta-llama-3.1-8b-instruct",
                "context_window": 100000,
                "use_case": "Bulk analysis, pattern detection, comprehensive review"
            },
            "coding": {
                "name": "codellama-13b-instruct",
                "context_window": 16384,
                "use_case": "Rule generation, configuration analysis"
            }
        }
    
    def is_server_running(self) -> bool:
        """Check if LM Studio server is running"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_loaded_model(self) -> Optional[str]:
        """Get currently loaded model"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=self.timeout)
            if response.status_code == 200:
                models = response.json()
                if models.get("data"):
                    return models["data"][0]["id"]
        except requests.RequestException as e:
            logger.warning(f"Could not get loaded model: {e}")
        return None
    
    def load_model(self, model_key: str) -> bool:
        """Note: LM Studio API does not support programmatic model loading"""
        logger.warning("LM Studio API does not support remote model loading")
        logger.info("Models must be loaded manually in the LM Studio interface")
        if model_key in self.models:
            logger.info(f"To optimize performance, please load: {self.models[model_key]['name']}")
        return False
    
    def detect_current_model_capability(self) -> str:
        """Detect what type of model is currently loaded based on its ID"""
        current_model_id = self.get_loaded_model()
        if not current_model_id:
            return "unknown"
        
        # Map loaded model to capability level
        model_id_lower = current_model_id.lower()
        
        if any(fast_term in model_id_lower for fast_term in ["phi", "mini", "small"]):
            return "fast"
        elif any(large_term in model_id_lower for large_term in ["70b", "large", "big"]):
            return "large"
        elif any(code_term in model_id_lower for code_term in ["code", "coder", "coding"]):
            return "coding"
        else:
            return "medium"  # Default assumption
    
    def generate_completion(self, prompt: str, max_tokens: int = 1000, 
                          temperature: float = 0.3, preferred_model: str = "medium") -> Optional[str]:
        """Generate completion using currently loaded model (Smart Selection Strategy)"""
        
        if not self.is_server_running():
            logger.error("LM Studio server is not running")
            return None
        
        # Use smart selection: work with whatever model is currently loaded
        current_model_id = self.get_loaded_model()
        if not current_model_id:
            logger.error("No model currently loaded in LM Studio")
            logger.info("Please load a model manually in LM Studio interface")
            return None
        
        # Detect model capability and adjust parameters accordingly
        detected_capability = self.detect_current_model_capability()
        logger.info(f"Using loaded model: {current_model_id} (detected as '{detected_capability}' capability)")
        
        # Adjust parameters based on detected model capability
        adjusted_max_tokens = max_tokens
        adjusted_temperature = temperature
        
        if detected_capability == "fast":
            # Fast models: reduce tokens for quicker responses
            adjusted_max_tokens = min(max_tokens, 500)
            logger.debug("Adjusted for fast model: reduced max_tokens")
        elif detected_capability == "large":
            # Large models: can handle more complexity
            adjusted_max_tokens = min(max_tokens, 2000)
            adjusted_temperature = max(temperature, 0.1)  # Slightly higher temp for creativity
            logger.debug("Adjusted for large model: increased max_tokens")
        
        try:
            payload = {
                "model": current_model_id,  # Use the actual loaded model ID
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": adjusted_max_tokens,
                "temperature": adjusted_temperature,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    logger.debug(f"Generated {len(content)} characters using {detected_capability} model")
                    return content
            else:
                logger.error(f"LM Studio API error: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Error calling LM Studio API: {e}")
        
        return None
    
    def categorize_emails_batch(self, email_subjects: List[str], 
                               email_senders: List[str] = None) -> List[Dict]:
        """Fast email categorization using smaller model"""
        
        if not email_subjects:
            return []
        
        # Use fast model for quick categorization
        categories = ["INBOX", "BILLS", "SHOPPING", "NEWSLETTERS", "SOCIAL", "PERSONAL", "JUNK", "REVIEW"]
        
        # Build prompt for batch processing
        emails_text = ""
        for i, subject in enumerate(email_subjects[:50]):  # Limit batch size
            sender = email_senders[i] if email_senders and i < len(email_senders) else "unknown"
            emails_text += f"{i+1}. From: {sender} | Subject: {subject}\n"
        
        prompt = f"""You are an expert email categorization system. Analyze each email and assign the most appropriate category.

CATEGORIES:
• INBOX - Critical/urgent only (security alerts, payment issues, account problems)
• BILLS - Receipts, invoices, statements, financial documents
• SHOPPING - Orders, shipping updates, promotions, retail communications  
• NEWSLETTERS - News, updates, educational content, subscriptions
• SOCIAL - Social media, gaming, app notifications
• PERSONAL - Personal correspondence, scheduling, real estate
• JUNK - Spam, irrelevant content, suspicious emails

EMAILS TO CATEGORIZE:
{emails_text}

Respond with ONLY valid JSON array. Each object must have "index" (1-based) and "category":
[{{"index": 1, "category": "SHOPPING"}}, {{"index": 2, "category": "NEWSLETTERS"}}]"""

        result = self.generate_completion(
            prompt, 
            max_tokens=2000, 
            temperature=0.1, 
            model_key="fast"
        )
        
        if result:
            try:
                # Parse JSON response
                categories_data = json.loads(result)
                return categories_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse categorization result: {e}")
                logger.debug(f"Raw result: {result}")
        
        return []
    
    def analyze_email_patterns(self, email_data: List[Dict], 
                              max_emails: int = 1000) -> Dict:
        """Comprehensive pattern analysis using large context model"""
        
        if not email_data:
            return {}
        
        # Use large context model for comprehensive analysis
        emails_sample = email_data[:max_emails]
        
        # Build comprehensive data for analysis
        analysis_data = {
            "total_emails": len(emails_sample),
            "subjects": [email.get("subject", "") for email in emails_sample],
            "senders": [email.get("sender", "") for email in emails_sample],
            "dates": [email.get("date", "") for email in emails_sample]
        }
        
        prompt = f"""You are an advanced email pattern analysis expert. Analyze this dataset of {len(emails_sample)} emails and provide comprehensive insights.

Email Data Summary:
- Total emails: {analysis_data['total_emails']}
- Sample subjects: {analysis_data['subjects'][:20]}
- Sample senders: {analysis_data['senders'][:20]}

Provide analysis in the following JSON format:
{{
  "sender_patterns": {{
    "top_domains": [list of most frequent sender domains],
    "spam_indicators": [list of suspicious sender patterns],
    "legitimate_senders": [list of clearly legitimate senders]
  }},
  "subject_patterns": {{
    "common_keywords": [list of most frequent keywords],
    "spam_keywords": [list of spam-indicating keywords],
    "categories_detected": [list of detected email categories]
  }},
  "recommendations": {{
    "filter_suggestions": [list of suggested Gmail filters],
    "categorization_rules": [list of suggested categorization rules],
    "cleanup_targets": [list of emails/senders to consider for cleanup]
  }},
  "statistics": {{
    "estimated_spam_percentage": number,
    "estimated_newsletter_percentage": number,
    "estimated_important_percentage": number
  }}
}}

Focus on practical, actionable insights that can improve email organization."""

        result = self.generate_completion(
            prompt,
            max_tokens=4000,
            temperature=0.3,
            model_key="large"  # Use large context model
        )
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pattern analysis: {e}")
                logger.debug(f"Raw result: {result}")
        
        return {}
    
    def generate_filter_rules(self, pattern_analysis: Dict) -> List[Dict]:
        """Generate Gmail filter rules from pattern analysis"""
        
        if not pattern_analysis:
            return []
        
        prompt = f"""Based on this email pattern analysis, generate practical Gmail filter rules.

Analysis Data:
{json.dumps(pattern_analysis, indent=2)}

Generate Gmail filters in this JSON format:
[
  {{
    "name": "Filter name",
    "criteria": {{
      "from": "sender criteria (optional)",
      "subject": "subject criteria (optional)", 
      "has": "content criteria (optional)"
    }},
    "actions": {{
      "apply_label": "LABEL_NAME",
      "archive": true/false,
      "mark_read": true/false
    }},
    "description": "What this filter does"
  }}
]

Focus on high-impact filters that will catch the most emails with high accuracy."""

        result = self.generate_completion(
            prompt,
            max_tokens=3000,
            temperature=0.2,
            model_key="medium"
        )
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse filter rules: {e}")
                logger.debug(f"Raw result: {result}")
        
        return []
    
    def optimize_settings(self, current_settings: Dict, 
                         processing_stats: Dict) -> Dict:
        """Suggest settings optimizations based on processing results"""
        
        prompt = f"""You are a system optimization expert. Based on current settings and processing statistics, suggest improvements.

Current Settings:
{json.dumps(current_settings, indent=2)}

Processing Statistics:
{json.dumps(processing_stats, indent=2)}

Provide optimization suggestions in JSON format:
{{
  "settings_changes": {{
    "section.setting_name": "new_value_with_explanation"
  }},
  "performance_improvements": [
    "List of performance improvement suggestions"
  ],
  "accuracy_improvements": [
    "List of accuracy improvement suggestions"  
  ],
  "maintenance_suggestions": [
    "List of maintenance and monitoring suggestions"
  ]
}}

Focus on evidence-based improvements that will measurably improve performance."""

        result = self.generate_completion(
            prompt,
            max_tokens=2000,
            temperature=0.2,
            model_key="medium"
        )
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse optimization suggestions: {e}")
                logger.debug(f"Raw result: {result}")
        
        return {}

# Global instance
lm_studio = LMStudioManager()

def analyze_email_subjects_with_lm_studio(use_existing_export: bool = False) -> Optional[Dict]:
    """Main function to replace Gemini analysis with LM Studio"""
    
    logger.info("Starting LM Studio email analysis")
    
    if not lm_studio.is_server_running():
        logger.error("LM Studio server is not running. Please start LM Studio and load a model.")
        return None
    
    # Load email data
    email_data = []
    
    if use_existing_export:
        # Try to load from existing export
        export_files = list(Path("exports").glob("*.json")) if Path("exports").exists() else []
        if export_files:
            latest_export = max(export_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_export, 'r') as f:
                    email_data = json.load(f)
                logger.info(f"Loaded {len(email_data)} emails from {latest_export}")
            except Exception as e:
                logger.error(f"Failed to load export file: {e}")
    
    if not email_data:
        # Load from email_subjects.txt as fallback
        subjects_file = Path("email_subjects.txt")
        if subjects_file.exists():
            with open(subjects_file, 'r') as f:
                subjects = [line.strip() for line in f if line.strip()]
            email_data = [{"subject": subj, "sender": "unknown"} for subj in subjects]
            logger.info(f"Loaded {len(email_data)} subjects from email_subjects.txt")
    
    if not email_data:
        logger.error("No email data found for analysis")
        return None
    
    # Perform comprehensive analysis
    logger.info("Running pattern analysis with large context model...")
    pattern_analysis = lm_studio.analyze_email_patterns(email_data)
    
    if not pattern_analysis:
        logger.error("Pattern analysis failed")
        return None
    
    # Generate filter rules
    logger.info("Generating filter rules...")
    filter_rules = lm_studio.generate_filter_rules(pattern_analysis)
    
    # Combine results
    result = {
        "analysis": pattern_analysis,
        "suggested_filters": filter_rules,
        "metadata": {
            "emails_analyzed": len(email_data),
            "model_used": lm_studio.current_model,
            "timestamp": time.time()
        }
    }
    
    logger.info("LM Studio analysis completed successfully")
    return result

def update_config_from_lm_analysis(analysis_result: Dict, settings_path: str = "config/settings.json") -> bool:
    """Update system configuration based on LM Studio analysis results"""
    
    if not analysis_result:
        logger.warning("No analysis result provided for configuration update")
        return False
    
    try:
        logger.info("Applying LM Studio analysis results to configuration")
        
        # Load current settings
        settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
        
        # Extract categorization results and suggestions
        categorizations = analysis_result.get("categorizations", [])
        metadata = analysis_result.get("metadata", {})
        
        if not categorizations:
            logger.warning("No categorizations found in analysis result")
            return False
        
        # Analyze patterns and update settings
        updates_made = False
        
        # Update sender patterns based on categorizations
        sender_patterns = {}
        category_counts = {}
        
        for item in categorizations:
            category = item.get("category", "UNKNOWN")
            sender = item.get("sender", "")
            
            # Count categories
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Extract domain from sender
            if "@" in sender:
                domain = sender.split("@")[-1].lower()
                if domain not in sender_patterns:
                    sender_patterns[domain] = {}
                sender_patterns[domain][category] = sender_patterns[domain].get(category, 0) + 1
        
        # Find strong sender patterns (domain consistently categorized the same way)
        strong_patterns = {}
        for domain, categories in sender_patterns.items():
            if len(categories) == 1:  # Only one category for this domain
                category = list(categories.keys())[0]
                count = categories[category]
                if count >= 3:  # At least 3 emails from this domain
                    strong_patterns[domain] = category
        
        # Update settings with new patterns
        if strong_patterns:
            if "sender_rules" not in settings:
                settings["sender_rules"] = {}
            
            for domain, category in strong_patterns.items():
                settings["sender_rules"][domain] = {
                    "category": category,
                    "confidence": 0.9,
                    "source": "lm_studio_analysis",
                    "created": datetime.now().isoformat()
                }
                logger.info(f"Added sender rule: {domain} -> {category}")
                updates_made = True
        
        # Update category statistics
        if category_counts:
            settings["last_analysis"] = {
                "timestamp": datetime.now().isoformat(),
                "model_used": metadata.get("model_used", "unknown"),
                "emails_analyzed": metadata.get("emails_analyzed", 0),
                "category_distribution": category_counts
            }
            updates_made = True
        
        # Save updated settings
        if updates_made:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f"Updated configuration with {len(strong_patterns)} new sender rules")
            return True
        else:
            logger.info("No configuration updates needed based on analysis")
            return True
        
    except Exception as e:
        logger.error(f"Failed to update config from LM analysis: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False
def apply_lm_studio_suggestions(suggestions: Dict) -> bool:
    """Applies suggestions from LM Studio analysis."""
    logger.info("Applying LM Studio suggestions")
    # In a real implementation, this would modify configuration files,
    # apply filters to an email service, or take other actions.
    if not suggestions:
        logger.warning("No suggestions provided to apply.")
        return False

    try:
        # Example: Log the suggestions that would be applied
        if "filter_suggestions" in suggestions:
            logger.info(f"Applying {len(suggestions['filter_suggestions'])} filter suggestions.")
            # Here you would have logic to interact with the Gmail API or other services
            # to create the filters.
        
        if "categorization_rules" in suggestions:
            logger.info(f"Applying {len(suggestions['categorization_rules'])} categorization rules.")

        logger.info("Suggestions applied successfully (simulation).")
        return True

    except Exception as e:
        logger.error(f"Failed to apply suggestions: {e}", exc_info=True)
        return False