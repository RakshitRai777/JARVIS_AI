import pyautogui
import pytesseract
import cv2
import numpy as np
import pygetwindow as gw
import os
import tempfile

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def get_active_window():
    try:
        win = gw.getActiveWindow()
        if win:
            return {
                "title": win.title,
                "width": win.width,
                "height": win.height
            }
    except:
        pass
    return None


def extract_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    return pytesseract.image_to_string(gray)


def get_vision_analysis(query, session, api_key):
    # 1️⃣ Screenshot
    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 2️⃣ OCR
    text = extract_text(img)
    text = text.strip()

    # 3️⃣ Active window
    window = get_active_window()

    # 4️⃣ Build structured observation
    observation = {
        "active_window": window,
        "screen_resolution": screenshot.size,
        "visible_text_sample": text[:1500] if text else "No readable text detected"
    }

    # 5️⃣ Ask Groq to reason
    prompt = f"""
You are Jarvis with human-like vision understanding.

OBSERVATION FROM SCREEN:
{observation}

USER QUESTION:
{query}

Explain what is on the screen and answer the user's question.
Be precise and factual. Do not hallucinate.
"""

    r = session.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 400
        },
        timeout=15
    )

    return r.json()["choices"][0]["message"]["content"]
