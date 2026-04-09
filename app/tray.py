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
        "FuckDoomScroll",
        _make_icon(),
        "F*CK Doom Scroll — Running",
        menu=pystray.Menu(
            pystray.MenuItem("F*CK Doom Scroll — Active", lambda *_: None, enabled=False),
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
