import os
import time
import json
import queue
import logging
import datetime
import requests
import threading
import tempfile
import asyncio
import warnings
import tracemalloc
import vision_module

from dotenv import load_dotenv
from pydub import AudioSegment
import simpleaudio as sa
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import edge_tts
from ddgs import DDGS

speech_lock = threading.Lock()
tracemalloc.start()
# ===================== SUPPRESS WARNINGS =====================
# This silences the ResourceWarning for temp files and DuckDuckGo rename warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ===================== ENV & SESSION =====================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in .env file. Please check your .env file.")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {GROQ_API_KEY}"})

# ===================== GLOBAL STATE =====================
is_speaking = False
assistant_active = False
interrupt_requested = False
vosk_ready = False 

command_queue = queue.Queue()
audio_queue = queue.Queue()
listener_running = True
conversation_turns = []  
persistent_memory = {"profile": {}}
MEMORY_FILE = "jarvis_memory.json"

# ===================== PERSISTENT MEMORY =====================
def load_mem():
    global persistent_memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f: 
                persistent_memory = json.load(f)
        except: 
            persistent_memory = {"profile": {}}

def save_mem():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(persistent_memory, f, indent=2)

load_mem()

def extract_and_store_memory(text):
    text = text.lower()
    p = persistent_memory["profile"]
    updated = False
    
    # Correction dictionary for phonetic misinterpretations of "Rakshit"
    corrections = {"rock shit": "Rakshit", "earache": "Rakshit", "rishi": "Rakshit", "reduction": "Rakshit"}
    
    if "my name is" in text:
        raw_name = text.split("is")[-1].strip()
        p["name"] = corrections.get(raw_name, raw_name.capitalize())
        updated = True
    elif "i live in" in text:
        p["location"] = text.split("in")[-1].strip().capitalize()
        updated = True

    if updated:
        save_mem()
    return updated

# ===================== ASYNC TTS ENGINE =====================
async def speak_async(text):
    global is_speaking, interrupt_requested
    is_speaking = True
    interrupt_requested = False 
    
    clean_text = text.replace("**", "").replace("*", "").strip()
    
    # Using NamedTemporaryFile is safer and ensures we get a string path
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_temp:
        path = mp3_temp.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_temp:
        wav = wav_temp.name
    
    try:
        # 1. Generate Speech
        comm = edge_tts.Communicate(clean_text, "en-GB-RyanNeural")
        await comm.save(path)
        
        # 2. Convert to WAV for simpleaudio
        audio = AudioSegment.from_mp3(path)
        audio.export(wav, format="wav")
        
        # 3. Play Audio
        wave_obj = sa.WaveObject.from_wave_file(wav)
        play_obj = wave_obj.play()
        
        # 4. Interruption Check Loop
        while play_obj.is_playing():
            if interrupt_requested:
                play_obj.stop()
                logging.info("🛑 Audio output killed.")
                break
            await asyncio.sleep(0.05)
            
    except Exception as e:
        logging.error(f"TTS Error: {e}")
    finally:
        is_speaking = False
        # Cleanup files
        for f_path in [path, wav]:
            try:
                if os.path.exists(f_path):
                    os.remove(f_path)
            except Exception as e:
                logging.debug(f"Cleanup error: {e}")

# ===================== SYNC BRIDGE FOR SPEAK =====================
def speak(text):
    """
    Spawns speech in a daemon thread. 
    By removing the .locked() check, we ensure multiple sentences 
    (like a scan intro and the scan result) queue up and play in order.
    """
    def run_speech():
        # Now, this thread will simply wait until the previous sentence is done.
        with speech_lock:  
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(speak_async(text))
                loop.close()
            except Exception as e:
                logging.error(f"Speech Bridge Error: {e}")

    threading.Thread(target=run_speech, daemon=True).start()

