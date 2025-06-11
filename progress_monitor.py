#!/usr/bin/env python3
"""
Progress Monitor for Bulk Email Processing
Shows real-time progress and statistics
"""

import time
import os
from datetime import datetime
from collections import defaultdict

def monitor_progress():
    """Monitor the bulk processing progress."""
    log_file = "logs/bulk_processing.log"
    
    if not os.path.exists(log_file):
        print("No log file found. Bulk processing may not be running.")
        return
    
    print("📊 Gmail Bulk Processing Monitor")
    print("=" * 50)
    
    stats = defaultdict(int)
    last_size = 0
    start_time = datetime.now()
    
    while True:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Count categorizations
            stats.clear()
            for line in content.split('\n'):
                if 'Decision:' in line:
                    for category in ['INBOX', 'SHOPPING', 'SOCIAL', 'NEWSLETTERS', 'PRIORITY', 'BILLS', 'PERSONAL', 'JUNK']:
                        if f'Decision: {category}' in line:
                            stats[category] += 1
                            break
            
            # Calculate totals
            total_processed = sum(stats.values())
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            if total_processed > 0:
                rate = total_processed / elapsed.total_seconds()
                
                # Clear screen and show stats
                os.system('clear')
                print("📊 Gmail Bulk Processing Monitor")
                print("=" * 50)
                print(f"⏱️  Running time: {elapsed}")
                print(f"📧 Total processed: {total_processed:,}")
                print(f"⚡ Processing rate: {rate:.1f} emails/second")
                print(f"📈 Est. time remaining: {(60168 - total_processed) / rate / 3600:.1f} hours")
                print("\n📂 Category Breakdown:")
                
                for category, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                    if count > 0:
                        percentage = (count / total_processed) * 100
                        print(f"   {category:12}: {count:4,} ({percentage:5.1f}%)")
                
                print(f"\n📈 Progress: {(total_processed/60168)*100:.1f}% complete")
                print("🔄 Refreshing in 30 seconds... (Ctrl+C to exit)")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_progress()