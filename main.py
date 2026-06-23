import tkinter as tk
import queue
import threading
import pystray
from PIL import Image, ImageDraw
import keyboard
from gui import RockyGUI

open_queue = queue.Queue()
app = RockyGUI()

def create_icon():
    img = Image.new("RGB", (64, 64), color="#1a1a1a")
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill="#8b90d6")
    return img

def on_hotkey():
    open_queue.put("open")

def start_hotkey():
    keyboard.add_hotkey("ctrl+space", on_hotkey)
    keyboard.wait()

def main():
    hotkey_thread = threading.Thread(target=start_hotkey)
    hotkey_thread.daemon = True
    hotkey_thread.start()

    root = tk.Tk()
    root.withdraw()

    icon = pystray.Icon(
        "Rocky",
        create_icon(),
        "Rocky — Ctrl+Space to open",
        menu=pystray.Menu(
            pystray.MenuItem("Quit", lambda: icon.stop())
        )
    )
    tray_thread = threading.Thread(target=icon.run)
    tray_thread.daemon = True
    tray_thread.start()

    def check_queue():
        try:
            msg = open_queue.get_nowait()
            if msg == "open":
                app.show(root)
        except:
            pass
        root.after(100, check_queue)

    root.after(100, check_queue)
    root.mainloop()

if __name__ == "__main__":
    main()