# ===================== ALL-KNOWING WEB SEARCH =====================
def web_search(query):
    try:
        logging.info(f"🌐 JARVIS: Accessing global databases for '{query}'...")
        with DDGS() as ddgs:
            # Modern DDGS v4.0+ usage
            results = list(ddgs.text(keywords=query, max_results=3))
            if not results: return "No real-time data found."
            return "\n\n".join([f"{r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Search error: {e}"

# ===================== GPT-OSS 120B CORE =====================
def get_groq_response(prompt):
    global conversation_turns
    clean_prompt = prompt.strip().lower()
    
    # 1. LIVE DATA DETECTION
    search_keywords = ["who is", "president", "news", "price", "today", "latest", "current", "weather"]
    search_context = ""
    if any(k in clean_prompt for k in search_keywords):
        search_context = f"\n\n[LIVE SEARCH RESULTS]:\n{web_search(clean_prompt)}"

    # 2. CONFIG: Using Llama 3.3 70B for stability (or gpt-oss-120b if available)
    MODEL = "llama-3.3-70b-versatile" 
    curr_date = datetime.datetime.now().strftime("%B %d, %Y")

    msgs = [{
        "role": "system", 
        "content": (
            f"You are JARVIS, an advanced AI based on the 120B parameter OSS architecture. "
            f"Current date: {curr_date}. User: {persistent_memory['profile'].get('name', 'Sir')}. "
            "Integrate search results naturally. Be brilliant, concise, and professional."
            f"{search_context}"
        )
    }]
    
    msgs.extend(conversation_turns[-10:]) # Maintain 10 turns of context
    msgs.append({"role": "user", "content": clean_prompt})

    try:
        r = session.post("https://api.groq.com/openai/v1/chat/completions", 
                         json={
                             "model": MODEL, 
                             "messages": msgs, 
                             "temperature": 0.5,
                             "max_tokens": 500
                         }, timeout=15)
        
        ans = r.json()['choices'][0]['message']['content']
        conversation_turns.append({"role": "user", "content": clean_prompt})
        conversation_turns.append({"role": "assistant", "content": ans})
        return ans
    except Exception as e: 
        return f"Sir, my core link is unstable: {e}"

# ===================== VOSK & LISTENER =====================
def load_vosk():
    global vosk_model, vosk_ready
    logging.info("🚀 Loading Brain Modules...")
    VOSK_PATH = os.path.join("models", "vosk-model-en-us-0.22")
    if not os.path.exists(VOSK_PATH):
        raise RuntimeError(f"Vosk model not found at {VOSK_PATH}")
    vosk_model = Model(VOSK_PATH)
    vosk_ready = True
    logging.info("🧠 Brain Modules Loaded.")

def audio_callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

def background_listener():
    global interrupt_requested, assistant_active
    while not vosk_ready: time.sleep(0.1)
    
    rec = KaldiRecognizer(vosk_model, 16000)
    stop_words = ["stop", "shut up", "quiet", "cancel", "hold on"]
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype="int16", channels=1, callback=audio_callback):
        logging.info("🎧 JARVIS is monitoring...")
        while listener_running:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "").strip().lower()
                if text:
                    # GLOBAL INTERRUPTION TRIGGER
                    if any(w in text for w in stop_words):
                        interrupt_requested = True
                        # Clear existing commands so JARVIS doesn't "answer" the stop command
                        while not command_queue.empty():
                            try: command_queue.get_nowait()
                            except: break
                        logging.info("🛑 Interruption Signal Received.")
                        continue
                    
                    if not assistant_active:
                        if "jarvis" in text: command_queue.put(text)
                    else:
                        command_queue.put(text)

# ===================== CORE BRAIN LOOP =====================
def brain_loop():
    global assistant_active, conversation_turns, persistent_memory, interrupt_requested
    last_act = time.time()
    
    print("\n" + "="*30 + "\n      JARVIS IS ONLINE\n" + "="*30 + "\n")

    while True:
        try:
            # We use a short timeout so the loop stays responsive
            query = command_queue.get(timeout=0.2)
            last_act = time.time()
        except queue.Empty:
            # AUTO-SLEEP (2 Minutes of silence)
            if assistant_active and (time.time() - last_act > 120): 
                assistant_active = False
                speak("Going to sleep due to inactivity, Sir.")
            continue

        # 1. WAKE LOGIC
        if not assistant_active:
            if "jarvis" in query:
                assistant_active = True
                speak("Ready, Sir.")
            continue

        # 2. INTERRUPTION HANDLING (The Fix for Overlapping)
        if interrupt_requested:
            # Clear everything currently in the command queue 
            # so JARVIS doesn't try to answer "Stop" or "Shut up"
            while not command_queue.empty():
                try: command_queue.get_nowait()
                except: break
            
            # Reset the flag so he can speak again on the NEXT command
            interrupt_requested = False
            logging.info("🧹 Command queue cleared after interruption.")
            continue

        # 3. CLEAR HISTORY / WIPE MEMORY
        if any(cmd in query for cmd in ["clear history", "wipe memory", "reset session"]):
            conversation_turns = []
            persistent_memory = {"profile": {}}
            if os.path.exists(MEMORY_FILE):
                try: os.remove(MEMORY_FILE)
                except: pass
            speak("Session history and memory have been wiped, Sir.")
            continue

        # 4. SLEEP LOGIC
        if any(w in query for w in ["sleep", "goodbye", "exit"]):
            assistant_active = False
            speak("Powering down systems. Goodbye.")
            continue

        # 5. TIME LOGIC
        if "time" in query:
            speak(f"The time is {datetime.datetime.now().strftime('%I:%M %p')}")
            continue

        # 6. MEMORY EXTRACTION
        if extract_and_store_memory(query):
            speak("I've updated my records.")
            continue

        # 7. VISION LOGIC
        if any(w in query for w in ["what am i looking at", "what's on my screen", "look at this"]):
            speak("Scanning your display now, Sir...")
            # FIXED: Passing the API key as the 3rd argument
            description = vision_module.get_vision_analysis(query, session, GROQ_API_KEY)
            speak(description)
            continue

        # 8. AI REASONING (The Core Response)
        # Check one last time that we haven't been interrupted while waiting for Groq
        if not interrupt_requested:
            answer = get_groq_response(query)
            if not interrupt_requested: # Double-check before speaking
                speak(answer)

def wipe_system_memory():
    """Wipes the session memory and deletes temporary vision images."""
    global session_memory
    session_memory = []
    if os.path.exists("session_memory.json"):
        os.remove("session_memory.json")
    
    # Delete vision screenshots if they exist
    for img in ["temp_screen.png", "temp_resized.png"]:
        if os.path.exists(img):
            os.remove(img)
    return "Memory and temporary files have been wiped, Sir."

if __name__ == "__main__":
    threading.Thread(target=load_vosk, daemon=True).start()
    threading.Thread(target=background_listener, daemon=True).start()
    brain_loop()