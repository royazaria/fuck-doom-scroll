# Scroll Blocker — Windows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Windows desktop app + Chrome/Edge browser extension that detects active scrolling on Facebook, Instagram, and YouTube, and after 2.5 minutes blocks access behind a fullscreen 60-second countdown that cannot be dismissed.

**Architecture:** A Python tray app runs a local HTTP server on `localhost:7331`. A browser extension content script detects scroll velocity, reports accumulated active-scroll time to the Python server, and polls for block status. When the threshold is hit, the Python server shows a fullscreen topmost countdown window (tkinter + win32 hooks) and tells the extension to block navigation. After 60 seconds the block lifts, the cycle resets.

**Tech Stack:** Python 3.11, tkinter, pywin32, pystray, Pillow, uvicorn/FastAPI (local server), Chrome/Edge Manifest V3 extension, PyInstaller (to build .exe)

---

## File Map

| File | Responsibility |
|------|---------------|
| `app/server.py` | FastAPI local HTTP server — receives scroll pings, returns block status |
| `app/tracker.py` | Tracks per-site active-scroll seconds, decides when to block |
| `app/countdown.py` | Fullscreen tkinter window, topmost, hooks Win/Alt+F4, 60s countdown |
| `app/tray.py` | pystray system tray icon + menu (pause, quit) |
| `app/autostart.py` | Adds/removes app from Windows registry autostart |
| `app/main.py` | Entry point — starts server, tray, wires together |
| `app/config.py` | Constants: blocked sites, scroll threshold, countdown duration |
| `extension/manifest.json` | Chrome MV3 manifest |
| `extension/content.js` | Detects scroll velocity on page, pings server |
| `extension/background.js` | Polls server for block status, redirects blocked tabs |
| `extension/blocked.html` | Page shown to blocked tabs |
| `tests/test_tracker.py` | Unit tests for scroll tracking + block logic |
| `tests/test_server.py` | Integration tests for HTTP endpoints |
| `build.py` | PyInstaller build script → `dist/ScrollBlocker.exe` |
| `requirements.txt` | Python dependencies |

---

## Task 1: Project bootstrap + config

**Files:**
- Create: `app/config.py`
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `app/config.py`**

```python
BLOCKED_SITES = [
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "youtube.com", "www.youtube.com", "m.youtube.com",
]

SERVER_PORT = 7331
ACTIVE_SCROLL_THRESHOLD_SECONDS = 150  # 2.5 minutes
COUNTDOWN_SECONDS = 60
SCROLL_VELOCITY_MIN = 3   # scroll events per second to count as "active"
POLL_INTERVAL_MS = 2000   # extension polls server every 2s
```

- [ ] **Step 2: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn==0.30.6
pywin32==306
pystray==0.19.5
Pillow==10.4.0
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 3: Install dependencies**

```bash
cd C:\Users\Roy\Downloads\scroll-blocker
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 4: Create empty `tests/__init__.py`**

```python
```

- [ ] **Step 5: Commit**

```bash
git init
git add app/config.py requirements.txt tests/__init__.py
git commit -m "feat: project bootstrap + config"
```

---

## Task 2: Scroll tracker logic

**Files:**
- Create: `app/tracker.py`
- Create: `tests/test_tracker.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tracker.py
import time
import pytest
from app.tracker import ScrollTracker

def test_fresh_tracker_not_blocked():
    t = ScrollTracker(threshold=10, cooldown=5)
    assert t.is_blocked("youtube.com") is False

def test_accumulates_active_scroll_time():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=6)
    t.record_scroll("youtube.com", active_seconds=5)
    assert t.get_accumulated("youtube.com") == 11

def test_triggers_block_at_threshold():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.is_blocked("youtube.com") is True

def test_different_sites_independent():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.is_blocked("facebook.com") is False

def test_unblock_resets_accumulator():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    t.unblock("youtube.com")
    assert t.is_blocked("youtube.com") is False
    assert t.get_accumulated("youtube.com") == 0
```

- [ ] **Step 2: Run tests — expect FAIL (module not found)**

```bash
pytest tests/test_tracker.py -v
```

Expected output: `ModuleNotFoundError: No module named 'app.tracker'`

- [ ] **Step 3: Implement `app/tracker.py`**

```python
import threading
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class SiteState:
    accumulated: float = 0.0
    blocked: bool = False

