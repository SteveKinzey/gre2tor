#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/"
  read -r -p "Press Enter to exit..."
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "Creating local Python environment..."
  python3 -m venv venv
fi

echo "Installing/updating requirements..."
"venv/bin/python" -m pip install --upgrade pip
"venv/bin/python" -m pip install -r requirements.txt

echo "Starting GRE2Tor..."
"venv/bin/python" scripts/run_local.py
