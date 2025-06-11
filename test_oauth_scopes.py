#!/usr/bin/env python3
"""
Test script to verify OAuth scopes after re-authentication
"""

import os
from gmail_lm_cleaner import GmailLMCleaner, SCOPES

def test_oauth_scopes():
    print("🔐 OAuth Scope Test")
    print("=" * 50)
    
    print(f"📋 Required scopes:")
    for scope in SCOPES:
        print(f"   ✅ {scope}")
    
    print(f"\n📁 Token file: {'EXISTS' if os.path.exists('config/token.json') else 'DELETED (will force re-auth)'}")
    
    try:
        print(f"\n🔄 Initializing Gmail client...")
        cleaner = GmailLMCleaner()
        
        print(f"✅ Gmail service created successfully!")
        print(f"📧 Ready to test filter creation with both scopes")
        
        # Test basic Gmail access
        try:
            profile = cleaner.service.users().getProfile(userId='me').execute()
            print(f"📬 Gmail access confirmed: {profile.get('emailAddress', 'Unknown')}")
        except Exception as e:
            print(f"⚠️ Gmail access issue: {e}")
        
        # Test filter access (this will fail with 403 if scope is missing)
        try:
            filters = cleaner.service.users().settings().filters().list(userId='me').execute()
            filter_count = len(filters.get('filter', []))
            print(f"🔧 Filter access confirmed: {filter_count} existing filters")
            print(f"✅ Both scopes are working correctly!")
        except Exception as e:
            error_msg = str(e)
            if '403' in error_msg:
                print(f"❌ Filter access denied - scope issue")
                print(f"💡 Need to re-authenticate with gmail.settings.basic scope")
            else:
                print(f"⚠️ Filter access issue: {e}")
        
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        if "invalid_scope" in str(e):
            print(f"💡 Check that both scopes are properly configured in Google Cloud Console")

if __name__ == "__main__":
    test_oauth_scopes()