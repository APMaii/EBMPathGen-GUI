#!/usr/bin/env bash
# Install dependencies into the current environment (no env creation).
# Activate your own conda/venv first if you use one, then run this.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

REQUIREMENTS="$PROJECT_ROOT/requirements.txt"

echo "EBMPathGen-GUI — Installing dependencies (current environment)"
echo "Project root: $PROJECT_ROOT"
echo ""

pip install -r "$REQUIREMENTS"

echo ""
echo "Done. Run the app with: pm_ebm run  or  python main.py"
