import os
import time
import json
import queue
import logging
import datetime
import requests
import tempfile
from pydub import AudioSegment
import simpleaudio as sa
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import edge_tts
import asyncio
from dotenv import load_dotenv

# ===================== ENV & LOGGING =====================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ===================== GLOBAL STATE =====================
is_speaking = False
assistant_active = False
interrupt_requested = False

# ===================== SESSION MEMORY =====================
MAX_TURNS = 6
conversation_turns = []

BASE_SYSTEM_PROMPT = """
You are Jarvis, a helpful AI assistant.
You remember context only during this session like ChatGPT.
Use prior context naturally.
Do not claim long-term memory unless explicitly told.
"""

# ===================== PERSISTENT MEMORY =====================
MEMORY_FILE = "jarvis_memory.json"

def load_persistent_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"profile": {}}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_persistent_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

persistent_memory = load_persistent_memory()

def extract_and_store_memory(text):
    text = text.lower()
    profile = persistent_memory["profile"]
    updated = False

    if "my name is" in text:
        profile["name"] = text.split("my name is")[-1].strip()
        updated = True
    elif "i live in" in text:
        profile["location"] = text.split("i live in")[-1].strip()
        updated = True
    elif "i am a" in text:
        profile["profession"] = text.split("i am a")[-1].strip()
        updated = True
    elif "remember that i like" in text:
        profile["likes"] = text.split("remember that i like")[-1].strip()
        updated = True

    if updated:
        save_persistent_memory(persistent_memory)
        return True
    return False

# ===================== VOSK =====================
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
vosk_model = Model(VOSK_MODEL_PATH)
audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    audio_queue.put(bytes(indata))

def takeCommand(timeout=8):
    global is_speaking
    while is_speaking:
        time.sleep(0.1)

    while not audio_queue.empty():
        audio_queue.get()

    rec = KaldiRecognizer(vosk_model, 16000)
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        start = time.time()
        while time.time() - start < timeout:
            if not audio_queue.empty():
                if rec.AcceptWaveform(audio_queue.get()):
                    text = json.loads(rec.Result()).get("text", "").lower()
                    if text:
                        logging.info(f"User: {text}")
                        return text
    return None

# ===================== TTS =====================
JARVIS_VOICE = "en-GB-RyanNeural"

async def speak_async(text):
    global is_speaking, interrupt_requested
    try:
        is_speaking = True

        mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

        await edge_tts.Communicate(text, JARVIS_VOICE).save(mp3)

        audio = AudioSegment.from_mp3(mp3)
        audio.set_frame_rate(16000).set_channels(1).set_sample_width(2).export(wav, "wav")

        play = sa.WaveObject.from_wave_file(wav).play()
        while play.is_playing():
            if interrupt_requested:
                play.stop()
                break
            time.sleep(0.05)

        os.remove(mp3)
        os.remove(wav)

    finally:
        interrupt_requested = False
        is_speaking = False

def speak(text):
    asyncio.run(speak_async(text))

# ===================== GROQ =====================
def getGroqResponse(prompt):
    conversation_turns.append({"role": "user", "content": prompt})
    conversation_turns[:] = conversation_turns[-MAX_TURNS * 2:]

    messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]

    if persistent_memory["profile"]:
        messages.append({
            "role": "system",
            "content": f"User profile: {json.dumps(persistent_memory['profile'])}"
        })

    messages.extend(conversation_turns)

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 256,
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    r.raise_for_status()
    data = r.json()
    reply = data["choices"][0]["message"]["content"].strip()

    conversation_turns.append({"role": "assistant", "content": reply})
    return reply

# ===================== COMMANDS =====================
WAKE_WORDS = ["jarvis", "hey jarvis", "hello jarvis"]
STOP_WORDS = ["stop", "jarvis stop", "cancel", "go to sleep"]

def processQuery(query):
    global assistant_active, interrupt_requested

    if extract_and_store_memory(query):
        speak("Got it. I will remember that.")
        return True

    if any(query == w or query.endswith(w) for w in STOP_WORDS):
        interrupt_requested = True
        assistant_active = False
        speak("Going silent.")
        return False

    if "time" in query:
        speak(datetime.datetime.now().strftime("%I:%M %p"))
        return True

    speak(getGroqResponse(query))
    return True

# ===================== MAIN LOOP =====================
def listenForWakeWord():
    global assistant_active
    logging.info("Waiting for wake word...")

    while True:
        text = takeCommand()
        if not text:
            continue

        if text in WAKE_WORDS or text.endswith(" jarvis"):
            assistant_active = True
            speak("Yes?")
            while assistant_active:
                if not processQuery(takeCommand()):
                    break

if __name__ == "__main__":
    listenForWakeWord()
