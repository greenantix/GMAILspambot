#!/bin/bash
# setup.sh - Automated environment setup for Gmail Automation System
# This script is idempotent and safe to run multiple times.
# It sets up Python environment, dependencies, directories, systemd services, and log rotation.

set -e

# Print error and exit on failure
function fail() {
  echo "❌ Error: $1"
  exit 1
}

echo "🔧 Gmail Automation System Setup"
echo "--------------------------------"

# 1. Create Python virtual environment if not present
if [ ! -d "venv" ]; then
  echo "🟢 Creating Python virtual environment..."
  python3 -m venv venv || fail "Failed to create virtual environment"
else
  echo "✅ Virtual environment already exists."
fi

# 2. Activate virtual environment
source venv/bin/activate || fail "Failed to activate virtual environment"

# 3. Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# 4. Install Python dependencies
if [ -f "requirements.txt" ]; then
  echo "📦 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt || fail "Failed to install requirements"
else
  echo "📦 Installing core dependencies (no requirements.txt found)..."
  pip install google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client google-generativeai python-dotenv \
    requests croniter flask pandas colorama || fail "Failed to install core dependencies"
fi

# 5. Create required directories
for d in logs exports rules data; do
  if [ ! -d "$d" ]; then
    echo "📁 Creating directory: $d"
    mkdir -p "$d" || fail "Failed to create directory $d"
  else
    echo "✅ Directory exists: $d"
  fi
done

# 6. Set permissions for scripts
chmod +x *.py *.sh

# 7. Create sample systemd unit files if not present
SYSTEMD_DIR="./systemd_units"
mkdir -p "$SYSTEMD_DIR"

# Main runner service
RUNNER_SERVICE="$SYSTEMD_DIR/gmail-autonomy-runner.service"
if [ ! -f "$RUNNER_SERVICE" ]; then
  cat > "$RUNNER_SERVICE" <<EOF
[Unit]
Description=Gmail Autonomy Runner
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/autonomous_runner.py
Restart=on-failure
User=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
  echo "📝 Created sample systemd unit: $RUNNER_SERVICE"
else
  echo "✅ Systemd unit exists: $RUNNER_SERVICE"
fi

# Health check service
HEALTH_SERVICE="$SYSTEMD_DIR/gmail-autonomy-health.service"
if [ ! -f "$HEALTH_SERVICE" ]; then
  cat > "$HEALTH_SERVICE" <<EOF
[Unit]
Description=Gmail Autonomy Health Check API
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/health_check.py
Restart=on-failure
User=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
  echo "📝 Created sample systemd unit: $HEALTH_SERVICE"
else
  echo "✅ Systemd unit exists: $HEALTH_SERVICE"
fi

# 8. (Optional) Install systemd units (requires sudo)
echo
echo "To enable services, run:"
echo "  sudo cp $RUNNER_SERVICE /etc/systemd/system/gmail-autonomy-runner.service"
echo "  sudo cp $HEALTH_SERVICE /etc/systemd/system/gmail-autonomy-health.service"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable gmail-autonomy-runner"
echo "  sudo systemctl enable gmail-autonomy-health"
echo "  sudo systemctl start gmail-autonomy-runner"
echo "  sudo systemctl start gmail-autonomy-health"

# 9. Set up log rotation for logs directory
LOGROTATE_CONF="/etc/logrotate.d/gmail-autonomy"
TMP_LOGROTATE="gmail-autonomy.logrotate"
cat > "$TMP_LOGROTATE" <<EOF
$(pwd)/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
EOF

if [ -w "/etc/logrotate.d" ]; then
  sudo cp "$TMP_LOGROTATE" "$LOGROTATE_CONF"
  echo "🌀 Logrotate config installed at $LOGROTATE_CONF"
else
  echo "⚠️  No permission to write to /etc/logrotate.d. Please run:"
  echo "    sudo cp $TMP_LOGROTATE $LOGROTATE_CONF"
fi
rm -f "$TMP_LOGROTATE"

# 10. Print usage instructions and next steps
echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Review and update your .env or settings.json as needed."
echo "2. Copy and enable the systemd services as shown above."
echo "3. To start the main runner: sudo systemctl start gmail-autonomy-runner"
echo "4. To start the health check API: sudo systemctl start gmail-autonomy-health"
echo "5. Logs are in the 'logs/' directory and will be rotated automatically."
echo
echo "To rerun this setup, simply execute ./setup.sh again."
echo
echo "For more details, see README.md or claude.md."