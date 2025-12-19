import whisper
import sounddevice as sd
import scipy.io.wavfile as wav

MODEL = "small"   # you can change to "base" if you want faster
SAMPLE_RATE = 16000
AUDIO_FILE = "test.wav"

print("🔊 Loading Whisper model...")
model = whisper.load_model(MODEL)

print("🎤 Recording for 5 seconds...")
audio = sd.rec(
    int(5 * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16"
)
sd.wait()

wav.write(AUDIO_FILE, SAMPLE_RATE, audio)

print("🧠 Transcribing...")
result = model.transcribe(
    AUDIO_FILE,
    fp16=False,
    language="en",
    task="transcribe"
)

print("🗣️ You said:", result["text"])
