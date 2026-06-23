import tkinter as tk
import queue
import threading
import keyboard

open_queue = queue.Queue()

def on_hotkey():
    open_queue.put("open")

def start_hotkey():
    keyboard.add_hotkey("ctrl+space", on_hotkey)
    keyboard.wait()

root = tk.Tk()
root.withdraw()

def check_queue():
    try:
        msg = open_queue.get_nowait()
        if msg == "open":
            # simple test window
            win = tk.Toplevel(root)
            win.geometry("300x200")
            win.title("Test")
            tk.Label(win, text="It works!").pack(pady=50)
    except:
        pass
    root.after(100, check_queue)

hotkey_thread = threading.Thread(target=start_hotkey)
hotkey_thread.daemon = True
hotkey_thread.start()

root.after(100, check_queue)
root.mainloop()