#!/usr/bin/env bash
# WFH Job Bot — Mac / Linux runner
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
  echo "Python 3 is not installed. Install it from https://www.python.org/downloads/"; exit 1
fi

if ! python3 -c "import requests, yaml" >/dev/null 2>&1; then
  echo "Installing required pieces (one time only)..."
  python3 -m pip install --quiet --upgrade pip
  python3 -m pip install --quiet -r requirements.txt
fi

echo "Checking LinkedIn, Apna, Naukri for work-from-home jobs..."
python3 -m jobbot.main
echo
echo "Digest saved at: data/latest_digest.html"
echo "To prove alerts work, run:  python3 -m jobbot.main --test"
