#!/bin/bash

# Gmail Cleaner - Easy Shutdown Script
# This script safely stops the Gmail cleaner and cleans up

echo "🛑 Gmail Intelligent Cleaner - Shutting Down"
echo "============================================"

# Find and kill any running gmail_lm_cleaner processes
echo "🔍 Looking for running Gmail Cleaner processes..."

# Get the process IDs
pids=$(pgrep -f "gmail_lm_cleaner.py")

if [ -z "$pids" ]; then
    echo "ℹ️  No Gmail Cleaner processes found running"
else
    echo "🔄 Found Gmail Cleaner processes: $pids"
    echo "   Sending termination signal..."
    
    # Send SIGTERM first (graceful shutdown)
    kill $pids 2>/dev/null
    
    # Wait a moment for graceful shutdown
    sleep 2
    
    # Check if processes are still running
    still_running=$(pgrep -f "gmail_lm_cleaner.py")
    
    if [ -n "$still_running" ]; then
        echo "⚠️  Processes still running, forcing shutdown..."
        kill -9 $still_running 2>/dev/null
        sleep 1
    fi
    
    # Final check
    final_check=$(pgrep -f "gmail_lm_cleaner.py")
    if [ -z "$final_check" ]; then
        echo "✓ Gmail Cleaner processes stopped successfully"
    else
        echo "❌ Some processes may still be running. Try running this script again."
        exit 1
    fi
fi

# Clean up temporary files if any exist
echo "🧹 Cleaning up temporary files..."

temp_files=(
    "*.tmp"
    "*.log"
    "__pycache__"
    "*.pyc"
)

cleaned_any=false
for pattern in "${temp_files[@]}"; do
    if ls $pattern 1> /dev/null 2>&1; then
        rm -rf $pattern
        echo "   Removed: $pattern"
        cleaned_any=true
    fi
done

if [ "$cleaned_any" = false ]; then
    echo "   No temporary files to clean"
fi

# Display status
echo ""
echo "📊 Current Status:"
if [ -f "config/settings.json" ]; then
    echo "   ✓ Settings file preserved: config/settings.json"
else
    echo "   ℹ️  No settings file found"
fi

if [ -f "config/token.json" ]; then
    echo "   ✓ Authentication token preserved: config/token.json"
else
    echo "   ℹ️  No authentication token found"
fi

if [ -f "config/credentials.json" ]; then
    echo "   ✓ Gmail credentials preserved: config/credentials.json"
else
    echo "   ⚠️  No Gmail credentials found"
fi

echo ""
echo "✅ Gmail Cleaner shutdown complete"
echo "   Your settings and authentication are preserved"
echo "   Run ./start.sh to start again"