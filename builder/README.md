
## Building the installer 
You need to build the installer once per platform (Mac and Windows) so your friend can download the right file.

1. **Install PyInstaller** (one-time):

   ```bash
   pip install pyinstaller
   ```

2. **Build** (from the project root):

   ```bash
   chmod +x installer/build_installer.sh
   ./installer/build_installer.sh
   ```

   Or directly:

   ```bash
   pyinstaller installer/EBMPathGen_Installer.spec
   ```

3. **Output:**

   - **Mac:** `dist/EBMPathGen-Setup` (no extension; executable)
   - **Windows:** `dist/EBMPathGen-Setup.exe`

Give your friend the file for their OS. They do not need to install Python or Git before running the installer; the installer will use their existing Python and Git. (If Python or Git is missing, the installer will show an error and ask them to install it.)

---

## Testing the installer without building

From the project root (with Python and Git available):

```bash
python installer/installer_gui.py
```

This opens the same GUI; choose a folder and install. Useful to verify behavior before building the executable.