class ScrollTracker:
    def __init__(self, threshold: float, cooldown: float):
        self.threshold = threshold
        self.cooldown = cooldown
        self._sites: Dict[str, SiteState] = {}
        self._lock = threading.Lock()

    def _get(self, site: str) -> SiteState:
        if site not in self._sites:
            self._sites[site] = SiteState()
        return self._sites[site]

    def record_scroll(self, site: str, active_seconds: float):
        with self._lock:
            state = self._get(site)
            if not state.blocked:
                state.accumulated += active_seconds
                if state.accumulated >= self.threshold:
                    state.blocked = True

    def is_blocked(self, site: str) -> bool:
        with self._lock:
            return self._get(site).blocked

    def unblock(self, site: str):
        with self._lock:
            self._sites[site] = SiteState()

    def get_accumulated(self, site: str) -> float:
        with self._lock:
            return self._get(site).accumulated
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_tracker.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add app/tracker.py tests/test_tracker.py
git commit -m "feat: scroll tracker with block threshold"
```

---

## Task 3: Local HTTP server (FastAPI)

**Files:**
- Create: `app/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_server.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.server import create_app
from app.tracker import ScrollTracker

@pytest.fixture
def tracker():
    return ScrollTracker(threshold=10, cooldown=5)

@pytest.fixture
def app(tracker):
    return create_app(tracker)

@pytest.mark.asyncio
async def test_status_not_blocked(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/status?site=youtube.com")
    assert r.status_code == 200
    assert r.json() == {"blocked": False}

@pytest.mark.asyncio
async def test_scroll_ping_accumulates(app, tracker):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/scroll", json={"site": "youtube.com", "active_seconds": 5})
    assert r.status_code == 200
    assert tracker.get_accumulated("youtube.com") == 5

@pytest.mark.asyncio
async def test_status_blocked_after_threshold(app, tracker):
    tracker.record_scroll("youtube.com", active_seconds=11)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/status?site=youtube.com")
    assert r.json() == {"blocked": True}
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_server.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.server'`

- [ ] **Step 3: Install pytest-asyncio**

```bash
pip install pytest-asyncio==0.23.8
```

- [ ] **Step 4: Add `pytest.ini` to root**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5: Implement `app/server.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.tracker import ScrollTracker

class ScrollPing(BaseModel):
    site: str
    active_seconds: float

def create_app(tracker: ScrollTracker) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/status")
    def status(site: str):
        return {"blocked": tracker.is_blocked(site)}

    @app.post("/scroll")
    def scroll(ping: ScrollPing):
        tracker.record_scroll(ping.site, ping.active_seconds)
        return {"ok": True, "accumulated": tracker.get_accumulated(ping.site)}

    @app.post("/unblock")
    def unblock(site: str):
        tracker.unblock(site)
        return {"ok": True}

    return app
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
pytest tests/test_server.py -v
```

Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add app/server.py tests/test_server.py pytest.ini
git commit -m "feat: local HTTP server with scroll + status endpoints"
```

---

## Task 4: Fullscreen countdown window

**Files:**
- Create: `app/countdown.py`

This is the core UX — a fullscreen window that:
- Covers all monitors
- Has no title bar (overrideredirect)
- Is always on top
- Intercepts Alt+F4, Win key via low-level keyboard hook
- Regains focus if it loses it
- Calls `on_complete` callback when 60s expires

- [ ] **Step 1: Implement `app/countdown.py`**

```python
import tkinter as tk
import ctypes
import ctypes.wintypes
import threading
from typing import Callable

# Windows API constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_F4 = 0x73
MOD_ALT = 0x0001

BLOCKED_KEYS = {VK_LWIN, VK_RWIN}

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class CountdownWindow:
    def __init__(self, seconds: int, on_complete: Callable):
        self.seconds = seconds
        self.remaining = seconds
        self.on_complete = on_complete
        self._hook = None
        self._hook_thread = None
        self.root = None

    def show(self):
        """Show the fullscreen countdown. Blocks until countdown completes."""
        self._install_keyboard_hook()
        self._build_window()
        self._tick()
        self.root.mainloop()
        self._uninstall_keyboard_hook()

    def _build_window(self):
        self.root = tk.Tk()
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        # Cover all virtual screen (multi-monitor)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")

        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # Regain focus if lost
        self.root.bind("<FocusOut>", lambda e: self.root.after(100, self.root.focus_force))
        self.root.bind("<Escape>", lambda e: None)
        self.root.bind("<Alt-F4>", lambda e: None)

        # Main message
        tk.Label(
            self.root,
            text="DON'T BE ON YOUR PHONE WHILE WAITING",
            font=("Arial Black", 28, "bold"),
            fg="white",
            bg="black",
            wraplength=800,
            justify="center",
        ).pack(expand=True, pady=(120, 20))

        tk.Label(
            self.root,
            text="You've been scrolling too long.\nWait for the timer — then you can continue.",
            font=("Arial", 16),
            fg="#aaaaaa",
            bg="black",
            justify="center",
        ).pack(pady=(0, 40))

        self.timer_label = tk.Label(
            self.root,
            text=str(self.remaining),
            font=("Arial Black", 96, "bold"),
            fg="#ff4444",
            bg="black",
        )
        self.timer_label.pack()

        tk.Label(
            self.root,
            text="seconds",
            font=("Arial", 18),
            fg="#888888",
            bg="black",
        ).pack(pady=(0, 80))

        self.root.focus_force()

    def _tick(self):
        if self.remaining <= 0:
            self.root.destroy()
            self.on_complete()
            return
        self.timer_label.config(text=str(self.remaining))
        # Flash red → orange in last 10 seconds
        color = "#ff4444" if self.remaining > 10 else "#ff8800"
        self.timer_label.config(fg=color)
        self.remaining -= 1
        self.root.after(1000, self._tick)

    def _keyboard_hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0 and wParam == WM_KEYDOWN:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.vkCode in BLOCKED_KEYS:
                return 1  # block the key
        return ctypes.windll.user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def _install_keyboard_hook(self):
        HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        self._hook_func = HOOKPROC(self._keyboard_hook_proc)

        def run_hook():
            self._hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_KEYBOARD_LL, self._hook_func, None, 0
            )
            msg = ctypes.wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        self._hook_thread = threading.Thread(target=run_hook, daemon=True)
        self._hook_thread.start()

    def _uninstall_keyboard_hook(self):
        if self._hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self._hook)


