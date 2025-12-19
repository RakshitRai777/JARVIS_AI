import os
import sounddevice as sd
from groq_ai import GroqAI
from memory import get_short_context
from config import VOSK_MODEL_PATH

def check_microphone():
    try:
        sd.query_devices(kind="input")
        return True
    except Exception:
        return False

def check_groq():
    try:
        ai = GroqAI()
        ai.ask("Say OK")
        return True
    except Exception:
        return False

def check_vosk():
    return os.path.exists(VOSK_MODEL_PATH)

def run_health_check():
    report = {
        "Microphone": check_microphone(),
        "Groq API": check_groq(),
        "Vosk Model": check_vosk(),
        "Memory": bool(get_short_context())
    }

    print("\n🩺 JARVIS HEALTH REPORT")
    for k, v in report.items():
        print(f"{k}: {'✅ OK' if v else '❌ FAIL'}")

    return report

if __name__ == "__main__":
    run_health_check()
