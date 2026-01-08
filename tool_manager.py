import os
import time
import uuid
import threading
import pyautogui
import pytesseract
import cv2
import numpy as np
import pygetwindow as gw
import yt_dlp
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

# ===================== REGISTRY =====================

class ToolsManager:
    """Central registry for all JARVIS capabilities."""
    _tools = {}

    @classmethod
    def register(cls, name):
        def decorator(func):
            cls._tools[name] = func
            return func
        return decorator

    @classmethod
    def get_all_tools(cls):
        return cls._tools

# ===================== VISION ENGINE =====================

# 🔧 Update this path if Tesseract is installed elsewhere
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_vision_lock = threading.Lock()
_last_vision_time = 0.0
VISION_COOLDOWN = 10 

def get_active_window_info():
    """Returns metadata about the currently focused window."""
    try:
        win = gw.getActiveWindow()
        if not win or win.title == "":
            return "Desktop"
        return f"{win.title} ({win.width}x{win.height})"
    except:
        return "Unknown Window"

# ===================== MUSIC ENGINE =====================

_current_playback = None  # Holds the current playing object to stop it later

@ToolsManager.register("play_music")
def play_music(query: str):
    """Searches YouTube, downloads audio, and plays it in the background."""
    global _current_playback
    
    track_id = str(uuid.uuid4())[:8]
    filename = f"temp_{track_id}.wav"

    def run_engine():
        global _current_playback
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': f"temp_{track_id}.%(ext)s",
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{query}"])
            
            if os.path.exists(filename):
                audio = AudioSegment.from_wav(filename)
                # _play_with_simpleaudio is non-blocking and returns a controller
                _current_playback = _play_with_simpleaudio(audio)
                
                # Wait for song to finish or be stopped, then cleanup
                while _current_playback.is_playing():
                    time.sleep(1)
                os.remove(filename)
        except Exception as e:
            print(f"Music Engine Error: {e}")

    threading.Thread(target=run_engine, daemon=True).start()
    return f"Searching for {query}. I'll start the playback shortly, sir."

@ToolsManager.register("stop_music")
def stop_music(args=None):
    """Stops any currently playing audio."""
    global _current_playback
    if _current_playback and _current_playback.is_playing():
        _current_playback.stop()
        return "Music stopped, sir."
    return "No music is currently playing."

# ===================== UTILITY TOOLS =====================

@ToolsManager.register("get_time")
def get_time(args=None):
    """Returns the current local time."""
    return f"The current time is {time.strftime('%I:%M %p')}."