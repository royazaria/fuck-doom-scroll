import threading
import queue
import time
import ctypes
import uvicorn
from app.config import (
    SERVER_PORT, ACTIVE_SCROLL_THRESHOLD_SECONDS,
    COUNTDOWN_SECONDS,
)
from app.tracker import ScrollTracker
from app.server import create_app
from app.countdown import show_countdown
from app.tray import run_tray
from app import autostart

tracker = ScrollTracker(
    threshold=ACTIVE_SCROLL_THRESHOLD_SECONDS,
    cooldown=COUNTDOWN_SECONDS,
)

# Queue used to pass countdown requests to the main thread
# (tkinter MUST run on the main thread on Windows)
_countdown_queue = queue.Queue()
_countdown_active = False
_countdown_lock = threading.Lock()

# ── Call detection ────────────────────────────────────────────────────────────
_CALL_KEYWORDS = [
    'zoom meeting', 'zoom', 'microsoft teams', 'teams meeting',
    'whatsapp', 'google meet', ' meet ', 'webex', 'on a call',
]

def _is_call_in_progress() -> bool:
    """Returns True if a video/audio call app has a visible window."""
    titles = []
    def _cb(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            n = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if n > 2:
                buf = ctypes.create_unicode_buffer(n + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, n + 1)
                titles.append(buf.value.lower())
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return any(any(kw in t for kw in _CALL_KEYWORDS) for t in titles)

# ── Scroll tracking ───────────────────────────────────────────────────────────
def on_block_triggered(site: str):
    global _countdown_active
    with _countdown_lock:
        if _countdown_active:
            return
        _countdown_active = True
    _countdown_queue.put(site)

original_record = tracker.record_scroll

def _patched_record(site, active_seconds):
    was_blocked = tracker.is_blocked(site)
    original_record(site, active_seconds)
    now_blocked = tracker.is_blocked(site)
    if not was_blocked and now_blocked:
        on_block_triggered(site)

tracker.record_scroll = _patched_record

fastapi_app = create_app(tracker)

def start_server():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")

def main():
    import os, traceback
    log_path = os.path.join(os.path.expanduser("~"), "ScrollBlocker.log")
    try:
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        if not autostart.is_installed():
            autostart.install()

        run_tray(on_quit=lambda: exit(0))

        # Main thread: process countdown requests
        # tkinter MUST run on the main thread on Windows
        global _countdown_active
        while True:
            try:
                site = _countdown_queue.get(timeout=1)
            except queue.Empty:
                continue

            # Wait if a call is in progress — don't interrupt Zoom/Teams/WhatsApp/Meet
            while _is_call_in_progress():
                time.sleep(15)

            duration = tracker.get_countdown_seconds(site, COUNTDOWN_SECONDS)

            def on_done(s=site):
                global _countdown_active
                tracker.unblock(s)
                with _countdown_lock:
                    _countdown_active = False

            show_countdown(duration, on_complete=on_done)

    except Exception:
        with open(log_path, "w") as f:
            traceback.print_exc(file=f)
        raise

if __name__ == "__main__":
    main()
