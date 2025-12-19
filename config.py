import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSISTANT_NAME = "FRIDAY"
WAKE_WORD = "friday"

VOSK_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "vosk-model-small-en-us-0.15"
)

GROQ_MODEL = "llama-3.3-70b-versatile"
