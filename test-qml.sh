#!/bin/bash
# Test QML Interface directly on Pop!_OS

echo "🧪 Testing QML Interface on Pop!_OS..."

# Check if we're on a desktop environment
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "❌ No display detected. Make sure you're running in a GUI environment."
    exit 1
fi

echo "✅ Display detected: $DISPLAY $WAYLAND_DISPLAY"

# Check if PySide6 is installed
echo "🔍 Checking PySide6 installation..."
if python3 -c "import PySide6" 2>/dev/null; then
    echo "✅ PySide6 is installed"
else
    echo "📦 Installing PySide6..."
    pip3 install --user PySide6
fi

# Test basic Qt functionality
echo "🧪 Testing basic Qt functionality..."
python3 -c "
from PySide6.QtWidgets import QApplication, QLabel
import sys
app = QApplication(sys.argv)
label = QLabel('✅ Qt Works!')
label.show()
print('Qt test window should appear...')
app.processEvents()
import time
time.sleep(2)
app.quit()
" || {
    echo "❌ Qt test failed. Installing missing dependencies..."
    sudo apt update
    sudo apt install -y qt6-base-dev libegl1 libgl1-mesa-glx python3-pyside6*
}

# Remove any offscreen mode settings
echo "🖥️  Ensuring visual mode..."
unset QT_QPA_PLATFORM

# Launch the QML app
echo "🚀 Launching Gmail Cleaner QML Interface..."
echo "📱 You should see a modern dark-themed window with Gmail Cleaner interface"
echo ""

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Launch with proper environment
QML_IMPORT_PATH="qml" python3 qml_main.py