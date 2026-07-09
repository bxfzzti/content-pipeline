#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 \
LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1 \
lark-cli base +base-create \
  --name "Hermes 产品体验选题池" \
  --table-name "选题池" \
  --time-zone Asia/Shanghai \
  --fields "$(cat references/lark_base_schema.json)" \
  --as user \
  --format json
