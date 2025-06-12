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
from tools.backlog_analyzer import analyze_backlog, export_analysis_report

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

def analyze_backlog_first(cleaner, max_analyze=5000):
    """Analyze email backlog to optimize processing strategy."""
    print("\n🔍 Analyzing email backlog to optimize processing...")
    
    try:
        # Run backlog analysis
        analysis = analyze_backlog(
            cleaner.service, 
            query="is:unread in:inbox",
            max_emails=max_analyze
        )
        
        if analysis and analysis['analysis_summary']['total_emails_analyzed'] > 0:
            # Export analysis for reference
            export_analysis_report(analysis, "logs/backlog_analysis.json")
            
            total_analyzed = analysis['analysis_summary']['total_emails_analyzed']
            print(f"📊 Analyzed {total_analyzed} emails from backlog")
            
            # Display top senders
            sender_freq = analysis.get('sender_frequency', {})
            if sender_freq:
                print("\n📈 Top email senders:")
                for i, (sender, count) in enumerate(list(sender_freq.items())[:10], 1):
                    percentage = (count / total_analyzed) * 100
                    print(f"   {i:2d}. {sender[:50]:50} - {count:4d} emails ({percentage:.1f}%)")
            
            # Display suggested batch queries
            batch_suggestions = analysis.get('suggested_batch_queries', [])
            if batch_suggestions:
                print(f"\n💡 Suggested batch processing queries:")
                for i, query in enumerate(batch_suggestions[:5], 1):
                    print(f"   {i}. {query}")
                
                return batch_suggestions
            
        else:
            print("⚠️  No emails found in backlog analysis")
            
    except Exception as e:
        print(f"⚠️  Backlog analysis failed: {e}")
    
    return []

def process_with_strategy(cleaner, batch_suggestions, args):
    """Process emails using optimized strategy based on backlog analysis."""
    print("\n🚀 Starting optimized bulk processing...")
    
    total_stats = {
        'total_found': 0,
        'total_processed': 0,
        'batch_count': 0,
        'errors': 0
    }
    
    start_time = datetime.now()
    
    # Process high-volume senders first if we have suggestions
    if batch_suggestions and not args.skip_analysis:
        print("\n📦 Phase 1: Processing high-volume senders...")
        
        for i, query in enumerate(batch_suggestions[:3], 1):  # Process top 3 suggestions
            print(f"\n🎯 Processing batch {i}: {query}")
            
            try:
                # Create a targeted query that's still unread
                full_query = f"is:unread in:inbox {query}"
                
                # Process this specific sender/pattern
                stats = cleaner.process_email_backlog(
                    batch_size=args.batch_size,
                    older_than_days=0,
                    query_override=full_query,
                    log_callback=log_callback,
                    progress_callback=progress_callback,
                    pause_callback=pause_callback
                )
                
                # Aggregate stats
                total_stats['total_found'] += stats.get('total_found', 0)
                total_stats['total_processed'] += stats.get('total_processed', 0)
                total_stats['batch_count'] += stats.get('batch_count', 0)
                total_stats['errors'] += stats.get('errors', 0)
                
                print(f"   ✅ Batch {i} complete: {stats.get('total_processed', 0)} emails processed")
                
            except Exception as e:
                print(f"   ❌ Batch {i} failed: {e}")
                total_stats['errors'] += 1
                continue
    
    # Process remaining emails
    print("\n📦 Phase 2: Processing remaining emails...")
    
    try:
        stats = cleaner.process_email_backlog(
            batch_size=args.batch_size,
            older_than_days=0,
            log_callback=log_callback,
            progress_callback=progress_callback,
            pause_callback=pause_callback
        )
        
        # Aggregate final stats
        total_stats['total_found'] += stats.get('total_found', 0)
        total_stats['total_processed'] += stats.get('total_processed', 0)
        total_stats['batch_count'] += stats.get('batch_count', 0)
        total_stats['errors'] += stats.get('errors', 0)
        
    except Exception as e:
        print(f"❌ Phase 2 processing failed: {e}")
        total_stats['errors'] += 1
    
    # Display final statistics
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("✅ OPTIMIZED BULK PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"⏱️  Total processing time: {duration}")
    print(f"📊 Total emails found: {total_stats['total_found']}")
    print(f"✅ Total emails processed: {total_stats['total_processed']}")
    print(f"📦 Total batches: {total_stats['batch_count']}")
    print(f"❌ Errors encountered: {total_stats['errors']}")
    
    if total_stats['total_processed'] > 0:
        rate = total_stats['total_processed'] / max(duration.total_seconds(), 1)
        print(f"⚡ Processing rate: {rate:.2f} emails/second")
    
    return total_stats

def main():
    """Main bulk processing function with argument parsing."""
    parser = argparse.ArgumentParser(description="Bulk Email Processor with Backlog Analysis")
    parser.add_argument("--batch-size", type=int, default=50, 
                       help="Batch size for processing (default: 50)")
    parser.add_argument("--analyze-limit", type=int, default=5000,
                       help="Number of emails to analyze for optimization (default: 5000)")
    parser.add_argument("--skip-analysis", action="store_true",
                       help="Skip backlog analysis and use standard processing")
    parser.add_argument("--dry-run", action="store_true",
                       help="Perform analysis only, don't process emails")
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    print("=" * 80)
    print("🚀 Gmail Bulk Email Processor - Enhanced with Backlog Analysis")
    print("=" * 80)
    print(f"📦 Batch size: {args.batch_size}")
    print(f"🔍 Analysis limit: {args.analyze_limit}")
    print(f"🏃 Skip analysis: {args.skip_analysis}")
    print(f"🧪 Dry run: {args.dry_run}")
    
    # Initialize the Gmail cleaner
    cleaner = GmailLMCleaner()
    
    print("\n📧 Connecting to Gmail...")
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
    
    # Analyze backlog first unless skipped
    batch_suggestions = []
    if not args.skip_analysis:
        batch_suggestions = analyze_backlog_first(cleaner, args.analyze_limit)
    
    if args.dry_run:
        print("\n🧪 Dry run complete - no emails were processed")
        return True
    
    # Process with optimized strategy
    stats = process_with_strategy(cleaner, batch_suggestions, args)
    
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