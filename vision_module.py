# vision_module.py
"""
JARVIS Vision Module
--------------------
• Screen capture
• OCR (Tesseract)
• Active window context
• Cooldown-protected
• Thread-safe
• Crash-proof
• 24/7 safe
"""

import time
import threading
import pyautogui
import pytesseract
import cv2
import numpy as np
import pygetwindow as gw

# ===================== CONFIG =====================

# 🔧 Update this path if Tesseract is installed elsewhere
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

VISION_COOLDOWN = 10  # seconds

_last_vision_time = 0.0
_vision_lock = threading.Lock()


# ===================== HELPERS =====================

def get_active_window():
    """
    Returns active window metadata safely.
    """
    try:
        win = gw.getActiveWindow()
        if not win:
            return None

        return {
            "title": win.title or "Unknown",
            "width": win.width,
            "height": win.height
        }
    except Exception:
        return None


def extract_text(image: np.ndarray) -> str:
    """
    OCR extraction with preprocessing.
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
        return pytesseract.image_to_string(gray)
    except Exception:
        return ""


# ===================== MAIN API =====================

def get_vision_analysis(query: str, session, api_key: str) -> str:
    """
    Performs:
    • Screenshot
    • OCR
    • Active window detection
    • Groq reasoning

    Thread-safe and cooldown-protected.
    """

    global _last_vision_time

    # ===================== COOLDOWN =====================

    with _vision_lock:
        now = time.time()
        elapsed = now - _last_vision_time

        if elapsed < VISION_COOLDOWN:
            remaining = int(VISION_COOLDOWN - elapsed)
            return f"Please wait {remaining} seconds before another screen analysis."

        _last_vision_time = now

    # ===================== SCREEN CAPTURE =====================

    try:
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception:
        return "I couldn't capture the screen."

    # ===================== OCR =====================

    text = extract_text(img).strip()

    # ===================== ACTIVE WINDOW =====================

    window = get_active_window()

    # ===================== OBSERVATION =====================

    observation = {
        "active_window": window,
        "screen_resolution": screenshot.size,
        "visible_text_sample": (
            text[:1500] if text else "No readable text detected"
        )
    }

    # ===================== PROMPT =====================

    prompt = f"""
You are JARVIS with human-like visual understanding.

OBSERVATION:
{observation}

USER QUESTION:
{query}

Rules:
- Be precise and factual
- Do NOT hallucinate
- If unsure, say so clearly
"""

    # ===================== GROQ REQUEST =====================

    try:
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

        data = r.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "I couldn't understand the screen clearly.")
        )

    except Exception:
        return "I encountered an error while analyzing the screen."