def show_countdown(seconds: int, on_complete: Callable):
    """Convenience function — shows countdown window, calls on_complete when done."""
    w = CountdownWindow(seconds, on_complete)
    w.show()
```

- [ ] **Step 2: Manual smoke test**

```python
# Run this directly to see the countdown:
# python -c "from app.countdown import show_countdown; show_countdown(5, lambda: print('done'))"
```

Expected: Fullscreen black window, countdown from 5, prints "done", window closes.

- [ ] **Step 3: Commit**

```bash
git add app/countdown.py
git commit -m "feat: fullscreen countdown window with keyboard hooks"
```

---

## Task 5: Browser extension — scroll detection

**Files:**
- Create: `extension/manifest.json`
- Create: `extension/content.js`

- [ ] **Step 1: Create `extension/manifest.json`**

```json
{
  "manifest_version": 3,
  "name": "Scroll Blocker",
  "version": "1.0.0",
  "description": "Blocks Facebook, Instagram, YouTube after 2.5 min of active scrolling",
  "permissions": ["tabs", "scripting", "storage"],
  "host_permissions": [
    "https://*.facebook.com/*",
    "https://*.instagram.com/*",
    "https://*.youtube.com/*",
    "http://localhost:7331/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://*.facebook.com/*",
        "https://*.instagram.com/*",
        "https://*.youtube.com/*"
      ],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

- [ ] **Step 2: Create `extension/content.js`**

```javascript
// Detects active scrolling and reports to local Python server
const SERVER = "http://localhost:7331";
const VELOCITY_THRESHOLD = 3;    // scroll events per second = "active"
const REPORT_INTERVAL_MS = 2000; // report every 2 seconds

let scrollEvents = 0;
let activeSeconds = 0;

// Count scroll events
window.addEventListener("scroll", () => { scrollEvents++; }, { passive: true });

const site = location.hostname.replace("www.", "");

setInterval(() => {
  const eventsPerSecond = scrollEvents / (REPORT_INTERVAL_MS / 1000);
  scrollEvents = 0;

  if (eventsPerSecond >= VELOCITY_THRESHOLD) {
    activeSeconds += REPORT_INTERVAL_MS / 1000;

    fetch(`${SERVER}/scroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site, active_seconds: REPORT_INTERVAL_MS / 1000 }),
    }).catch(() => {});  // server might not be running — silent fail
  }
}, REPORT_INTERVAL_MS);
```

- [ ] **Step 3: Commit**

```bash
git add extension/manifest.json extension/content.js
git commit -m "feat: extension content script — scroll velocity detection"
```

---

## Task 6: Browser extension — blocking + background

**Files:**
- Create: `extension/background.js`
- Create: `extension/blocked.html`

- [ ] **Step 1: Create `extension/blocked.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Blocked — Scroll Blocker</title>
  <style>
    body {
      background: #111;
      color: white;
      font-family: Arial Black, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      text-align: center;
    }
    h1 { font-size: 2.5rem; color: #ff4444; margin-bottom: 1rem; }
    p  { font-size: 1.2rem; color: #aaa; max-width: 500px; }
    .timer { font-size: 5rem; color: #ff8800; margin: 2rem 0; }
    button {
      margin-top: 2rem;
      padding: 1rem 2rem;
      font-size: 1rem;
      background: #333;
      color: white;
      border: 1px solid #555;
      border-radius: 8px;
      cursor: pointer;
    }
    button:hover { background: #444; }
  </style>
</head>
<body>
  <h1>🚫 Scroll Limit Reached</h1>
  <p>You've been actively scrolling for too long. A 60-second pause is required.</p>
  <p>The desktop app is showing your countdown. Come back when it's done.</p>
  <button onclick="window.history.back()">← Go back</button>
</body>
</html>
```

- [ ] **Step 2: Create `extension/background.js`**

```javascript
const SERVER = "http://localhost:7331";
const POLL_MS = 2000;

const BLOCKED_PATTERNS = [
  /facebook\.com/,
  /instagram\.com/,
  /youtube\.com/,
];

function isBlockedSite(url) {
  return BLOCKED_PATTERNS.some(p => p.test(url));
}

function getSite(url) {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch { return ""; }
}

// Poll server for block status — redirect blocked tabs
async function checkAndBlock() {
  const tabs = await chrome.tabs.query({ active: true });
  for (const tab of tabs) {
    if (!tab.url || !isBlockedSite(tab.url)) continue;
    const site = getSite(tab.url);
    try {
      const r = await fetch(`${SERVER}/status?site=${site}`);
      const { blocked } = await r.json();
      if (blocked && !tab.url.includes("blocked.html")) {
        chrome.tabs.update(tab.id, {
          url: chrome.runtime.getURL("blocked.html"),
        });
      }
    } catch (_) {}  // server not running — don't block
  }
}

setInterval(checkAndBlock, POLL_MS);

// Also check immediately when a tab is updated
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && isBlockedSite(tab.url)) {
    const site = getSite(tab.url);
    fetch(`${SERVER}/status?site=${site}`)
      .then(r => r.json())
      .then(({ blocked }) => {
        if (blocked) {
          chrome.tabs.update(tabId, {
            url: chrome.runtime.getURL("blocked.html"),
          });
        }
      })
      .catch(() => {});
  }
});
```

- [ ] **Step 3: Commit**

```bash
git add extension/background.js extension/blocked.html
git commit -m "feat: extension background — tab blocking + blocked page"
```

---

## Task 7: Main app + tray icon + autostart

**Files:**
- Create: `app/autostart.py`
- Create: `app/tray.py`
- Create: `app/main.py`

- [ ] **Step 1: Create `app/autostart.py`**

```python
import sys
import winreg

APP_NAME = "ScrollBlocker"

def install():
    """Add app to Windows startup registry."""
    exe_path = sys.executable if not getattr(sys, "frozen", False) else sys.argv[0]
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
    winreg.CloseKey(key)

def uninstall():
    """Remove app from Windows startup registry."""
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

def is_installed() -> bool:
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
```

- [ ] **Step 2: Create `app/tray.py`**

```python
import threading
import pystray
from PIL import Image, ImageDraw
from app import autostart

def _make_icon():
    img = Image.new("RGB", (64, 64), color="#111111")
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, 56, 56], fill="#ff4444")
    draw.text((18, 18), "SB", fill="white")
    return img

