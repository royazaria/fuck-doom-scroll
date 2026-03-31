# F*CK Doom Scroll 🚫📱

Windows desktop app that detects active scrolling on Facebook, Instagram, YouTube — and blocks you behind a 60-second fullscreen countdown you can't dismiss.

## Project layout

```
fuck-doom-scroll/
  app/              Python app (FastAPI server + tracker + countdown + tray)
  extension/        Chrome/Edge browser extension (load unpacked)
  tests/            pytest unit + integration tests
  docs/plans/       Implementation plan
  dist/             Built .exe output (after build)
  logo.png          Project logo
```

## Plan

Full step-by-step plan: `docs/plans/2026-03-31-scroll-blocker.md`

## Current status

- [x] Project structure created
- [x] Implementation plan written
- [ ] Task 1: Bootstrap + config
- [ ] Task 2: Scroll tracker logic
- [ ] Task 3: Local HTTP server
- [ ] Task 4: Fullscreen countdown window
- [ ] Task 5: Browser extension — scroll detection
- [ ] Task 6: Browser extension — blocking
- [ ] Task 7: Main app + tray + autostart
- [ ] Task 8: Load extension into Chrome/Edge
- [ ] Task 9: Build .exe

## How to continue in a new chat

Open this folder in Claude Code:
```
cd C:\Users\Roy\Downloads\fuck-doom-scroll
```
Then say: **"continue building fuck-doom-scroll from the plan"**

## Tech stack

- Python 3.11, FastAPI, uvicorn, tkinter, pywin32, pystray, Pillow
- Chrome/Edge Manifest V3 extension
- PyInstaller for .exe

## Run locally

```bash
cd C:\Users\Roy\Downloads\fuck-doom-scroll
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```
