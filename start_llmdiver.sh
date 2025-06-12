#!/bin/bash
# LLMdiver Daemon Startup Script

DAEMON_SCRIPT="llmdiver_daemon.py"
PID_FILE="llmdiver.pid"
LOG_FILE="llmdiver_daemon.log"

start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "LLMdiver daemon is already running (PID: $PID)"
            return 1
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "Starting LLMdiver daemon..."
    
    # Check dependencies
    if ! command -v repomix &> /dev/null; then
        echo "❌ Error: repomix not found. Install with: npm install -g repomix"
        exit 1
    fi
    
    if ! python3 -c "import git, watchdog" 2>/dev/null; then
        echo "❌ Error: Missing Python dependencies. Install with: pip install gitpython watchdog"
        exit 1
    fi
    
    # Check LM Studio
    if ! curl -s http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
        echo "⚠️  Warning: LM Studio not accessible at http://127.0.0.1:1234"
        echo "   Make sure LM Studio is running with API enabled"
    fi
    
    # Create config directory
    mkdir -p config
    
    # Start daemon in background
    nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ LLMdiver daemon started successfully (PID: $PID)"
        echo "📋 Log file: $LOG_FILE"
        echo "🔍 Monitor with: tail -f $LOG_FILE"
        return 0
    else
        echo "❌ Failed to start daemon"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "LLMdiver daemon is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo "Stopping LLMdiver daemon (PID: $PID)..."
    
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Force killing daemon..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ LLMdiver daemon stopped"
    else
        echo "Daemon was not running, removing PID file"
        rm -f "$PID_FILE"
    fi
}

status_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ LLMdiver daemon is running (PID: $PID)"
            
            # Show recent log entries
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "📋 Recent log entries:"
                tail -n 5 "$LOG_FILE"
            fi
            
            # Show analysis files
            if [ -d ".llmdiver" ]; then
                echo ""
                echo "📁 Recent analyses:"
                ls -lt .llmdiver/*.md 2>/dev/null | head -n 3
            fi
            
            return 0
        else
            echo "❌ LLMdiver daemon is not running (stale PID file)"
            return 1
        fi
    else
        echo "❌ LLMdiver daemon is not running"
        return 1
    fi
}

restart_daemon() {
    stop_daemon
    sleep 1
    start_daemon
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found"
    fi
}

case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the LLMdiver daemon"
        echo "  stop    - Stop the LLMdiver daemon"
        echo "  restart - Restart the LLMdiver daemon"
        echo "  status  - Show daemon status and recent activity"
        echo "  logs    - Show live daemon logs"
        echo ""
        echo "Examples:"
        echo "  ./start_llmdiver.sh start"
        echo "  ./start_llmdiver.sh status"
        echo "  ./start_llmdiver.sh logs"
        exit 1
        ;;
esac