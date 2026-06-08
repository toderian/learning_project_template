#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 12_tools/scripts/validate_vault.py

if [[ "${SKIP_MARKDOWNLINT:-}" == "1" ]]; then
  echo "SKIP_MARKDOWNLINT=1 set; skipped external Markdown lint." >&2
elif [[ -x "node_modules/.bin/markdownlint-cli2" ]]; then
  node_modules/.bin/markdownlint-cli2
elif command -v markdownlint-cli2 >/dev/null 2>&1; then
  markdownlint-cli2
elif command -v npx >/dev/null 2>&1; then
  npx --no-install markdownlint-cli2 || {
    echo "markdownlint-cli2 is required. Run npm ci, install it globally, or set SKIP_MARKDOWNLINT=1." >&2
    exit 1
  }
else
  echo "markdownlint-cli2 is required. Run npm ci, install it globally, or set SKIP_MARKDOWNLINT=1." >&2
  exit 1
fi
