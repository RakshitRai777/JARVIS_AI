from vosk import Model
from config import VOSK_MODEL_PATH

print("Loading model from:", VOSK_MODEL_PATH)
model = Model(VOSK_MODEL_PATH)
print("✅ Vosk model loaded successfully")
