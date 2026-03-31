import subprocess
import sys

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "ScrollBlocker",
    "--add-data", "app;app",
    "app/main.py",
]
subprocess.run(cmd, check=True)
print("\nBuilt: dist/ScrollBlocker.exe")
print("Share ScrollBlocker.exe + the extension/ folder.")
