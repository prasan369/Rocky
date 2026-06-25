import os
import subprocess
import pyautogui
from langchain.tools import tool
import screen_brightness_control as sbc

@tool
def control_volume(action: str) -> str:
    """Controls system volume. Actions: 'up', 'down', 'mute', 'unmute'.
    Only call this tool ONCE per request."""
    try:
        print(f"VOLUME ACTION: {action}")
        if action == "up":
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Volume increased. Do not call this tool again."
        elif action == "down":
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Volume decreased. Do not call this tool again."
        elif action == "mute":
            pyautogui.press("volumemute")
            return "Volume muted. Do not call this tool again."
        elif action == "unmute":
            pyautogui.press("volumemute")
            return "Volume unmuted. Do not call this tool again."
        else:
            return f"Unknown action: {action}. Use up, down, mute, or unmute."
    except Exception as e:
        print(f"VOLUME ERROR: {str(e)}")
        return f"Volume control error: {str(e)}"


@tool
def take_screenshot(filename: str = "") -> str:
    """Takes a screenshot and saves it to the desktop.
    Only call this tool ONCE per request."""
    try:
        from datetime import datetime
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        return f"Screenshot saved to {path}. Do not call this tool again."
    except Exception as e:
        return f"Screenshot error: {str(e)}"


@tool
def lock_pc(confirm: str = "") -> str:
    """Locks the PC/Windows session.
    Only call this tool ONCE per request."""
    try:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "PC locked. Do not call this tool again."
    except Exception as e:
        return f"Lock error: {str(e)}"


@tool
def control_brightness(action: str) -> str:
    """Controls screen brightness. Actions: 'up', 'down', or 'set 50' (0-100).
    Only call this tool ONCE per request."""
    try:
        current = sbc.get_brightness()[0]

        if action == "up":
            new = min(100, current + 10)
            sbc.set_brightness(new)
            return f"Brightness increased to {new}%. Do not call this tool again."
        elif action == "down":
            new = max(0, current - 10)
            sbc.set_brightness(new)
            return f"Brightness decreased to {new}%. Do not call this tool again."
        elif action.startswith("set"):
            level = int(action.split()[-1])
            sbc.set_brightness(level)
            return f"Brightness set to {level}%. Do not call this tool again."
        else:
            return f"Unknown action: {action}. Use up, down, or set 0-100."
    except Exception as e:
        return f"Brightness error: {str(e)}"