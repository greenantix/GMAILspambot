#!/bin/bash

# Stable Gmail Cleaner Startup Script
# Handles segfaults and memory issues gracefully

echo "🚀 Starting Gmail Cleaner with stability improvements..."

# Set memory and threading environment variables
export PYTHONHASHSEED=0
export PYTHONMALLOC=malloc
export MALLOC_CHECK_=0

# Increase stack size
ulimit -s 16384

# Function to start GUI with retry
start_gui() {
    local attempt=1
    local max_attempts=3
    
    while [ $attempt -le $max_attempts ]; do
        echo "🖥️  Starting GUI (attempt $attempt/$max_attempts)..."
        
        # Run with error handling
        python3 gmail_lm_cleaner.py 2>&1 | tee -a logs/gui_session.log
        
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "✅ GUI closed normally"
            break
        elif [ $exit_code -eq 139 ]; then
            echo "💥 Segmentation fault detected (exit code $exit_code)"
            echo "🔄 Attempting to restart GUI..."
            
            # Clean up any hanging processes
            pkill -f "python.*gmail_lm_cleaner"
            sleep 2
            
            # Try with different display settings
            export QT_X11_NO_MITSHM=1
            export GDK_SYNCHRONIZE=1
            
            ((attempt++))
        else
            echo "❌ GUI exited with code $exit_code"
            break
        fi
        
        if [ $attempt -le $max_attempts ]; then
            echo "⏳ Waiting 5 seconds before retry..."
            sleep 5
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ GUI failed to start after $max_attempts attempts"
        echo "💡 You can still monitor processing with:"
        echo "   tail -f logs/email_processing.log"
        echo "   python progress_monitor.py"
        return 1
    fi
}

# Check if bulk processor is running
if pgrep -f "bulk_processor.py" > /dev/null; then
    echo "✅ Bulk processor is already running"
    echo "📊 Current processing status:"
    python3 -c "
from gmail_api_utils import get_gmail_service
try:
    service = get_gmail_service()
    if service:
        inbox = service.users().labels().get(userId='me', id='INBOX').execute()
        print(f'   📧 Unread emails remaining: {inbox.get(\"messagesUnread\", \"Unknown\")}')
    else:
        print('   ⚠️  Could not connect to Gmail')
except Exception as e:
    print(f'   ❌ Error checking status: {e}')
"
else
    echo "⚠️  Bulk processor is not running"
    echo "🚀 Starting bulk processor in background..."
    nohup python3 bulk_processor.py > "bulk_processing_$(date +%H%M).log" 2>&1 &
    echo "✅ Bulk processor started"
fi

echo ""
echo "🖥️  Starting GUI interface..."

# Start the GUI
start_gui

echo ""
echo "👋 Gmail Cleaner session ended"
echo "📊 Processing continues in background if bulk processor is running"
echo ""
echo "📋 Useful commands:"
echo "   📈 Monitor progress:    python progress_monitor.py"
echo "   📝 Check logs:         tail -f logs/email_processing.log"
echo "   🔄 Restart GUI:        python gmail_lm_cleaner.py"
echo "   ⏹️  Stop processing:    pkill -f bulk_processor"
echo ""