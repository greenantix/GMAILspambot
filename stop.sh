#!/bin/bash

# Gmail Cleaner - Easy Shutdown Script
# This script safely stops the Gmail cleaner and cleans up all processes

echo "🛑 Gmail Intelligent Cleaner - Shutting Down"
echo "============================================"

# Use PID files for graceful shutdown when available
echo "🔍 Stopping processes using PID files..."

# Function to stop process using PID file with fallback to process name
stop_process_with_fallback() {
    local process_name="$1"
    local script_pattern="$2"
    
    # Check if PID file exists
    if [ -f "pids/${process_name}.pid" ]; then
        pid=$(cat "pids/${process_name}.pid" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "   Found ${process_name} via PID file (PID: $pid) - stopping gracefully..."
            kill -TERM "$pid" 2>/dev/null
            
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo "   ✅ ${process_name} stopped gracefully"
                    rm -f "pids/${process_name}.pid" 2>/dev/null
                    return 0
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "   ⚠️  Force killing ${process_name}..."
                kill -KILL "$pid" 2>/dev/null
                sleep 1
                rm -f "pids/${process_name}.pid" 2>/dev/null
            fi
        else
            echo "   ℹ️  Stale PID file for ${process_name}, cleaning up..."
            rm -f "pids/${process_name}.pid" 2>/dev/null
        fi
    fi
    
    # Fallback to process search if PID file method didn't work
    fallback_pids=$(pgrep -f "$script_pattern" 2>/dev/null)
    if [ -n "$fallback_pids" ]; then
        echo "   Found ${process_name} via process search (PID: $fallback_pids) - stopping..."
        kill -TERM $fallback_pids 2>/dev/null
        sleep 2
        
        # Force kill if still running
        still_running=$(pgrep -f "$script_pattern" 2>/dev/null)
        if [ -n "$still_running" ]; then
            echo "   ⚠️  Force killing remaining ${process_name} processes..."
            kill -KILL $still_running 2>/dev/null
            sleep 1
        fi
        echo "   ✅ ${process_name} stopped"
    else
        echo "   ℹ️  No ${process_name} processes running"
    fi
}

# Stop bulk processor first (prevents new LM Studio requests)
echo "🔍 Stopping bulk processor..."
stop_process_with_fallback "bulk_processor" "bulk_processor.py"

# Stop autonomous runner
echo "🔍 Stopping autonomous runner..."
stop_process_with_fallback "autonomous_runner" "autonomous_runner.py"

# Find and kill any other Gmail cleaner processes
echo "🔍 Looking for other Gmail Cleaner processes..."
other_pids=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)

if [ -n "$other_pids" ]; then
    echo "🔄 Found other Gmail Cleaner processes: $other_pids"
    echo "   Sending termination signal..."
    
    # Send SIGTERM first (graceful shutdown)
    kill -TERM $other_pids 2>/dev/null
    
    # Wait a moment for graceful shutdown
    sleep 3
    
    # Check if processes are still running
    still_running=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)
    
    if [ -n "$still_running" ]; then
        echo "⚠️  Processes still running, forcing shutdown..."
        kill -KILL $still_running 2>/dev/null
        sleep 1
    fi
    
    # Final check
    final_check=$(pgrep -f "gmail_lm_cleaner.py" 2>/dev/null)
    if [ -z "$final_check" ]; then
        echo "✓ Other Gmail Cleaner processes stopped successfully"
    else
        echo "❌ Some processes may still be running. Try running this script again."
        exit 1
    fi
else
    echo "ℹ️  No other Gmail Cleaner processes found running"
fi

# Clean up LM Studio processes and backlog
echo "🤖 Cleaning up LM Studio processes..."

# Check if LM Studio is running
lm_processes=$(pgrep -f "lmstudio\|llama\|llamacpp" 2>/dev/null || true)

if [ -n "$lm_processes" ]; then
    echo "   Found LM Studio processes: $lm_processes"
    
    # Graceful shutdown first
    echo "   Sending termination signal to LM Studio..."
    pkill -f "lmstudio" 2>/dev/null || true
    pkill -f "llama" 2>/dev/null || true
    pkill -f "llamacpp" 2>/dev/null || true
    
    sleep 3
    
    # Force kill if still running
    if pgrep -f "lmstudio\|llama\|llamacpp" > /dev/null 2>&1; then
        echo "   Force stopping LM Studio processes..."
        killall -9 lmstudio 2>/dev/null || true
        killall -9 lmstudio-cli 2>/dev/null || true
        killall -9 llama-server 2>/dev/null || true
        killall -9 llamacpp 2>/dev/null || true
        pkill -9 -f "lmstudio" 2>/dev/null || true
        pkill -9 -f "llama" 2>/dev/null || true
        sleep 2
    fi
    
    # Final verification
    remaining=$(pgrep -f "lmstudio\|llama\|llamacpp" 2>/dev/null || true)
    if [ -z "$remaining" ]; then
        echo "   ✅ LM Studio processes stopped successfully"
    else
        echo "   ⚠️  Some LM Studio processes may still be running: $remaining"
    fi
else
    echo "   ℹ️  No LM Studio processes found"
fi

# Test LM Studio API status
echo "🔍 Checking LM Studio API status..."
if command -v curl > /dev/null 2>&1; then
    api_response=$(curl -s --connect-timeout 2 http://localhost:1234/v1/models 2>/dev/null || echo "offline")
    if [[ "$api_response" == *"offline"* ]] || [[ "$api_response" == "" ]]; then
        echo "   ✅ LM Studio API is offline"
    else
        echo "   ⚠️  LM Studio API may still be responding"
        echo "   💡 You may need to manually stop LM Studio app"
    fi
else
    echo "   ℹ️  curl not available, cannot test API status"
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
echo "   • Gmail Cleaner processes stopped"
echo "   • Bulk processor stopped"  
echo "   • LM Studio processes cleaned up"
echo "   • Your settings and authentication are preserved"
echo ""
echo "🚀 To restart:"
echo "   ./start.sh        - Start with current settings"
echo "   ./start_stable.sh - Start with stability improvements"
echo ""
echo "🧪 Before restarting LM Studio:"
echo "   python test_lm_studio.py - Test LM Studio connectivity"