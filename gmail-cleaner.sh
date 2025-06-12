#!/bin/bash
# Gmail Cleaner Flatpak Launcher

# Set up environment
export QML_IMPORT_PATH="/app/qml"
export PYTHONPATH="/app:$PYTHONPATH"

# Create config directory if it doesn't exist
mkdir -p "$HOME/.config/gmail-cleaner"
mkdir -p "$HOME/.local/share/gmail-cleaner"

# Copy default config if user doesn't have one
if [ ! -f "$HOME/.config/gmail-cleaner/settings.json" ] && [ -f "/app/config/settings.json" ]; then
    cp "/app/config/settings.json" "$HOME/.config/gmail-cleaner/"
fi

# Change to app directory
cd /app

# Launch the QML application
exec python3 qml_main.py "$@"