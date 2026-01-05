import os, time, json, queue, threading, asyncio, datetime
import requests
from config import Config
from pydub import AudioSegment
import simpleaudio as sa
import edge_tts
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import vision_module
from brain_manager import BrainManager
import healing_arbiter
import memory_manager

# ===================== GLOBAL STATE =====================
assistant_active = False

command_queue = queue.Queue()
audio_queue = queue.Queue(maxsize=5)   # prevent memory blowup
stream_queue = queue.Queue()

# ===================== VOSK SYNC =====================
vosk_ready = threading.Event()
vosk_model = None

# ===================== TTS EVENT LOOP =====================
tts_loop = asyncio.new_event_loop()

def start_tts_loop():
    asyncio.set_event_loop(tts_loop)
    tts_loop.run_forever()

threading.Thread(target=start_tts_loop, daemon=True).start()

# ===================== SPEECH (SERIALIZED, SAFE) =====================
speech_lock = threading.Lock()

async def _speak_async(text):
    if not text.strip():
        return

    await edge_tts.Communicate(
        text, "en-GB-RyanNeural"
    ).save("response.mp3")

    AudioSegment.from_mp3("response.mp3").export(
        "response.wav", format="wav"
    )

    sa.WaveObject.from_wave_file("response.wav").play().wait_done()

def speak(text):
    def task():
        with speech_lock:
            asyncio.run_coroutine_threadsafe(
                _speak_async(text), tts_loop
            ).result()
    threading.Thread(target=task, daemon=True).start()

# ===================== GROQ =====================
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {Config.GROQ_API_KEY}"})

def groq(prompt):
    try:
        r = session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400
            },
            timeout=15
        )
        data = r.json()
        if "choices" not in data:
            return "I am temporarily unable to think clearly, sir."
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "I encountered a temporary issue while thinking, sir."

# ===================== VOICE =====================
def load_vosk():
    global vosk_model
    model_path = "models/vosk-model-en-us-0.22"

    print("🔊 Loading Vosk model...")
    if not os.path.isdir(model_path):
        raise RuntimeError(f"Vosk model not found at {model_path}")

    vosk_model = Model(model_path)
    print("✅ Vosk model loaded")
    vosk_ready.set()

def audio_callback(indata, frames, time_info, status):
    try:
        audio_queue.put_nowait(bytes(indata))
    except queue.Full:
        pass

def listener():
    print("🎧 Waiting for Vosk model...")
    vosk_ready.wait()
    print("🎧 Microphone listener started")

    rec = KaldiRecognizer(vosk_model, 16000)

    with sd.RawInputStream(
        samplerate=16000,
        channels=1,
        dtype="int16",
        callback=audio_callback
    ):
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "")
                if text:
                    command_queue.put(text.lower())

# ===================== MEMORY =====================
def memory_context(query: str) -> str:
    hits = memory_manager.search(query, limit=5)
    if not hits:
        return ""
    lines = ["Relevant past memories:"]
    for m in hits:
        lines.append(f"- ({m['time']}) {m['text']}")
    return "\n".join(lines)

# ===================== BRAIN LOOP =====================
def brain_loop():
    global assistant_active
    print("\n=== JARVIS ONLINE ===\n")

    while True:
        healing_arbiter.heartbeat()

        try:
            query = command_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        # ---- Wake word ----
        if not assistant_active:
            if "jarvis" in query:
                assistant_active = True
                reply = "Ready, sir."
                speak(reply)
                for w in reply.split():
                    stream_queue.put(w + " ")
                    time.sleep(0.05)
                stream_queue.put("__END__")
            continue

        # ---- Commands ----
        if "time" in query:
            reply = datetime.datetime.now().strftime(
                "The time is %I:%M %p"
            )

        elif "how many memories" in query:
            reply = f"I currently remember {memory_manager.size()} things, sir."

        elif "clear your memory" in query:
            memory_manager.clear()
            reply = "My long-term memory has been cleared."

        elif "screen" in query:
            reply = vision_module.get_vision_analysis(
                query, session, Config.GROQ_API_KEY
            )

        else:
            mem_ctx = memory_context(query)
            prompt = f"{mem_ctx}\n\nUser: {query}" if mem_ctx else query
            reply = groq(prompt)

            if any(k in query for k in [
                "remember", "my name is", "i am", "i like",
                "i prefer", "i work", "i study"
            ]):
                memory_manager.add_memory(
                    f"User said: {query}",
                    tags=["user_fact"]
                )

        # ---- Speak + Stream ----
        speak(reply)
        for w in reply.split():
            stream_queue.put(w + " ")
            time.sleep(0.05)
        stream_queue.put("__END__")

# ===================== START =====================
if __name__ == "__main__":
    threading.Thread(target=load_vosk, daemon=True).start()
    threading.Thread(target=listener, daemon=True).start()
    healing_arbiter.start()
    BrainManager.start(brain_loop)
