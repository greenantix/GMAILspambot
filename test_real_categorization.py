#!/usr/bin/env python3
"""
Test LM Studio categorization with real email data
"""

import sys
from pathlib import Path
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from lm_studio_integration import lm_studio

def parse_email_subjects(file_path):
    """Parse the email_subjects.txt file"""
    emails = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find email entries using regex
        email_pattern = r'\d+\.\s+Subject:\s+(.+?)\n\s+From:\s+(.+?)\n'
        matches = re.findall(email_pattern, content)
        
        for subject, sender in matches[:10]:  # Test with first 10 emails
            emails.append({
                'subject': subject.strip(),
                'sender': sender.strip()
            })
    
    except Exception as e:
        print(f"Error parsing emails: {e}")
        return []
    
    return emails

def test_categorization():
    """Test email categorization with real data"""
    
    # Check LM Studio connection
    if not lm_studio.is_server_running():
        print("❌ LM Studio is not running. Please start LM Studio first.")
        return
    
    print("✅ LM Studio is running")
    print(f"🧠 Current model: {lm_studio.get_loaded_model()}")
    print()
    
    # Parse email data
    email_file = Path("email_subjects.txt")
    if not email_file.exists():
        print("❌ email_subjects.txt not found. Please export emails first.")
        return
    
    emails = parse_email_subjects(email_file)
    if not emails:
        print("❌ No emails found in file")
        return
    
    print(f"📧 Loaded {len(emails)} emails for testing")
    print()
    
    # Extract subjects and senders
    subjects = [email['subject'] for email in emails]
    senders = [email['sender'] for email in emails]
    
    # Test categorization
    print("🔍 Testing email categorization...")
    results = lm_studio.categorize_emails_batch(subjects, senders)
    
    if results:
        print("✅ Categorization successful!")
        print()
        
        for i, result in enumerate(results):
            if i < len(emails):
                email = emails[i]
                index = result.get('index', i + 1)
                category = result.get('category', 'UNKNOWN')
                
                print(f"📧 Email {index}:")
                print(f"   Subject: {email['subject'][:60]}...")
                print(f"   From: {email['sender']}")
                print(f"   → Category: {category}")
                print()
    else:
        print("❌ Categorization failed")

if __name__ == "__main__":
    test_categorization()