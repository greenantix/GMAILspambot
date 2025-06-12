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

# Check if config directory and credentials file exist
if [ ! -d "config" ]; then
    echo "📁 Creating config directory..."
    mkdir -p config
fi

if [ ! -f "config/credentials.json" ]; then
    echo "⚠️  config/credentials.json not found!"
    echo "   Please download your Gmail API credentials and place them as 'config/credentials.json'"
    echo "   Get them from: https://console.cloud.google.com/apis/credentials"
    echo ""
    read -p "Press Enter when you've added config/credentials.json, or Ctrl+C to exit..."
fi

# Check for token.json and warn about new scopes
if [ -f "config/token.json" ]; then
    echo "⚠️  Found existing token.json - you may need to re-authenticate"
    echo "   New scopes have been added (gmail.send for unsubscribe emails)"
    echo "   If you encounter auth errors, delete config/token.json and restart"
fi

# Check if settings.json exists in config, if not create a default one
if [ ! -f "config/settings.json" ]; then
    echo "📄 Creating default config/settings.json..."
    # Create a minimal default settings file
    cat > config/settings.json << EOF
{
  "important_keywords": [
    "security alert", "account suspended", "verify your account", "confirm your identity",
    "password reset", "login attempt", "suspicious activity", "unauthorized access",
    "fraud alert", "payment failed", "invoice due", "tax notice", "bank statement",
    "urgent action required", "account expires", "verification code"
  ],
  "important_senders": [
    "security@", "alerts@", "fraud@", "admin@", 
    "billing@", "accounts@", "statements@"
  ],
  "promotional_keywords": [
    "sale", "discount", "offer", "deal", "coupon", "promo", "marketing",
    "newsletter", "unsubscribe", "shop", "buy", "limited time", "free"
  ],
  "auto_delete_senders": [],
  "never_delete_senders": [],
  "max_emails_per_run": 50,
  "days_back": 7,
  "dry_run": false,
  "lm_studio_model": "meta-llama-3.1-8b-instruct"
}
EOF
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
echo "🎯 Starting Gmail Cleaner GUI with Intelligence Features..."
echo "   🚨 INBOX: Critical emails only (security alerts, personal messages)"
echo "   ⚡ PRIORITY: Important but not urgent (GitHub, Zillow, bank statements)"  
echo "   📦 Other categories: Bills, Shopping, Newsletters, Social, Personal, Junk"
echo "   🔧 Filter-first processing for massive email backlogs"
echo "   🤖 Machine learning-like pattern recognition and rule suggestions"
echo "   📊 Real-time analytics with filter effectiveness tracking"
echo "   ✉️  Automated unsubscribe workflow (HTTP links + mailto handling)"
echo "   🛡️  Crash-proof UI with comprehensive exception handling"
echo ""
echo "   Close the GUI window or press Ctrl+C here to stop"
echo ""

# Make the script executable and run the GUI
chmod +x gmail_lm_cleaner.py
python3 gmail_lm_cleaner.py

echo ""
echo "👋 Gmail Cleaner stopped"