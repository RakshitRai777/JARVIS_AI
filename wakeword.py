# wakeword.py
import json
import os
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from config import WAKE_WORD, VOSK_MODEL_PATH


class WakeWordDetector:
    def __init__(self):
        print("🎧 Loading wake word model...")
        print(f"📂 Using model: {VOSK_MODEL_PATH}")

        if not os.path.exists(VOSK_MODEL_PATH):
            raise RuntimeError(f"❌ Vosk model not found at: {VOSK_MODEL_PATH}")

        self.model = Model(VOSK_MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)

    def listen(self):
        print("🔥 Say 'FRIDAY' to wake me.")

        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
        ) as stream:
            while True:
                data, _ = stream.read(4000)

                # ✅ CRITICAL FIX (buffer → bytes)
                data_bytes = bytes(data)

                if self.recognizer.AcceptWaveform(data_bytes):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()

                    if WAKE_WORD in text:
                        print("🟢 Wake word detected!")
                        self.recognizer.Reset()
                        return True
