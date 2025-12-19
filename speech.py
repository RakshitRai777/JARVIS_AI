# speech.py
import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile

print("🔊 Loading Whisper model...")
model = whisper.load_model("base")  # or "small"


def listen_command(duration=5):
    samplerate = 16000
    print("🎤 Listening...")

    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, samplerate, recording)
        result = model.transcribe(f.name)

    text = result["text"].strip()
    print(f"🧠 Heard: {text}")
    return text
