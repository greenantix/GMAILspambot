# 📦 Gmail Cleaner Flatpak

Transform your Gmail Cleaner into a native Linux desktop application!

## 🚀 Quick Start

### Option 1: Test QML Interface First (Recommended)
```bash
./test-qml.sh
```
This will test if the QML interface works on your Pop!_OS desktop.

### Option 2: Build Full Flatpak
```bash
./build-flatpak.sh
```
This creates a distributable Flatpak package.

## 📱 What You Get

✅ **Native Desktop App** - Shows up in your app launcher  
✅ **Modern QML Interface** - Material Design with dark theme  
✅ **Sandboxed Security** - Controlled access to Gmail credentials  
✅ **Auto-updatable** - Can be published to Flathub  
✅ **Cross-Distribution** - Works on any Linux distro with Flatpak  

## 🏗️ Project Structure

```
gmail-cleaner/
├── flatpak/
│   ├── com.greenantix.GmailCleaner.json    # Flatpak manifest
│   └── com.greenantix.GmailCleaner.yaml    # Alternative YAML format
├── src/                                     # Python source files
├── qml/                                     # QML interface files
├── gmail-cleaner.sh                         # Flatpak launcher script
├── com.greenantix.GmailCleaner.desktop     # Desktop entry
├── com.greenantix.GmailCleaner.svg         # App icon
├── com.greenantix.GmailCleaner.metainfo.xml # AppStream metadata
├── build-flatpak.sh                        # Build script
└── test-qml.sh                             # Quick test script
```

## 🎯 Features

- **🧠 LM Studio Integration** - AI-powered email categorization
- **📊 Real-time Dashboard** - Live processing statistics
- **📋 Audit System** - Comprehensive activity logging
- **⚙️ Advanced Settings** - Configurable rules and filters
- **🏥 Health Monitoring** - System status and diagnostics

## 📦 Distribution Options

### Local Installation
```bash
flatpak run com.greenantix.GmailCleaner
```

### Create Bundle for Sharing
```bash
flatpak build-bundle ~/.local/share/flatpak/repo gmail-cleaner.flatpak com.greenantix.GmailCleaner
```

### Publish to Flathub
1. Fork this repo to GitHub
2. Submit to [Flathub](https://github.com/flathub/flathub)
3. Users can install with: `flatpak install flathub com.greenantix.GmailCleaner`

## 🔧 Configuration

The Flatpak stores user data in:
- **Config**: `~/.config/gmail-cleaner/`
- **Data**: `~/.local/share/gmail-cleaner/`
- **Credentials**: Secure keyring integration

## 🐛 Troubleshooting

**QML won't show?**
```bash
# Test Qt installation
python3 -c "from PySide6.QtWidgets import QApplication, QLabel; app = QApplication([]); QLabel('Test').show(); app.exec()"

# Install missing packages
sudo apt install qt6-base-dev libegl1 libgl1-mesa-glx
```

**Flatpak build fails?**
```bash
# Clean and retry
rm -rf build-dir .flatpak-builder
./build-flatpak.sh
```

**Permission issues?**
```bash
# Reset Flatpak permissions
flatpak override --user com.greenantix.GmailCleaner --filesystem=home
```

## 🏆 Success Metrics

Once built, you should see:
- ✅ Gmail Cleaner appears in app launcher
- ✅ Modern QML interface opens on click
- ✅ LM Studio integration works
- ✅ Settings persist between sessions
- ✅ Can be shared as `.flatpak` file

Ready to build your Gmail Cleaner Flatpak? Start with `./test-qml.sh`!