import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from config import WAKE_WORD, VOSK_MODEL_PATH

class WakeWordDetector:
    def __init__(self):
        self.model = Model(VOSK_MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)

    def listen(self):
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1
        ) as stream:
            while True:
                data, _ = stream.read(4000)
                if self.recognizer.AcceptWaveform(bytes(data)):
                    text = json.loads(self.recognizer.Result()).get("text", "").lower()
                    if WAKE_WORD in text:
                        self.recognizer.Reset()
                        return True
