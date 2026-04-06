import threading
import queue
import time
import ctypes
import os
import traceback
import uvicorn
from app.config import SERVER_PORT, ACTIVE_SCROLL_THRESHOLD_SECONDS, COUNTDOWN_SECONDS
from app.tracker import ScrollTracker
from app.server import create_app
from app.countdown import show_countdown
from app.tray import run_tray
from app import autostart

LOG_PATH = os.path.join(os.path.expanduser("~"), "ScrollBlocker.log")

tracker = ScrollTracker(threshold=ACTIVE_SCROLL_THRESHOLD_SECONDS, cooldown=COUNTDOWN_SECONDS)

_countdown_queue = queue.Queue()
_countdown_active = False
_countdown_lock = threading.Lock()

# ── Call detection (don't interrupt Zoom/Teams/WhatsApp/Meet) ─────────────────
_CALL_KEYWORDS = ['zoom meeting', 'microsoft teams', 'whatsapp', 'google meet', 'webex', 'meets call']

def _is_call_in_progress():
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
    try:
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(_cb), 0)
    except Exception:
        pass
    return any(any(kw in t for kw in _CALL_KEYWORDS) for t in titles)

# ── Scroll → block trigger ────────────────────────────────────────────────────
def on_block_triggered(site):
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
    if not was_blocked and tracker.is_blocked(site):
        on_block_triggered(site)

tracker.record_scroll = _patched_record
fastapi_app = create_app(tracker)

# ── Server — if it dies, crash the whole process so watchdog restarts ─────────
def start_server():
    try:
        uvicorn.run(fastapi_app, host="127.0.0.1", port=SERVER_PORT, log_config=None)
    except Exception:
        with open(LOG_PATH, "w") as f:
            traceback.print_exc(file=f)
    finally:
        os._exit(1)  # force watchdog to restart everything

def main():
    try:
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        if not autostart.is_installed():
            autostart.install()

        run_tray(on_quit=lambda: os._exit(0))

        # Main thread: show countdown windows (tkinter must run on main thread)
        global _countdown_active
        while True:
            try:
                site = _countdown_queue.get(timeout=1)
            except queue.Empty:
                continue

            while _is_call_in_progress():
                time.sleep(15)

            duration = tracker.get_countdown_seconds(site, COUNTDOWN_SECONDS)

            def on_done(s=site):
                global _countdown_active
                tracker.unblock(s)
                with _countdown_lock:
                    _countdown_active = False

            try:
                show_countdown(duration, on_complete=on_done)
            except Exception:
                with open(LOG_PATH, "a") as f:
                    traceback.print_exc(file=f)
                on_done()  # unblock even if countdown crashes

    except Exception:
        with open(LOG_PATH, "w") as f:
            traceback.print_exc(file=f)
        os._exit(1)

if __name__ == "__main__":
    main()
