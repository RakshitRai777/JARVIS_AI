import pyautogui
from logger import info

def capture_screen(path="screen.png"):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    info(f"Screen captured: {path}")
    return path
