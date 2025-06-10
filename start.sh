#!/bin/bash

# Gmail Cleaner - Easy Startup Script
# This script handles all dependencies and launches the Gmail cleaner

echo "🚀 Gmail Intelligent Cleaner - Starting Up"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first:"
    echo "   sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

echo "✓ Python3 found"

# Check and install required Python packages
echo "📦 Checking Python dependencies..."

# List of required packages
packages=(
    "google-auth"
    "google-auth-oauthlib" 
    "google-auth-httplib2"
    "google-api-python-client"
    "google-generativeai"
    "python-dotenv"
    "requests"
)

missing_packages=()

for package in "${packages[@]}"; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

# Install missing packages
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "📥 Installing missing packages: ${missing_packages[*]}"
    pip3 install "${missing_packages[@]}"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install packages. Trying with --user flag..."
        pip3 install --user "${missing_packages[@]}"
        
        if [ $? -ne 0 ]; then
            echo "❌ Package installation failed. Please run manually:"
            echo "   pip3 install ${missing_packages[*]}"
            exit 1
        fi
    fi
fi

echo "✓ All dependencies installed"

# Check if credentials file exists
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found!"
    echo "   Please download your Gmail API credentials and place them as 'credentials.json'"
    echo "   Get them from: https://console.cloud.google.com/apis/credentials"
    echo ""
    read -p "Press Enter when you've added credentials.json, or Ctrl+C to exit..."
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   For Gemini auto-analysis, create a .env file with your API key:"
    echo "   cp .env.example .env"
    echo "   Then edit .env and add your Gemini API key from https://aistudio.google.com/app/apikey"
    echo "   (This is optional - the app works without Gemini)"
    echo ""
fi

# Check if LM Studio is running (optional)
echo "🤖 Checking LM Studio connection..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✓ LM Studio is running"
else
    echo "⚠️  LM Studio not detected on port 1234"
    echo "   The app will still work, but email analysis will be limited"
    echo "   Start LM Studio and load a model for full functionality"
fi

echo ""
echo "🎯 Starting Gmail Cleaner GUI..."
echo "   Close the GUI window or press Ctrl+C here to stop"
echo ""

# Make the script executable and run the GUI
chmod +x gmail_lm_cleaner.py
python3 -c "from gmail_lm_cleaner import GmailCleanerGUI; app = GmailCleanerGUI(); app.run()"

echo ""
echo "👋 Gmail Cleaner stopped"