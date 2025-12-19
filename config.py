import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSISTANT_NAME = "FRIDAY"
WAKE_WORD = "friday"

# Absolute Vosk model path (your real path)
VOSK_MODEL_PATH = r"C:\Users\raksh\OneDrive\Desktop\J.A.R.V.I.S\vosk-model-en-us-0.22"

# Whisper (offline, accurate)
WHISPER_MODEL = "small"

# Groq
GROQ_MODEL = "llama-3.3-70b-versatile"
