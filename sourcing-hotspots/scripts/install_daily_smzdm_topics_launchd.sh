#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <base_token> [table_id]" >&2
  exit 2
fi

BASE_TOKEN="$1"
TABLE_ID="${2:-选题池}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/ai.hermes.smzdm-product-topics.plist"
PY="${HERMES_TOPICS_PYTHON:-python3}"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.hermes.smzdm-product-topics</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$ROOT/scripts/smzdm_product_topics.py</string>
    <string>--output-dir</string>
    <string>$ROOT/output</string>
    <string>--sync-lark</string>
    <string>--base-token</string>
    <string>$BASE_TOKEN</string>
    <string>--table-id</string>
    <string>$TABLE_ID</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>20</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$ROOT/output/daily-smzdm-topics.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/output/daily-smzdm-topics.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "$PLIST"
