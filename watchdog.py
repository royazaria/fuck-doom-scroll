"""
Watchdog for F*CK Doom Scroll.
Keeps the app running forever — restarts it automatically if it crashes or is closed.
This is what runs on startup, not app/main.py directly.
"""
import subprocess
import time
import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable  # same pythonw.exe that runs this watchdog

def run():
    while True:
        proc = subprocess.Popen(
            [PYTHON, "-m", "app.main"],
            cwd=APP_DIR,
        )
        proc.wait()  # blocks until app exits for any reason
        time.sleep(3)  # brief pause, then restart

if __name__ == "__main__":
    run()
