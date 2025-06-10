#!/usr/bin/env python3
"""
Standalone Email Subjects Exporter
Exports email subjects and senders for analysis by Gemini or other LLMs
"""

import sys
import argparse
from gmail_lm_cleaner import GmailLMCleaner

def main():
    parser = argparse.ArgumentParser(description='Export Gmail subjects for analysis')
    parser.add_argument('--max-emails', type=int, default=1000, 
                       help='Maximum number of emails to export (default: 1000)')
    parser.add_argument('--days-back', type=int, default=30,
                       help='Number of days back to search (default: 30)')
    parser.add_argument('--output', type=str, default='email_subjects.txt',
                       help='Output file name (default: email_subjects.txt)')
    
    args = parser.parse_args()
    
    print("📧 Gmail Subjects Exporter")
    print("=" * 40)
    
    try:
        # Initialize Gmail cleaner
        print("🔑 Connecting to Gmail...")
        cleaner = GmailLMCleaner()
        
        # Export subjects
        cleaner.export_subjects(
            max_emails=args.max_emails,
            days_back=args.days_back, 
            output_file=args.output
        )
        
        print(f"\n🎯 Next steps:")
        print(f"1. Upload '{args.output}' to Gemini")
        print(f"2. Ask Gemini to analyze and create filtering rules")
        print(f"3. Update your Gmail cleaner settings with the recommendations")
        
    except KeyboardInterrupt:
        print("\n👋 Export cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()