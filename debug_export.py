#!/usr/bin/env python3
"""
Debug Email Export - Find out why export is empty
"""

import os
import json
from datetime import datetime, timedelta
from gmail_lm_cleaner import GmailLMCleaner

def debug_export():
    print("🔍 Debug Email Export")
    print("=" * 30)
    
    try:
        # Initialize Gmail cleaner
        print("🔑 Connecting to Gmail...")
        cleaner = GmailLMCleaner()
        print("✅ Connected successfully")
        
        # Try different queries to see what works
        queries_to_test = [
            ('in:inbox', 'All inbox emails'),
            ('in:inbox after:2024/01/01', 'Inbox emails from 2024'),
            ('in:inbox after:2024/12/01', 'Inbox emails from December 2024'),
            ('after:2024/12/01', 'All emails from December 2024'),
            ('newer_than:7d', 'Emails from last 7 days'),
            ('newer_than:30d', 'Emails from last 30 days')
        ]
        
        for query, description in queries_to_test:
            print(f"\n📧 Testing query: {query} ({description})")
            
            try:
                results = cleaner.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=10
                ).execute()
                
                messages = results.get('messages', [])
                count = results.get('resultSizeEstimate', 0)
                
                print(f"   Found: {len(messages)} messages (estimated total: {count})")
                
                if messages:
                    # Get first message details
                    msg = cleaner.get_email_content(messages[0]['id'])
                    if msg:
                        print(f"   Sample: {msg['subject'][:50]}...")
                        print(f"   From: {msg['sender'][:50]}...")
                        print(f"   Date: {msg['date']}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Check what the original export function was using
        print(f"\n🔍 Original export settings:")
        days_back = 30
        date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        original_query = f'in:inbox after:{date_after}'
        print(f"   Query: {original_query}")
        print(f"   Date cutoff: {date_after}")
        
        # Test the specific query
        print(f"\n📧 Testing original query...")
        try:
            results = cleaner.service.users().messages().list(
                userId='me',
                q=original_query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            print(f"   Found: {len(messages)} messages")
            
            if messages:
                print(f"   Exporting first 5 subjects:")
                for i, msg in enumerate(messages[:5], 1):
                    email_data = cleaner.get_email_content(msg['id'])
                    if email_data:
                        print(f"   {i}. {email_data['subject']}")
            else:
                print("   No messages found with this query")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == '__main__':
    debug_export()