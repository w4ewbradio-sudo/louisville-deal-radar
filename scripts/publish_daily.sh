#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_daily.py
git add index.html daily data/deals.json
git diff --cached --quiet || git commit -m "Daily dashboard rebuild"
git push
