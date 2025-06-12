#!/usr/bin/env python3
"""
Bulk Email Processor - Command Line Version
Designed to process large volumes of emails (75k+) efficiently without GUI
Enhanced with backlog analysis and optimized processing strategies
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from gmail_lm_cleaner import GmailLMCleaner
from log_config import init_logging
from tools.filter_harvester import apply_existing_filters_to_backlog, fetch_and_parse_filters
from exceptions import GmailAPIError, EmailProcessingError, LLMConnectionError


def run_server_side_filter_pass(cleaner, log_callback):
    """
    Phase 1: Apply all existing user filters on the server side.
    """
    log_callback("🚀 Phase 1: Starting server-side filter pass...")
    
    try:
        stats = apply_existing_filters_to_backlog(
            cleaner.service,
            progress_callback=lambda msg, prog: log_callback(f"Filter Progress: {msg} ({prog:.0f}%)")
        )
        
        processed_count = stats.get('server_side_processed', 0)
        filter_stats = stats.get('filter_stats', {})
        
        log_callback(f"✅ Server-side filtering complete. Processed {processed_count} emails across {len(filter_stats)} filters.")
        
        if filter_stats:
            log_callback("📊 Filter Application Stats:")
            # Fetch filter details to show human-readable queries
            all_filters = fetch_and_parse_filters(cleaner.service)
            filter_map = {f['id']: f for f in all_filters}
            
            for filter_id, count in filter_stats.items():
                filter_details = filter_map.get(filter_id)
                query_str = f"'{filter_details['query']}'" if filter_details else f"ID: {filter_id}"
                log_callback(f"  - Filter {query_str} processed {count} emails.")

        # Determine which labels were applied to exclude them in the next phase
        applied_labels = set()
        all_filters = fetch_and_parse_filters(cleaner.service)
        for filter_data in all_filters:
            if filter_data['id'] in filter_stats:
                # Add labels from the action to our set
                if 'add_labels' in filter_data['action']:
                    for label_name in filter_data['action']['add_labels']:
                        applied_labels.add(label_name)

        return stats, list(applied_labels)

    except GmailAPIError as e:
        log_callback(f"❌ Gmail API Error during server-side filtering: {e}")
    except Exception as e:
        log_callback(f"❌ An unexpected error occurred during server-side filtering: {e}")
        
    return {"server_side_processed": 0, "filter_stats": {}}, []


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
    """Main bulk processing function with argument parsing."""
    parser = argparse.ArgumentParser(description="Bulk Email Processor with Server-Side Filtering")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Batch size for LLM processing (default: 50)")
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    print("=" * 80)
    print("🚀 Gmail Bulk Email Processor - Server-Side Filtering Edition")
    print("=" * 80)
    print(f"📦 LLM Batch size: {args.batch_size}")
    
    # Initialize the Gmail cleaner
    cleaner = GmailLMCleaner()
    
    print("\n📧 Connecting to Gmail...")
    if not cleaner.ensure_gmail_connection():
        log_callback("❌ Failed to connect to Gmail. Check authentication.")
        return False
    
    log_callback("✅ Gmail connection established!")
    
    # Get initial email count
    try:
        inbox_label = cleaner.service.users().labels().get(userId='me', id='INBOX').execute()
        total_unread = inbox_label.get('messagesUnread', 0)
        log_callback(f"📊 Found {total_unread} unread emails in inbox before processing.")
    except Exception as e:
        log_callback(f"⚠️ Could not get initial email count: {e}")
        total_unread = 0

    start_time = datetime.now()

    # Phase 1: Server-Side Filtering
    server_stats, applied_labels = run_server_side_filter_pass(cleaner, log_callback)
    
    # Phase 2: LLM processing for the remainder
    log_callback("\n🚀 Phase 2: Starting LLM processing for remaining emails...")
    
    # Construct a query to exclude emails that have already been processed by filters
    exclusion_query = "is:unread in:inbox"
    if applied_labels:
        # Create -label:LabelName for each label applied
        label_exclusions = [f"-label:{label.replace(' ', '-')}" for label in applied_labels]
        exclusion_query += " " + " ".join(label_exclusions)
        log_callback(f"🧠 LLM will process emails NOT matching labels: {', '.join(applied_labels)}")
    else:
        log_callback("🧠 No labels were applied in Phase 1. LLM will process all unread emails.")
        
    log_callback(f"🔍 Using query for LLM processing: {exclusion_query}")

    llm_stats = {}
    try:
        llm_stats = cleaner.process_email_backlog(
            batch_size=args.batch_size,
            older_than_days=0, # Process all regardless of age
            query_override=exclusion_query,
            log_callback=log_callback,
            progress_callback=progress_callback,
            pause_callback=pause_callback
        )
        log_callback("✅ LLM processing complete.")
    except (GmailAPIError, EmailProcessingError, LLMConnectionError) as e:
        log_callback(f"❌ LLM processing failed ({e.__class__.__name__}): {e}")
    except Exception as e:
        log_callback(f"❌ An unexpected error occurred during LLM processing: {e}")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    total_server_processed = server_stats.get('server_side_processed', 0)
    total_llm_processed = llm_stats.get('total_processed', 0)
    total_processed = total_server_processed + total_llm_processed

    print("\n" + "=" * 80)
    print("✅ BULK PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"⏱️  Total processing time: {duration}")
    print(f"📊 Total emails processed: {total_processed}")
    print(f"  - Server-side filters: {total_server_processed}")
    print(f"  - LLM processing: {total_llm_processed}")
    
    if total_processed > 0:
        rate = total_processed / max(duration.total_seconds(), 1)
        print(f"⚡ Processing rate: {rate:.2f} emails/second")

    print(f"\n📝 Detailed logs available in: logs/bulk_processing.log")
    
    # Show final inbox status
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

if __name__ == "__main__":
    try:
        print("🤖 Gmail Bulk Processor - Enhanced with Backlog Analysis")
        print("🛡️  All emails will be processed according to configured rules")
        print("📧 Critical emails will be preserved in INBOX")
        print("⚡ Optimized processing with targeted batch strategies")
        print("🚀 Starting...")
        
        success = main()
        
        if success:
            print("\n✅ Bulk processing completed successfully!")
            print("📱 You can check your email to see the cleaned inbox")
        else:
            print("\n❌ Bulk processing failed or was interrupted")
            print("🔍 Check logs for details")
            
    except KeyboardInterrupt:
        print("\n\n⏸️ Processing interrupted by user")
        print("📊 Partial statistics available in logs")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Bulk processing failed with fatal error")
    
    print("\n👋 Bulk processor finished. Have a great sleep! 😴")