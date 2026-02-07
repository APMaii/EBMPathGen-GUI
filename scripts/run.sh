#!/usr/bin/env bash
# Run the EBM PathGen GUI (uses current environment).
# Activate your conda/venv first if you use one, then run this.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

python main.py
