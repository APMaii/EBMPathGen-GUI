#!/usr/bin/env python3
"""
EBMPathGen-GUI Installer — one-click setup with GUI.
Run this (or the packaged .exe / Mac app) to choose a folder, clone the repo,
create a virtual environment, install dependencies, and create a double-click launcher.
Requires: Python 3.8+ and Git installed on the system.
"""

import os
import sys
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

REPO_URL = "https://github.com/APMaii/EBMPathGen-GUI.git"
LAUNCHER_NAME_WIN = "Run EBM PathGen.bat"
LAUNCHER_NAME_MAC = "Run EBM PathGen.command"
IS_WINDOWS = platform.system() == "Windows"


def find_python():
    """Prefer the same Python running this script; fallback to python3 / python."""
    return sys.executable


def find_git():
    """Return path to git executable or None."""
    try:
        out = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0:
            return "git"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def run_cmd(cmd, cwd=None, env=None, log_fn=None):
    """Run command; log stdout/stderr via log_fn. Raise on non-zero exit."""
    if log_fn:
        log_fn(f"Running: {' '.join(cmd)}\n")
    env = env or os.environ.copy()
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in p.stdout:
        if log_fn:
            log_fn(line)
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {p.returncode}: {' '.join(cmd)}")


def install(install_dir: str, log_fn) -> str:
    """
    Create install_dir, clone repo, create venv, pip install, create launcher.
    Returns path to the created launcher file.
    """
    install_dir = os.path.abspath(install_dir)
    python_exe = find_python()
    if not find_git():
        raise RuntimeError("Git is not installed or not on PATH. Please install Git and try again.")

    # 1. Create directory (must be empty or not exist for clone)
    if os.path.exists(install_dir):
        if os.listdir(install_dir):
            raise RuntimeError(
                f"Folder is not empty: {install_dir}\nPlease choose an empty folder or a new path."
            )
    else:
        os.makedirs(install_dir, exist_ok=True)
        log_fn(f"Created folder: {install_dir}\n")

    # 2. Clone (clone into install_dir; repo root will be install_dir)
    log_fn("Cloning repository...\n")
    run_cmd(["git", "clone", REPO_URL, install_dir], log_fn=log_fn)
    # Remove .git if we want a clean copy; optional. Keep .git so they can pull updates.

    # 3. Create venv
    venv_path = os.path.join(install_dir, "venv")
    log_fn("Creating virtual environment...\n")
    run_cmd([python_exe, "-m", "venv", venv_path], log_fn=log_fn)

    # 4. Pip install
    if IS_WINDOWS:
        pip = os.path.join(venv_path, "Scripts", "pip.exe")
        python_launcher = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        pip = os.path.join(venv_path, "bin", "pip")
        python_launcher = os.path.join(venv_path, "bin", "python")
    req_file = os.path.join(install_dir, "requirements.txt")
    if not os.path.isfile(req_file):
        raise RuntimeError(f"requirements.txt not found at {req_file}")
    log_fn("Installing dependencies (this may take a few minutes)...\n")
    run_cmd([pip, "install", "-r", req_file], cwd=install_dir, log_fn=log_fn)

    # 5. Create launcher
    if IS_WINDOWS:
        launcher_path = os.path.join(install_dir, LAUNCHER_NAME_WIN)
        content = f'''@echo off
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
python main.py
pause
'''
        with open(launcher_path, "w", newline="\r\n") as f:
            f.write(content)
    else:
        launcher_path = os.path.join(install_dir, LAUNCHER_NAME_MAC)
        content = f'''#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec python main.py
'''
        with open(launcher_path, "w") as f:
            f.write(content)
        os.chmod(launcher_path, 0o755)

    log_fn(f"\nDone. Launcher created: {launcher_path}\n")
    return launcher_path


class InstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EBMPathGen-GUI Installer")
        self.root.minsize(480, 380)
        self.root.resizable(True, True)

        # Top frame: intro + path
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="EBMPathGen-GUI — Installer", font=("", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(
            top,
            text="Choose a folder. The app will be cloned there, dependencies installed,\n"
            "and a launcher created so you can run the app by double-clicking it.",
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 8))

        path_frame = ttk.Frame(top)
        path_frame.pack(fill=tk.X)
        self.path_var = tk.StringVar()
        default_dir = os.path.expanduser("~")
        if IS_WINDOWS:
            default_dir = os.path.join(default_dir, "EBMPathGen")
        else:
            default_dir = os.path.join(default_dir, "EBMPathGen")
        self.path_var.set(default_dir)
        ttk.Entry(path_frame, textvariable=self.path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(path_frame, text="Browse...", command=self._browse).pack(side=tk.RIGHT)

        # Install button
        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill=tk.X, pady=8)
        self.install_btn = ttk.Button(btn_frame, text="Install", command=self._do_install)
        self.install_btn.pack(side=tk.LEFT)

        # Log area
        ttk.Label(top, text="Log:").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(self.root, height=14, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _browse(self):
        d = filedialog.askdirectory(title="Choose install folder", initialdir=os.path.dirname(self.path_var.get()) or os.path.expanduser("~"))
        if d:
            self.path_var.set(d)

    def _log(self, msg: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _do_install(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please choose a folder.")
            return
        self.install_btn.config(state=tk.DISABLED)
        self._log("Starting installation...\n")

        def log_fn(msg):
            self.root.after(0, lambda: self._log(msg))

        def run():
            try:
                launcher = install(path, log_fn=log_fn)
                self.root.after(0, lambda: self._done(launcher, None))
            except Exception as e:
                self.root.after(0, lambda: self._done(None, str(e)))

        import threading
        threading.Thread(target=run, daemon=True).start()

    def _done(self, launcher_path, error):
        self.install_btn.config(state=tk.NORMAL)
        if error:
            self._log(f"\nError: {error}\n")
            messagebox.showerror("Installation failed", error)
            return
        messagebox.showinfo(
            "Installation complete",
            f"EBMPathGen-GUI is installed.\n\n"
            f"Double-click this file to run the app:\n{launcher_path}",
        )

    def run(self):
        self.root.mainloop()


def main():
    app = InstallerApp()
    app.run()


if __name__ == "__main__":
    main()
