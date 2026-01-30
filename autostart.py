"""Windows auto-start registry management."""

import sys
import winreg
from pathlib import Path

APP_NAME = "ClipboardImageViewer"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_path() -> str:
    """Get the path to the current executable or script."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        return sys.executable
    else:
        # Running as Python script
        return f'"{sys.executable}" "{Path(__file__).parent / "main.py"}"'


def is_auto_start_registered() -> bool:
    """Check if the application is registered for auto-start."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False


def enable_auto_start() -> bool:
    """Add the application to Windows auto-start."""
    try:
        exe_path = get_executable_path()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        return True
    except WindowsError as e:
        print(f"Failed to enable auto-start: {e}")
        return False


def disable_auto_start() -> bool:
    """Remove the application from Windows auto-start."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        # Already not registered
        return True
    except WindowsError as e:
        print(f"Failed to disable auto-start: {e}")
        return False


def toggle_auto_start() -> bool:
    """Toggle auto-start and return the new state."""
    if is_auto_start_registered():
        disable_auto_start()
        return False
    else:
        enable_auto_start()
        return True
