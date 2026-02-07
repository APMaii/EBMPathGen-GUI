#!/usr/bin/env bash
# Build the EBMPathGen-Setup single-file installer (Mac or Windows if run on Windows).
# Requires: pip install pyinstaller
# Run from project root:  ./installer/build_installer.sh
# Output: dist/EBMPathGen-Setup (Mac) or dist/EBMPathGen-Setup.exe (Windows)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v pyinstaller &>/dev/null; then
  echo "PyInstaller not found. Install with: pip install pyinstaller"
  exit 1
fi

pyinstaller installer/EBMPathGen_Installer.spec

echo ""
echo "Done. Installer is at: $PROJECT_ROOT/dist/EBMPathGen-Setup (or .exe on Windows)"
echo "Give that single file to your friend; they run it, choose a folder, then use the launcher created there."
