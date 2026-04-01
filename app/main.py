import threading
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

_countdown_active = False
_countdown_lock = threading.Lock()

def on_block_triggered(site: str):
    global _countdown_active
    with _countdown_lock:
        if _countdown_active:
            return
        _countdown_active = True

    def _run():
        global _countdown_active
        def on_done():
            global _countdown_active
            tracker.unblock(site)
            with _countdown_lock:
                _countdown_active = False
        show_countdown(COUNTDOWN_SECONDS, on_complete=on_done)

    threading.Thread(target=_run, daemon=False).start()

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
    import sys, os, traceback
    log_path = os.path.join(os.path.expanduser("~"), "ScrollBlocker.log")
    try:
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        if not autostart.is_installed():
            autostart.install()

        run_tray(on_quit=lambda: exit(0))
        server_thread.join()
    except Exception:
        with open(log_path, "w") as f:
            traceback.print_exc(file=f)
        raise

if __name__ == "__main__":
    main()
