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
    raise RuntimeError("GROQ_API_KEY not found in .env file")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ===================== GLOBAL STATE =====================
is_speaking = False

# ===================== VOSK SETUP =====================
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"

if not os.path.exists(VOSK_MODEL_PATH):
    raise RuntimeError("Vosk model folder not found")

vosk_model = Model(VOSK_MODEL_PATH)
audio_queue = queue.Queue()

# ===================== AUDIO CALLBACK =====================
def audio_callback(indata, frames, time_info, status):
    if status:
        logging.warning(status)
    audio_queue.put(bytes(indata))

# ===================== SPEECH INPUT =====================
def takeCommand(timeout=8):
    global is_speaking

    # 🔒 Do not listen while speaking
    while is_speaking:
        time.sleep(0.1)

    # 🔥 Clear mic buffer
    while not audio_queue.empty():
        audio_queue.get()

    rec = KaldiRecognizer(vosk_model, 16000)
    rec.SetWords(False)

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
                data = audio_queue.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()
                    if text:
                        logging.info(f"User: {text}")
                        return text
    return None

# ===================== TEXT TO SPEECH =====================
JARVIS_VOICE = "en-GB-RyanNeural"

async def speak_async(text):
    global is_speaking
    try:
        is_speaking = True

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_f:
            mp3_file = mp3_f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_f:
            wav_file = wav_f.name

        # 🔊 Edge-TTS (MP3 output)
        communicate = edge_tts.Communicate(text=text, voice=JARVIS_VOICE)
        await communicate.save(mp3_file)

        # 🔁 Convert MP3 → PCM WAV
        audio = AudioSegment.from_mp3(mp3_file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_file, format="wav")

        # 🔊 Play PCM WAV (reliable)
        wave_obj = sa.WaveObject.from_wave_file(wav_file)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        os.remove(mp3_file)
        os.remove(wav_file)

    except Exception as e:
        logging.error(f"TTS Error: {e}")
    finally:
        is_speaking = False



def speak(text):
    asyncio.run(speak_async(text))

# ===================== GROQ AI =====================
def getGroqResponse(prompt):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
            "max_tokens": 256,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logging.error(f"Groq Error: {e}")
        return "I'm having trouble accessing my AI core."

# ===================== GREETING =====================
def wishMe():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning. I am Jarvis.")
    elif hour < 18:
        speak("Good afternoon. I am Jarvis.")
    else:
        speak("Good evening. I am Jarvis.")
    speak("How can I assist you?")

# ===================== COMMAND HANDLER =====================
def processQuery(query):
    if not query:
        return True

    if "exit" in query or "bye" in query:
        speak("Goodbye.")
        return False

    if "time" in query:
        speak(datetime.datetime.now().strftime("%I:%M %p"))
        return True

    response = getGroqResponse(query)
    speak(response)
    return True

# ===================== WAKE WORD LOOP =====================
def listenForWakeWord():
    wake_words = ["jarvis", "hey jarvis", "hello jarvis"]
    logging.info("Waiting for wake word...")

    while True:
        text = takeCommand()
        if text and any(w in text for w in wake_words):

            # 🔥 Flush mic buffer
            while not audio_queue.empty():
                audio_queue.get()

            wishMe()

            while True:
                command = takeCommand()
                if not processQuery(command):
                    break

# ===================== MAIN =====================
if __name__ == "__main__":
    listenForWakeWord()
