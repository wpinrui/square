import ctypes
import json
import os
import queue
import sys
import tkinter as tk
import winreg

import pystray
from PIL import Image, ImageDraw

GREY = "#808080"
EDGE = 8
MIN_SIZE = 30
CONFIG = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "square", "config.json")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

CURSORS = {
    "l": "size_we", "r": "size_we", "t": "size_ns", "b": "size_ns",
    "lt": "size_nw_se", "rb": "size_nw_se", "rt": "size_ne_sw", "lb": "size_ne_sw",
}


class Square:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.root, bg=GREY, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        cfg = self.load()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = cfg.get("w", 300), cfg.get("h", 120)
        x, y = cfg.get("x", (sw - w) // 2), cfg.get("y", (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.locked = cfg.get("locked", False)
        self.visible = "--hidden" not in sys.argv
        if not self.visible:
            self.root.withdraw()
        self.drag = None
        self.startup = cfg.get("startup", True)
        self.apply_startup()

        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double)
        self.canvas.bind("<Configure>", lambda e: self.draw_border())

        self.events = queue.Queue()
        self.icon = pystray.Icon("square", self.tray_image(), "Square", pystray.Menu(
            pystray.MenuItem("Show/Hide", lambda icon, item: self.events.put("toggle"), default=True),
            pystray.MenuItem("Reset", lambda icon, item: self.events.put("reset")),
            pystray.MenuItem("Launch on startup", lambda icon, item: self.events.put("startup"),
                             checked=lambda item: self.startup),
            pystray.MenuItem("Quit", lambda icon, item: self.events.put("quit")),
        ))
        self.icon.run_detached()
        self.root.after(100, self.poll)

    def load(self):
        try:
            with open(CONFIG) as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w") as f:
            json.dump({
                "x": self.root.winfo_x(), "y": self.root.winfo_y(),
                "w": self.root.winfo_width(), "h": self.root.winfo_height(),
                "locked": self.locked, "startup": self.startup,
            }, f)

    def apply_startup(self):
        # Only the installed exe registers itself, so running from source never autostarts.
        if not getattr(sys, "frozen", False):
            return
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if self.startup:
                winreg.SetValueEx(key, "square", 0, winreg.REG_SZ, f'"{sys.executable}" --hidden')
            else:
                try:
                    winreg.DeleteValue(key, "square")
                except FileNotFoundError:
                    pass

    def tray_image(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(img).rectangle((8, 8, 56, 56), fill=GREY, outline="white", width=3)
        return img

    def draw_border(self):
        self.canvas.delete("border")
        if not self.locked:
            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.create_rectangle(1, 1, w - 2, h - 2, outline="white", width=2, tags="border")

    def edges(self, x, y):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        mode = ""
        if x < EDGE:
            mode += "l"
        elif x >= w - EDGE:
            mode += "r"
        if y < EDGE:
            mode += "t"
        elif y >= h - EDGE:
            mode += "b"
        return mode

    def on_motion(self, e):
        if self.locked:
            self.canvas.config(cursor="arrow")
        else:
            self.canvas.config(cursor=CURSORS.get(self.edges(e.x, e.y), "fleur"))

    def on_press(self, e):
        if self.locked:
            return
        self.drag = (self.edges(e.x, e.y), e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(),
                     self.root.winfo_width(), self.root.winfo_height())

    def on_drag(self, e):
        if self.locked or not self.drag:
            return
        mode, px, py, x, y, w, h = self.drag
        dx, dy = e.x_root - px, e.y_root - py
        if not mode:
            x, y = x + dx, y + dy
        if "l" in mode:
            dx = min(dx, w - MIN_SIZE)
            x, w = x + dx, w - dx
        if "r" in mode:
            w = max(MIN_SIZE, w + dx)
        if "t" in mode:
            dy = min(dy, h - MIN_SIZE)
            y, h = y + dy, h - dy
        if "b" in mode:
            h = max(MIN_SIZE, h + dy)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def on_release(self, e):
        if self.drag:
            self.drag = None
            self.save()

    def on_double(self, e):
        self.drag = None
        self.locked = not self.locked
        self.draw_border()
        self.on_motion(e)
        self.save()

    def poll(self):
        while not self.events.empty():
            event = self.events.get()
            if event == "toggle":
                if self.visible:
                    self.root.withdraw()
                else:
                    self.root.deiconify()
                    self.root.attributes("-topmost", True)
                self.visible = not self.visible
            elif event == "reset":
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                self.root.geometry(f"100x100+{(sw - 100) // 2}+{(sh - 100) // 2}")
                self.locked = False
                if not self.visible:
                    self.root.deiconify()
                    self.visible = True
                self.root.attributes("-topmost", True)
                self.root.update_idletasks()
                self.draw_border()
                self.save()
            elif event == "startup":
                self.startup = not self.startup
                self.apply_startup()
                self.icon.update_menu()
                self.save()
            elif event == "quit":
                self.save()
                self.icon.stop()
                self.root.destroy()
                return
        self.root.after(100, self.poll)


if __name__ == "__main__":
    Square().root.mainloop()
