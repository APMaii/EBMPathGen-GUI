@echo off
REM Build the EBMPathGen-Setup single-file installer on Windows.
REM Requires: pip install pyinstaller
REM Run from project root:  installer\build_installer.bat
REM Output: dist\EBMPathGen-Setup.exe

cd /d "%~dp0\.."
where pyinstaller >nul 2>nul
if errorlevel 1 (
  echo PyInstaller not found. Install with: pip install pyinstaller
  exit /b 1
)
pyinstaller installer\EBMPathGen_Installer.spec
echo.
echo Done. Installer is at: dist\EBMPathGen-Setup.exe
echo Give that file to your friend; they run it, choose a folder, then use the launcher created there.
