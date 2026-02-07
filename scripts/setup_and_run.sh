#!/usr/bin/env bash
# Install dependencies into current environment, then run the app.
# Activate your own conda/venv first if you use one.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

"$SCRIPT_DIR/setup.sh"
echo "Starting EBM PathGen GUI..."
python main.py
