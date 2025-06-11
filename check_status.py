#!/usr/bin/env python3
"""
Quick Status Checker for Gmail Processing
Shows current progress and system status
"""

import subprocess
import os
from datetime import datetime
from gmail_api_utils import get_gmail_service

def get_process_status():
    """Check if bulk processor is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'bulk_processor.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            return f"✅ Running (PID: {pid})"
        else:
            return "❌ Not running"
    except:
        return "❓ Unknown"

def get_gmail_status():
    """Get current Gmail inbox status."""
    try:
        service = get_gmail_service()
        if service:
            inbox = service.users().labels().get(userId='me', id='INBOX').execute()
            unread = inbox.get('messagesUnread', 0)
            return f"📧 {unread:,} unread emails remaining"
        else:
            return "❌ Cannot connect to Gmail"
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}..."

def get_processing_stats():
    """Get processing statistics from logs."""
    try:
        if os.path.exists('logs/email_processing.log'):
            with open('logs/email_processing.log', 'r') as f:
                lines = f.readlines()
            
            processed_count = sum(1 for line in lines if 'Processed:' in line)
            
            # Get latest processing time
            for line in reversed(lines):
                if 'Processed:' in line:
                    timestamp = line.split()[0:2]
                    latest_time = ' '.join(timestamp)
                    break
            else:
                latest_time = "No recent activity"
            
            return f"📊 {processed_count:,} emails processed | Last: {latest_time}"
        else:
            return "📊 No processing logs found"
    except Exception as e:
        return f"📊 Error reading logs: {str(e)[:30]}..."

def main():
    """Display complete status."""
    print("=" * 60)
    print("📈 Gmail Intelligent Cleaner - Status Report")
    print("=" * 60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🤖 Bulk Processor:")
    print(f"   {get_process_status()}")
    print()
    
    print("📧 Gmail Status:")
    print(f"   {get_gmail_status()}")
    print()
    
    print("📊 Processing Stats:")
    print(f"   {get_processing_stats()}")
    print()
    
    # Check log file sizes
    log_files = ['logs/email_processing.log', 'logs/bulk_processing.log']
    print("📝 Log Files:")
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file) / 1024 / 1024  # MB
            print(f"   {log_file}: {size:.1f} MB")
        else:
            print(f"   {log_file}: Not found")
    
    print()
    print("🔧 Commands:")
    print("   Monitor:     tail -f logs/email_processing.log")
    print("   Progress:    python progress_monitor.py")
    print("   Start GUI:   ./start_stable.sh")
    print("   Stop:        pkill -f bulk_processor")
    print("=" * 60)

if __name__ == "__main__":
    main()