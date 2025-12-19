import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from interrupt import trigger_interrupt
from config import VOSK_MODEL_PATH

INTERRUPT_WORDS = ["stop", "cancel", "wait", "enough"]

model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

def interrupt_listener():
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1
    ) as stream:
        while True:
            data, _ = stream.read(4000)
            if recognizer.AcceptWaveform(bytes(data)):
                text = json.loads(recognizer.Result()).get("text", "").lower()
                if any(word in text for word in INTERRUPT_WORDS):
                    trigger_interrupt()
