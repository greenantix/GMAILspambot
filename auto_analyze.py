#!/usr/bin/env python3
"""
Automatic Email Analysis with Gemini
Exports email subjects and uses Gemini to generate filtering rules
"""

import sys
import argparse
from gmail_lm_cleaner import GmailLMCleaner, GEMINI_API_KEY

def main():
    parser = argparse.ArgumentParser(description='Auto-analyze Gmail with Gemini')
    parser.add_argument('--max-emails', type=int, default=1000, 
                       help='Maximum number of emails to analyze (default: 1000)')
    parser.add_argument('--days-back', type=int, default=30,
                       help='Number of days back to search (default: 30)')
    
    args = parser.parse_args()
    
    print("🤖 Gmail Auto-Analyzer with Gemini")
    print("=" * 40)
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in .env file")
        print("Create a .env file with your Gemini API key:")
        print("GEMINI_API_KEY=your_api_key_here")
        print("\nGet your API key from: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    try:
        # Initialize Gmail cleaner
        print("🔑 Connecting to Gmail...")
        cleaner = GmailLMCleaner()
        
        # Export and analyze
        cleaner.export_and_analyze(
            max_emails=args.max_emails,
            days_back=args.days_back
        )
        
        print(f"\n🎯 Next steps:")
        print(f"1. Your filtering rules have been automatically updated")
        print(f"2. Run the Gmail cleaner to test the new filters")
        print(f"3. Adjust settings manually if needed")
        
    except KeyboardInterrupt:
        print("\n👋 Analysis cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()