def run_tray(on_quit):
    def quit_action(icon, item):
        icon.stop()
        on_quit()

    def toggle_autostart(icon, item):
        if autostart.is_installed():
            autostart.uninstall()
        else:
            autostart.install()

    icon = pystray.Icon(
        "ScrollBlocker",
        _make_icon(),
        "Scroll Blocker — Running",
        menu=pystray.Menu(
            pystray.MenuItem("Scroll Blocker — Active", lambda *_: None, enabled=False),
            pystray.MenuItem(
                "Start with Windows",
                toggle_autostart,
                checked=lambda item: autostart.is_installed()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", quit_action),
        )
    )
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
```

- [ ] **Step 3: Create `app/main.py`**

```python
import threading
import uvicorn
from app.config import (
    SERVER_PORT, ACTIVE_SCROLL_THRESHOLD_SECONDS,
    COUNTDOWN_SECONDS, BLOCKED_SITES
)
from app.tracker import ScrollTracker
from app.server import create_app
from app.countdown import show_countdown
from app.tray import run_tray

tracker = ScrollTracker(
    threshold=ACTIVE_SCROLL_THRESHOLD_SECONDS,
    cooldown=COUNTDOWN_SECONDS
)

def on_block_triggered(site: str):
    """Called when a site crosses the threshold — show countdown then unblock."""
    def _run():
        def on_done():
            tracker.unblock(site)
        show_countdown(COUNTDOWN_SECONDS, on_complete=on_done)
    threading.Thread(target=_run, daemon=False).start()

# Patch tracker to trigger countdown
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
    print("🚫 Scroll Blocker starting...")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    import autostart as _autostart
    if not _autostart.is_installed():
        _autostart.install()
        print("✅ Added to Windows startup")

    icon = run_tray(on_quit=lambda: exit(0))
    print(f"✅ Running on localhost:{SERVER_PORT} — tray icon active")
    server_thread.join()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Fix import in main.py** (use correct module path)

Replace `import autostart as _autostart` with `from app import autostart as _autostart`

- [ ] **Step 5: Smoke test — run the app**

```bash
python -m app.main
```

Expected: tray icon appears in Windows system tray, server running. Check `http://localhost:7331/status?site=youtube.com` in browser — should return `{"blocked": false}`.

- [ ] **Step 6: Commit**

```bash
git add app/autostart.py app/tray.py app/main.py
git commit -m "feat: main app, tray icon, autostart registry"
```

---

## Task 8: Load extension into Chrome/Edge

**Files:**
- Create: `extension/install-instructions.md`

- [ ] **Step 1: Load unpacked extension in Chrome**

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select `C:\Users\Roy\Downloads\scroll-blocker\extension`
5. Confirm extension appears as "Scroll Blocker"

- [ ] **Step 2: Load in Edge (same steps)**

1. Open Edge → `edge://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select `extension/` folder

- [ ] **Step 3: Verify end-to-end**

1. Start Python app: `python -m app.main`
2. Open `https://www.youtube.com` in Chrome
3. Scroll fast for ~3 minutes
4. Expected: fullscreen countdown appears on desktop, browser tab redirects to `blocked.html`
5. Wait 60s → countdown ends → can browse YouTube again

- [ ] **Step 4: Commit**

```bash
git add extension/install-instructions.md
git commit -m "docs: extension install instructions"
```

---

## Task 9: Build distributable .exe

**Files:**
- Create: `build.py`

- [ ] **Step 1: Install PyInstaller**

```bash
pip install pyinstaller==6.10.0
```

- [ ] **Step 2: Create `build.py`**

```python
import subprocess, sys

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",          # no console window
    "--name", "ScrollBlocker",
    "--icon", "NONE",
    "--add-data", "app;app",
    "app/main.py",
]
subprocess.run(cmd, check=True)
print("\n✅ Built: dist/ScrollBlocker.exe")
print("Share this .exe + the extension/ folder.")
```

- [ ] **Step 3: Build**

```bash
python build.py
```

Expected: `dist/ScrollBlocker.exe` created (~15-20MB).

- [ ] **Step 4: Test the .exe**

```bash
dist\ScrollBlocker.exe
```

Expected: tray icon appears, no console window.

- [ ] **Step 5: Final commit**

```bash
git add build.py
git commit -m "feat: PyInstaller build script → ScrollBlocker.exe"
```

---

## Summary

After all tasks, you'll have:

```
scroll-blocker/
  app/           ← Python app (server + tracker + countdown + tray)
  extension/     ← Chrome/Edge extension (load unpacked)
  dist/          ← ScrollBlocker.exe (run once, lives in tray)
  tests/         ← unit + integration tests
```

**To use:**
1. Run `ScrollBlocker.exe` once → it auto-starts on every boot
2. Load `extension/` as unpacked extension in Chrome/Edge
3. Done — אחי will watch your scrolling 👁️
