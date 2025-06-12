#!/bin/bash
# Gmail Cleaner Flatpak Build Script

set -e

echo "🏗️  Building Gmail Cleaner Flatpak..."

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "❌ flatpak-builder not found. Installing..."
    sudo apt update
    sudo apt install -y flatpak-builder
fi

# Check if Flathub remote is added
if ! flatpak remotes | grep -q flathub; then
    echo "📦 Adding Flathub remote..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

# Install required runtimes
echo "📚 Installing required runtimes..."
flatpak install -y flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build-dir .flatpak-builder

# Update requirements with PySide6
echo "📝 Updating requirements.txt with PySide6..."
if ! grep -q "PySide6" requirements.txt; then
    echo "PySide6>=6.5.0" >> requirements.txt
fi

# Build the Flatpak
echo "🔨 Building Flatpak package..."
flatpak-builder build-dir flatpak/com.greenantix.GmailCleaner.json --force-clean --ccache

# Install locally
echo "📦 Installing locally..."
flatpak-builder --user --install --force-clean build-dir flatpak/com.greenantix.GmailCleaner.json

echo "✅ Build complete!"
echo ""
echo "🚀 To run your app:"
echo "   flatpak run com.greenantix.GmailCleaner"
echo ""
echo "📱 Or find it in your applications menu: 'Gmail Cleaner'"
echo ""
echo "🗂️  To uninstall:"
echo "   flatpak uninstall com.greenantix.GmailCleaner"
echo ""
echo "📦 To create a bundle for distribution:"
echo "   flatpak build-bundle ~/.local/share/flatpak/repo gmail-cleaner.flatpak com.greenantix.GmailCleaner"