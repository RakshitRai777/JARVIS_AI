import sounddevice as sd
from vosk import Model, KaldiRecognizer
import queue

print("Testing Vosk installation...")

# List audio devices
print("\nAvailable audio devices:")
print(sd.query_devices())

# Test model loading
try:
    model = Model("models/vosk-model-en-us-0.22")
    print("\n✅ Vosk model loaded successfully!")
except Exception as e:
    print(f"\n❌ Failed to load Vosk model: {e}")