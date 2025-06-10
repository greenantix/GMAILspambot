# Gmail Intelligent Cleaner

A smart Gmail management tool with GUI that uses local LLM (via LM Studio) to intelligently sort and clean your inbox.

## 🚀 Quick Start for Linux

### 1. Simple Startup
```bash
chmod +x start.sh
./start.sh
```

### 2. Simple Shutdown
```bash
chmod +x stop.sh
./stop.sh
```

That's it! The startup script handles everything automatically.

## 📋 What You Need

1. **Gmail API Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create credentials for Gmail API
   - Download as `credentials.json` and place in this folder

2. **LM Studio (Optional but Recommended)**
   - Download from [LM Studio website](https://lmstudio.ai/)
   - Load any chat model
   - Keep it running on port 1234

## ✨ Features

- **Smart Filtering**: Never deletes important emails (bank, security, account info)
- **Configurable Settings**: Customize keywords and sender patterns
- **Safe Mode**: Dry run option to see what would happen
- **GUI Interface**: Easy-to-use graphical interface
- **Conservative Approach**: When in doubt, keeps emails

## 🔧 Settings You Can Configure

- **Important Keywords**: Words that mark emails as important
- **Important Senders**: Email patterns that should never be deleted
- **Never Delete List**: Specific senders to always keep
- **Processing Limits**: How many emails to process at once

## 🛡️ Safety Features

- **Dry Run Mode**: Test without actually modifying emails
- **Conservative LLM Prompts**: Strongly biased towards keeping emails
- **Pre-filtering**: Important emails are protected before LLM analysis
- **Manual Override**: Complete control over all settings

## 📁 Files Created

- `settings.json` - Your configuration preferences
- `token.json` - Gmail authentication (kept secure)
- Various logs and temporary files (auto-cleaned on shutdown)

## 🆘 Troubleshooting

**"Python not found"**
```bash
sudo apt update && sudo apt install python3 python3-pip
```

**"Package installation failed"**
```bash
pip3 install --user google-auth google-auth-oauthlib google-api-python-client requests
```

**"Credentials not found"**
- Make sure `credentials.json` is in the same folder as the scripts
- Verify it's downloaded from Google Cloud Console

**"LM Studio not running"**
- The app works without LM Studio, just with limited analysis
- Download LM Studio and load any chat model for full functionality

## 🔒 Privacy & Security

- All processing happens locally on your machine
- No data is sent to external servers (except Google for Gmail API)
- LM Studio runs locally - your emails never leave your computer
- Authentication tokens are stored securely