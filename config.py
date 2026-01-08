import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env once, early
load_dotenv()


class Config:
    # ===================== ENV =====================
    ENV = os.getenv("JARVIS_ENV", "production").lower()

    # ===================== API KEYS =====================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # ===================== PATHS =====================
    BASE_DIR = Path(__file__).resolve().parent
    MEMORY_FILE = BASE_DIR / "jarvis_memory.json"

    # ===================== AUDIO =====================
    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_CHUNK = 4096

    # ===================== VOICE =====================
    VOICE = os.getenv("JARVIS_VOICE", "en-GB-RyanNeural")

    # ===================== UI =====================
    UI_WIDTH = int(os.getenv("JARVIS_UI_WIDTH", 1000))
    UI_HEIGHT = int(os.getenv("JARVIS_UI_HEIGHT", 700))

    # ===================== VALIDATION =====================
    @classmethod
    def validate(cls, strict: bool = True):
        """
        Validates required configuration.
        strict=True  -> crash on missing critical values
        strict=False -> warn only (useful for UI / tests)
        """
        errors = []

        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY missing in .env")

        if errors:
            msg = "❌ Config error(s):\n" + "\n".join(f"- {e}" for e in errors)
            if strict:
                raise RuntimeError(msg)
            else:
                print(msg)

        return True

# Auto-validate in production
if Config.ENV == "production":
    Config.validate(strict=True)
