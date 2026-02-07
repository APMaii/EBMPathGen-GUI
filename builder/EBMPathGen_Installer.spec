# PyInstaller spec for EBMPathGen-GUI Installer
# Build from project root:  pyinstaller installer/EBMPathGen_Installer.spec
# Output: dist/EBMPathGen-Setup (Mac) or dist/EBMPathGen-Setup.exe (Windows)

# -*- mode: python ; coding: utf-8 -*-
import os
# Resolve script path relative to this spec file so build works from any cwd
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
script_path = os.path.join(SPEC_DIR, 'installer_gui.py')

block_cipher = None

a = Analysis(
    [script_path],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# One-file bundle, no console window (GUI only)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EBMPathGen-Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # No terminal window; use for both Windows and Mac
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
