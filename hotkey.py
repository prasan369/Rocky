import keyboard
import threading

def on_hotkey(app):
    thread = threading.Thread(target=app.show)
    thread.daemon = True
    thread.start()

def start_hotkey_listener(app):
    keyboard.add_hotkey("ctrl+space", lambda: on_hotkey(app))
    keyboard.wait()