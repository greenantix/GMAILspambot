#!/usr/bin/env python3
"""
Bulk Email Processor - Command Line Version
Designed to process large volumes of emails (75k+) efficiently without GUI
"""

import os
import sys
import time
import logging
from datetime import datetime
from gmail_lm_cleaner import GmailLMCleaner
from log_config import init_logging

def setup_logging():
    """Initialize logging for bulk processing."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    init_logging(
        log_level=logging.INFO,
        log_dir=log_dir,
        log_file_name="bulk_processing.log"
    )
    return logging.getLogger("BulkProcessor")

def progress_callback(processed, total):
    """Progress callback for batch processing."""
    if total > 0:
        percentage = (processed / total) * 100
        print(f"Progress: {processed}/{total} ({percentage:.1f}%)")
    else:
        print(f"Processed: {processed} emails")

def log_callback(message):
    """Log callback for batch processing."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def pause_callback():
    """Check if processing should be paused (always return False for autonomous processing)."""
    return False

def main():
    """Main bulk processing function."""
    logger = setup_logging()
    
    print("=" * 80)
    print("🚀 Gmail Bulk Email Processor - Starting 75k Email Cleanup")
    print("=" * 80)
    
    # Initialize the Gmail cleaner
    cleaner = GmailLMCleaner()
    
    print("📧 Connecting to Gmail...")
    if not cleaner.ensure_gmail_connection():
        print("❌ Failed to connect to Gmail. Check authentication.")
        return False
    
    print("✅ Gmail connection established!")
    
    # Get email count first
    try:
        inbox_label = cleaner.service.users().labels().get(userId='me', id='INBOX').execute()
        total_unread = inbox_label.get('messagesUnread', 0)
        print(f"📊 Found {total_unread} unread emails in inbox")
    except Exception as e:
        print(f"⚠️ Could not get exact count: {e}")
        total_unread = 0
    
    # Start processing with optimized settings
    print("\n🔥 Starting bulk processing with filter-first strategy...")
    print("💡 Emails will be pre-processed by existing Gmail filters")
    print("🤖 Remaining emails will be analyzed by LLM")
    print("📊 Processing in batches of 200 for optimal performance")
    
    start_time = datetime.now()
    
    try:
        # Process all unread emails with smaller batch size for stability
        stats = cleaner.process_email_backlog(
            batch_size=50,  # Smaller batch size for stability
            older_than_days=0,  # Process ALL unread emails
            log_callback=log_callback,
            progress_callback=progress_callback,
            pause_callback=pause_callback
        )
        
        # Display final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("✅ BULK PROCESSING COMPLETE!")
        print("=" * 80)
        print(f"⏱️  Total processing time: {duration}")
        print(f"📊 Total emails found: {stats['total_found']}")
        print(f"✅ Total emails processed: {stats['total_processed']}")
        print(f"📦 Total batches: {stats['batch_count']}")
        print(f"❌ Errors encountered: {stats['errors']}")
        
        if stats['by_category']:
            print("\n📂 Processing breakdown by category:")
            for category, count in stats['by_category'].items():
                print(f"   {category}: {count} emails")
        
        # Calculate processing rate
        if duration.total_seconds() > 0:
            rate = stats['total_processed'] / duration.total_seconds()
            print(f"\n⚡ Processing rate: {rate:.1f} emails/second")
        
        print(f"\n📝 Detailed logs available in: logs/bulk_processing.log")
        
        # Show inbox status
        try:
            inbox_label_after = cleaner.service.users().labels().get(userId='me', id='INBOX').execute()
            remaining_unread = inbox_label_after.get('messagesUnread', 0)
            print(f"📬 Remaining unread emails: {remaining_unread}")
            
            if remaining_unread == 0:
                print("🎉 INBOX ZERO ACHIEVED! 🎉")
            elif total_unread > 0:
                processed_percentage = ((total_unread - remaining_unread) / total_unread) * 100
                print(f"📈 Cleanup progress: {processed_percentage:.1f}%")
        except Exception as e:
            print(f"⚠️ Could not check final inbox status: {e}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Processing interrupted by user")
        print("📊 Partial statistics available in logs")
        return False
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        logger.exception("Bulk processing failed")
        return False

if __name__ == "__main__":
    print("🤖 Gmail Bulk Processor - Autonomous Mode")
    print("🛡️  All emails will be processed according to configured rules")
    print("📧 Critical emails will be preserved in INBOX")
    print("⚡ Filter-first strategy will handle most emails efficiently")
    print("🚀 Starting in 3 seconds...")
    
    # Give a moment to cancel if needed
    time.sleep(3)
    
    success = main()
    
    if success:
        print("\n✅ Bulk processing completed successfully!")
        print("📱 You can check your email to see the cleaned inbox")
    else:
        print("\n❌ Bulk processing failed or was interrupted")
        print("🔍 Check logs for details")
    
    print("\n👋 Bulk processor finished. Have a great sleep! 😴")