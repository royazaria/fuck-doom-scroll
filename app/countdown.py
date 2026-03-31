import tkinter as tk
import ctypes
import ctypes.wintypes
import threading
from typing import Callable

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
VK_LWIN = 0x5B
VK_RWIN = 0x5C

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

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<FocusOut>", lambda e: self.root.after(100, self.root.focus_force))
        self.root.bind("<Escape>", lambda e: None)
        self.root.bind("<Alt-F4>", lambda e: None)

        tk.Label(
            self.root,
            text="PUT DOWN YOUR PHONE",
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
        color = "#ff4444" if self.remaining > 10 else "#ff8800"
        self.timer_label.config(fg=color)
        self.remaining -= 1
        self.root.after(1000, self._tick)

    def _keyboard_hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0 and wParam == WM_KEYDOWN:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.vkCode in BLOCKED_KEYS:
                return 1
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
    w = CountdownWindow(seconds, on_complete)
    w.show()
