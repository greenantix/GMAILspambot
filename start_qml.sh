#!/bin/bash

# Gmail Spam Bot - QML Interface Launcher
# Modern Qt/QML interface with LM Studio integration

echo "🚀 Starting Gmail Spam Bot QML Interface..."
echo "==============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed."
    exit 1
fi

echo "✓ Python3 found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

echo "✓ Virtual environment found"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check for PySide6
echo "🔍 Checking PySide6 installation..."
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "📦 PySide6 not found. Installing..."
    pip install PySide6
fi

echo "✓ PySide6 ready"

# Start health check server in background
echo "🏥 Starting health check server..."
if ! pgrep -f "health_check.py" > /dev/null; then
    python3 health_check.py &
    HEALTH_PID=$!
    echo "✓ Health check server started (PID: $HEALTH_PID)"
    sleep 2
else
    echo "✓ Health check server already running"
fi

# Check LM Studio connection
echo "🧠 Checking LM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✓ LM Studio is running and accessible"
else
    echo "⚠️  LM Studio not detected. Some features may be limited."
    echo "   Please start LM Studio and load a model for full functionality."
fi

# Launch QML application
echo ""
echo "🎯 Launching QML Interface..."
echo "📱 Features:"
echo "   • Modern dark theme interface"
echo "   • Real-time LM Studio integration" 
echo "   • Smart model switching (Phi-3, Llama-8B, CodeLlama)"
echo "   • Live email processing monitoring"
echo "   • Comprehensive audit log with restore"
echo "   • Advanced settings management"
echo ""

# Set environment variables for Qt
export QT_QPA_PLATFORM_PLUGIN_PATH="$VIRTUAL_ENV/lib/python*/site-packages/PySide6/Qt/plugins"
export QML_IMPORT_PATH="qml"

# Launch the QML application
python3 qml_main.py

# Cleanup
echo ""
echo "🛑 Shutting down..."
if [ ! -z "$HEALTH_PID" ]; then
    kill $HEALTH_PID 2>/dev/null
    echo "✓ Health check server stopped"
fi

echo "👋 Gmail Spam Bot QML interface closed."