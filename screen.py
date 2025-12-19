import pyautogui


def capture_screen(path="screen.png"):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return path
