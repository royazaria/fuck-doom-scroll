"""
Three independent autostart mechanisms so the app survives any single failure:
  1. Registry  HKCU\Run
  2. Startup folder  %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FuckDoomScroll.vbs
  3. Task Scheduler  FuckDoomScrollWatchdog  (ONLOGON, current user, no admin needed)
"""
import sys
import os
import winreg
import subprocess

APP_NAME   = "FuckDoomScroll"
TASK_NAME  = "FuckDoomScrollWatchdog"

# Absolute paths
_WATCHDOG  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "watchdog.py")
_PYTHONW   = sys.executable.replace("python.exe", "pythonw.exe")  # works whether called via python or pythonw
_STARTUP   = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
_VBS_PATH  = os.path.join(_STARTUP, "FuckDoomScroll.vbs")
_APP_DIR   = os.path.dirname(_WATCHDOG)


# ── 1. Registry ───────────────────────────────────────────────────────────────

def _reg_install():
    cmd = f'"{_PYTHONW}" "{_WATCHDOG}"'
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)

def _reg_is_installed() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def _reg_uninstall():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass


# ── 2. Startup folder VBS ─────────────────────────────────────────────────────

def _vbs_install():
    vbs = (
        'Set oShell = CreateObject("WScript.Shell")\r\n'
        f'oShell.CurrentDirectory = "{_APP_DIR}"\r\n'
        f'oShell.Run Chr(34) & "{_PYTHONW}" & Chr(34) & " ' + f'\\"{_WATCHDOG}\\"", 0, False\r\n'
    )
    with open(_VBS_PATH, "w") as f:
        f.write(vbs)

def _vbs_is_installed() -> bool:
    return os.path.exists(_VBS_PATH)

def _vbs_uninstall():
    try:
        os.remove(_VBS_PATH)
    except FileNotFoundError:
        pass


# ── 3. Task Scheduler ─────────────────────────────────────────────────────────

def _task_install():
    """Requires admin on Windows 11 — silently skipped if denied."""
    cmd = f'"{_PYTHONW}" "{_WATCHDOG}"'
    subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", TASK_NAME,
            "/TR", cmd,
            "/SC", "ONLOGON",
            "/F",   # overwrite if exists
        ],
        capture_output=True,
    )

def _task_is_installed() -> bool:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True,
    )
    return result.returncode == 0

def _task_uninstall():
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def install():
    """Install all three persistence mechanisms."""
    try: _reg_install()
    except Exception: pass
    try: _vbs_install()
    except Exception: pass
    try: _task_install()
    except Exception: pass

def uninstall():
    """Remove all three persistence mechanisms."""
    _reg_uninstall()
    _vbs_uninstall()
    _task_uninstall()

def is_installed() -> bool:
    """Returns True if the two non-admin mechanisms (registry + VBS) are in place.
    Also attempts task scheduler (admin-only on Win11 — silently skipped if denied).
    Reinstalls any missing mechanism automatically."""
    reg  = _reg_is_installed()
    vbs  = _vbs_is_installed()
    if not reg:
        try: _reg_install()
        except Exception: pass
    if not vbs:
        try: _vbs_install()
        except Exception: pass
    if not _task_is_installed():
        try: _task_install()
        except Exception: pass
    return reg and vbs
