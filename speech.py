import os
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from config import VOSK_MODEL_PATH
from logger import info, warn, debug

if not os.path.exists(VOSK_MODEL_PATH):
    raise RuntimeError(f"Vosk model not found at: {VOSK_MODEL_PATH}")

SAMPLE_RATE = 16000
model = Model(VOSK_MODEL_PATH)

def listen_command(timeout=6) -> str:
    info("Listening for user command")
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
    ) as stream:

        for _ in range(int(timeout * 2)):
            data, _ = stream.read(4000)
            if recognizer.AcceptWaveform(bytes(data)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                recognizer.Reset()

                if text:
                    info(f"Recognized speech: {text}")
                    return text

    warn("No command recognized")
    return ""
