#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 12_tools/scripts/validate_vault.py

if command -v markdownlint-cli2 >/dev/null 2>&1; then
  markdownlint-cli2
elif command -v npx >/dev/null 2>&1; then
  npx --yes markdownlint-cli2
elif [[ "${CI:-}" == "true" ]]; then
  echo "markdownlint-cli2 is required in CI" >&2
  exit 1
else
  echo "markdownlint-cli2 not found; skipped external Markdown lint." >&2
fi
