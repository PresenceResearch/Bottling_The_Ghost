#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$DEPLOY_DIR/.." && pwd)"

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
RUNTIME_DIR="${CLARA_RUNTIME_DIR:-$HOME/.clara_runtime}"
RUNTIME_DEPLOY_DIR="$RUNTIME_DIR/app/8_DEPLOYMENT"
LOG_DIR="$RUNTIME_DIR/logs"
BOT_PLIST="$LAUNCH_AGENTS_DIR/com.clara.bot.plist"
OLLAMA_PLIST="$LAUNCH_AGENTS_DIR/com.clara.ollama.plist"

VENV_PYTHON="$RUNTIME_DIR/venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing virtualenv python at $VENV_PYTHON"
  echo "Run 'make setup-runtime' in 8_DEPLOYMENT first."
  exit 1
fi

if [[ -n "${OLLAMA_BIN:-}" ]]; then
  OLLAMA_CMD="$OLLAMA_BIN"
elif [[ -x "/opt/homebrew/bin/ollama" ]]; then
  OLLAMA_CMD="/opt/homebrew/bin/ollama"
elif [[ -x "/usr/local/bin/ollama" ]]; then
  OLLAMA_CMD="/usr/local/bin/ollama"
else
  OLLAMA_CMD="$(command -v ollama || true)"
fi

if [[ -z "$OLLAMA_CMD" ]]; then
  echo "Could not find ollama binary in PATH."
  echo "Install Ollama and ensure it is on PATH."
  exit 1
fi

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"
bash "$SCRIPT_DIR/sync_runtime_app.sh"

cat > "$OLLAMA_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.clara.ollama</string>
  <key>ProgramArguments</key>
  <array>
    <string>$OLLAMA_CMD</string>
    <string>serve</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/ollama.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/ollama_error.log</string>
</dict>
</plist>
EOF

cat > "$BOT_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.clara.bot</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV_PYTHON</string>
    <string>$RUNTIME_DEPLOY_DIR/telegram_bot.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$RUNTIME_DEPLOY_DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/clara_bot.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/clara_bot_error.log</string>
</dict>
</plist>
EOF

UID_VALUE="$(id -u)"
pkill -f "[o]llama serve" >/dev/null 2>&1 || true

launchctl bootout "gui/$UID_VALUE" "$OLLAMA_PLIST" >/dev/null 2>&1 || true
launchctl bootout "gui/$UID_VALUE" "$BOT_PLIST" >/dev/null 2>&1 || true

launchctl bootstrap "gui/$UID_VALUE" "$OLLAMA_PLIST"
launchctl bootstrap "gui/$UID_VALUE" "$BOT_PLIST"

echo "Installed and started launch agents:"
echo "  - com.clara.ollama"
echo "  - com.clara.bot"
echo
echo "Check status:"
echo "  launchctl print gui/$UID_VALUE/com.clara.ollama | head -n 5"
echo "  launchctl print gui/$UID_VALUE/com.clara.bot | head -n 5"
echo
echo "Tail logs:"
echo "  tail -f \"$LOG_DIR/ollama.log\" \"$LOG_DIR/clara_bot.log\""
