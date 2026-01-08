# wake_daemon.py
"""
JARVIS Wake Daemon
------------------
• Always-on microphone listener
• Offline wake-word detection (Vosk)
• Supervisor-safe core launcher
• Pipe-free (NO deadlocks)
• Memory-safe
• CPU-safe
• 24/7 stable on Windows
"""

import sounddevice as sd
import queue
import json
import subprocess
import sys
import time
import signal
from pathlib import Path
from vosk import Model, KaldiRecognizer

# ===================== CONFIG =====================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "vosk-model-en-us-0.22"
CORE_FILE = BASE_DIR / "jarvis_supervisor.py"

LOG_FILE = BASE_DIR / "wake_daemon.log"

# Audio settings
SAMPLE_RATE = 16000
INPUT_DEVICE = 1  # Using Microphone Array (Intel® Smart Sound Technology)
CHANNELS = 1       # Mono audio
BLOCKSIZE = 8000   # Audio block size

# Wake word settings
WAKE_WORD = "jarvis"
WAKE_COOLDOWN = 2.0
MIN_TEXT_LEN = 3

# System settings
AUDIO_QUEUE_SIZE = 50   # prevents RAM leaks
MAX_LOG_SIZE = 5_000_000  # 5 MB

# ===================== SAFETY CHECKS =====================

if not MODEL_PATH.exists():
    raise RuntimeError(f"❌ Vosk model not found at: {MODEL_PATH}")

# ===================== STATE =====================

audio_q = queue.Queue(maxsize=AUDIO_QUEUE_SIZE)

model = Model(str(MODEL_PATH))
rec = KaldiRecognizer(model, SAMPLE_RATE)

core_proc = None
last_wake_time = 0.0
shutdown = False

# ===================== LOGGING =====================

def log(msg: str):
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            LOG_FILE.unlink()
    except Exception:
        pass

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

# ===================== AUDIO CALLBACK =====================

def audio_cb(indata, frames, time_info, status):
    try:
        audio_q.put_nowait(bytes(indata))
    except queue.Full:
        pass  # drop audio safely
    if status:
        log(f"Audio status: {status}")

# ===================== CORE CONTROL =====================

def core_alive() -> bool:
    return core_proc is not None and core_proc.poll() is None


def start_core():
    global core_proc

    if core_alive():
        return

    log("🚀 Starting JARVIS supervisor")

    try:
        core_proc = subprocess.Popen(
            [sys.executable, str(CORE_FILE)],
            stdin=subprocess.DEVNULL,   # 🔒 NO PIPE DEADLOCKS
            stdout=open(BASE_DIR / "core_stdout.log", "a", encoding="utf-8"),
            stderr=open(BASE_DIR / "core_stderr.log", "a", encoding="utf-8"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32" else 0
        )
    except Exception as e:
        log(f"❌ Failed to start core: {e}")
        core_proc = None

# ===================== SIGNAL HANDLING =====================

def handle_signal(sig, frame):
    global shutdown
    shutdown = True
    log("🛑 Wake daemon shutting down")

    if core_alive():
        try:
            core_proc.terminate()
        except Exception:
            pass

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# ===================== MAIN LOOP =====================

print("🎧 Wake daemon online (listening for 'Jarvis')")
log(f"🎤 Starting wake word detection on device {INPUT_DEVICE}...")

try:
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        device=INPUT_DEVICE,
        channels=CHANNELS,
        dtype='int16',
        callback=audio_cb
    ) as stream:
        log(f"✅ Audio stream started on device {INPUT_DEVICE}")
        
        while not shutdown:
            time.sleep(0.1)

            # Process audio in chunks
            try:
                data = audio_q.get_nowait()
            except queue.Empty:
                continue
                
            if not rec.AcceptWaveform(data):
                continue

            try:
                result = json.loads(rec.Result())
                rec.Reset()
                text = result.get("text", "").lower().strip()

                if not text or len(text) < MIN_TEXT_LEN:
                    continue

                words = text.split()
                now = time.time()

                # 🔥 WAKE WORD DETECTION
                if WAKE_WORD in words:
                    if now - last_wake_time < WAKE_COOLDOWN:
                        continue

                    last_wake_time = now
                    log("👂 Wake word detected")
                    start_core()

            except Exception as e:
                log(f"Error processing audio: {e}")
                continue

except Exception as e:
    log(f"❌ Error in audio stream: {e}")
finally:
    log("🛑 Wake daemon exited")