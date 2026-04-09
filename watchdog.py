"""
Watchdog for F*CK Doom Scroll.
Keeps the app running forever — restarts it automatically if it crashes or is closed.
This is what runs on startup, not app/main.py directly.
"""
import sys, os

# ── Null-stream guard (same as main.py — pythonw.exe sets stdout=None) ────────
class _NullStream:
    encoding = "utf-8"; errors = "replace"
    def write(self, *a, **kw): pass
    def flush(self, *a, **kw): pass
    def isatty(self): return False
    def fileno(self): raise OSError("not a real file")

if sys.stdout is None: sys.stdout = _NullStream()
if sys.stderr is None: sys.stderr = _NullStream()

import subprocess
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable  # same pythonw.exe that runs this watchdog
LOG_PATH = os.path.join(os.path.expanduser("~"), "ScrollBlocker.log")


def _clear_pycache():
    """Delete all __pycache__ dirs so stale .pyc files never cause silent crashes."""
    for root, dirs, _ in os.walk(APP_DIR):
        for d in dirs:
            if d == "__pycache__":
                pycache = os.path.join(root, d)
                try:
                    import shutil
                    shutil.rmtree(pycache)
                except Exception:
                    pass
        # Don't descend into .worktrees or venv
        dirs[:] = [d for d in dirs if d not in (".worktrees", "venv", ".git")]


def run():
    _clear_pycache()

    while True:
        try:
            with open(LOG_PATH, "a") as log:
                proc = subprocess.Popen(
                    [PYTHON, "-m", "app.main"],
                    cwd=APP_DIR,
                    stdout=log,
                    stderr=log,
                )
                proc.wait()  # blocks until app exits for any reason
        except Exception as e:
            try:
                with open(LOG_PATH, "a") as log:
                    log.write(f"[watchdog] Popen error: {e}\n")
            except Exception:
                pass
        time.sleep(3)  # brief pause, then restart


if __name__ == "__main__":
    run()
