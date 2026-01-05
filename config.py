import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    MEMORY_FILE = "jarvis_memory.json"

    SAMPLE_RATE = 16000
    CHANNELS = 1
    AUDIO_CHUNK = 4096

    VOICE = "en-GB-RyanNeural"

    UI_WIDTH = 1000
    UI_HEIGHT = 700

    @classmethod
    def validate(cls):
        if not cls.GROQ_API_KEY:
            raise RuntimeError("❌ GROQ_API_KEY missing in .env")

Config.validate()
