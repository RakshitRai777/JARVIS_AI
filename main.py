import os
import time
import json
import queue
import threading
import asyncio
import datetime
import requests
import signal
import sys

from config import Config
from pydub import AudioSegment
import simpleaudio as sa
import edge_tts

import vision_module
from brain_manager import BrainManager
import healing_arbiter
import memory_manager
from hybrid_memory import hybrid_memory_search
import tool_manager
import certifi

from concurrent.futures import ThreadPoolExecutor
tts_executor = ThreadPoolExecutor(max_workers=1)

os.environ["SSL_CERT_FILE"] = certifi.where()
Config.validate()
# ===================== GLOBAL STATE =====================
print("GROQ KEY LOADED:", bool(Config.GROQ_API_KEY))
STATE_FILE = "jarvis_state.json"
pending_tool_confirmation = {
    "active": False,
    "tool_name": None,
    "tool_payload": None,
    "timestamp": 0
}

# ===================== TOOL CONFIRMATION =====================
tool_confirm_lock = threading.Lock()
TOOL_CONFIRM_TIMEOUT = 10  # seconds

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000002  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    )

# ===================== UI MODE =====================
ENABLE_UI = os.environ.get("JARVIS_UI") == "1"

shutdown_event = threading.Event()

conversation_history = []
conversation_summary = ""

MAX_CONTEXT_TURNS = 4
SUMMARY_TRIGGER_TURNS = 8

command_queue = queue.Queue(maxsize=30)   # (source, text)

stream_queue = queue.Queue(maxsize=200)

speech_finished = threading.Event()
speech_finished.set() # Start in a ready state
conversation_trace = []
brain_lock = threading.Lock()
if len(conversation_trace) > 5000:
    conversation_trace[:] = conversation_trace[-3000:]

last_heartbeat = time.time()

VISION_COOLDOWN = 15
_last_vision_time = 0
vision_lock = threading.Lock()
# ===================== INPUT SANITY =====================

IGNORED_INPUTS = {
    "", " ", "ok", "okay", "hmm", "hm", "yes", "no",
    "the", ".", "..", "...", "uh", "huh"
}

CONTROL_WORDS = {
    "stop", "pause", "cancel",
    "exit", "shutdown", "restart"
}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            conversation_summary = data.get("summary", "")
            conversation_trace = data.get("trace", [])
    except Exception:
        conversation_trace = []

def log_turn(role: str, content: str):
    conversation_trace.append({
        "role": role,
        "content": content,
        "time": time.time()
    })
    if len(conversation_trace) > 5000:
        conversation_trace[:] = conversation_trace[-3000:]


def is_meaningful_input(text: str) -> bool:
    """
    Filters junk input while allowing control commands.
    """
    if not isinstance(text, str):
        return False

    text = text.lower().strip()

    if not text:
        return False

    # Always allow control commands
    if text in CONTROL_WORDS:
        return True

    if text in IGNORED_INPUTS:
        return False

    # Allow short questions like "why?"
    if text.endswith("?"):
        return True

    # Reject very short non-questions
    if len(text.split()) < 2:
        return False

    return True


def extract_entity_anchor(reply: str) -> str | None:
    """
    Very lightweight entity anchoring.
    Extracts the main named entity from factual replies.
    """
    keywords = [" is ", " was ", " are "]
    for k in keywords:
        if k in reply:
            return reply.split(k)[0].strip()
    return None

# ===================== TTS LOOP =====================

tts_loop = asyncio.new_event_loop()

def start_tts_loop():
    asyncio.set_event_loop(tts_loop)
    tts_loop.run_forever()

threading.Thread(target=start_tts_loop, daemon=True).start()

speech_lock = threading.Lock()
audio_playback = None

import uuid
async def _speak_async(text: str):
    global audio_playback
    mp3 = wav = None

    try:
        uid = uuid.uuid4().hex
        mp3 = f"response_tmp_{uid}.mp3"
        wav = f"response_tmp_{uid}.wav"

        await edge_tts.Communicate(
            text=text,
            voice="en-GB-RyanNeural"
        ).save(mp3)

        sound = AudioSegment.from_mp3(mp3)
        sound.export(wav, format="wav")

        wave = sa.WaveObject.from_wave_file(wav)

        with speech_lock:
            audio_playback = wave.play()

        audio_playback.wait_done()

    except Exception as e:
        print("TTS error:", repr(e))

    finally:
        speech_finished.set()
        for f in (mp3, wav):
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

def speak(text: str):
    if shutdown_event.is_set():
        return

    def run():
        global audio_playback
        speech_finished.clear()

        with speech_lock:
            if audio_playback and audio_playback.is_playing():
                audio_playback.stop()
                audio_playback = None

        asyncio.run_coroutine_threadsafe(_speak_async(text), tts_loop)

    tts_executor.submit(run)

# ===================== GROQ =====================

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {Config.GROQ_API_KEY}"
})

session.verify = True
FAST_MODEL = "llama-3.1-8b-instant"
MID_MODEL = "llama-3.1-70b-instant"   # if available, else reuse 8b
DEEP_MODEL = "llama-3.3-70b-versatile"

# Safe fallback if MID model is unavailable
if not MID_MODEL:
    MID_MODEL = FAST_MODEL

# Optional in-memory cache (safe, simple, effective)
_GROQ_CACHE = {}
_GROQ_CACHE_MAX = 256


def groq(
    messages,
    task="chat",
    level=None,          # "fast" | "mid" | "deep" | None (auto)
    use_cache=True
):
    """
    Optimized Groq API caller with:
    - Dynamic model selection
    - Smart rate-limit backoff
    - Optional response caching
    - Backward compatibility
    """

    # -------------------------------
    # 🔹 MODEL SELECTION
    # -------------------------------
    if level is None:
        # Backward compatibility
        if task in ("reasoning", "summary"):
            level = "deep"
        else:
            level = "fast"

    if level == "deep":
        model = DEEP_MODEL
        max_tokens = 500
        timeout = 35
    elif level == "mid":
        model = MID_MODEL
        max_tokens = 350
        timeout = 20
    else:  # fast
        model = FAST_MODEL 
        max_tokens = 200
        timeout = 10

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }

    # -------------------------------
    # 🔹 CACHE KEY (SAFE & STABLE)
    # -------------------------------
    cache_key = None
    if use_cache:
        try:
            cache_key = json.dumps(
                {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                sort_keys=True
            )
            if cache_key in _GROQ_CACHE:
                return _GROQ_CACHE[cache_key]
        except Exception:
            cache_key = None  # fallback safely

    # -------------------------------
    # 🔹 REQUEST WITH SMART RETRIES
    # -------------------------------
    for attempt in range(3):
        try:
            response = session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                timeout=timeout
            )

            # ---------------------------
            # RATE LIMIT HANDLING
            # ---------------------------
            if response.status_code == 429:
                retry_after = int(
                    response.headers.get("Retry-After", 2)
                )
                wait_time = retry_after + attempt
                print(f"⚠️ Groq rate limited. Backing off {wait_time}s...")
                time.sleep(wait_time)
                continue

            if response.status_code != 200:
                print(
                    f"❌ Groq API error (attempt {attempt + 1}):",
                    response.status_code,
                    response.text
                )
                time.sleep(1 + attempt)
                continue

            data = response.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content")
            )

            if not content or not isinstance(content, str):
                raise ValueError("Empty or invalid Groq response")

            content = content.strip()

            # ---------------------------
            # CACHE STORE
            # ---------------------------
            if cache_key:
                if len(_GROQ_CACHE) >= _GROQ_CACHE_MAX:
                    _GROQ_CACHE.pop(next(iter(_GROQ_CACHE)))
                _GROQ_CACHE[cache_key] = content

            return content

        except requests.exceptions.Timeout:
            print(f"⏳ Groq timeout (attempt {attempt + 1})")
            time.sleep(1 + attempt)

        except Exception as e:
            print(f"❌ Groq exception (attempt {attempt + 1}):", repr(e))
            time.sleep(1 + attempt)

    return "I'm having trouble thinking right now."

def groq_stream(
    messages,
    level="fast"
):
    if level == "deep":
        model = DEEP_MODEL
        max_tokens = 500
        timeout = 35
    elif level == "mid":
        model = MID_MODEL
        max_tokens = 350
        timeout = 20
    else:
        model = FAST_MODEL
        max_tokens = 200
        timeout = 10

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }

    with session.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        stream=True,
        timeout=timeout
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            if line.startswith(b"data: "):
                data = line[len(b"data: "):]

                if data == b"[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )

                    if delta:
                        yield delta

                except Exception:
                    continue

ui_stream_queue = queue.Queue()
def stream_and_speak(messages, level):
    """
    Streams Groq response:
    - Sends tokens to UI immediately
    - Speaks sentence-by-sentence
    - Returns full final text (for memory, tools, logs)
    """
    full_text = ""
    speech_buffer = ""

    for token in groq_stream(messages, level=level):

        # Hard interrupt support
        if shutdown_event.is_set():
            break

        full_text += token

        # UI streaming
        if ENABLE_UI:
            stream_queue.put(token)

        # Voice buffering
        speech_buffer += token

        # Speak only meaningful sentences
        if (
            any(p in speech_buffer for p in ".?!")
            and len(speech_buffer.strip()) > 20
        ):
            speak(speech_buffer.strip())
            speech_buffer = ""

    # Speak leftover text
    if speech_buffer.strip():
        speak(speech_buffer.strip())

    # Signal UI end
    if ENABLE_UI:
        stream_queue.put("__END__")

    return full_text.strip()

# ===================== CONVERSATION SUMMARY =====================

def summarize_conversation(history):
    try:
        messages = [{
            "role": "system",
            "content": (
                "Summarize the following conversation briefly. "
                "Preserve facts, names, roles, and unresolved questions. "
                "Write in third person."
            )
        }]
        messages.extend(history)
        
        time.sleep(0.3)
        summary = groq(messages, task="summary")
        return summary.strip() if isinstance(summary, str) else ""

    except Exception:
        return ""

# ===================== MEMORY HELPERS =====================

def fact_already_known(text: str) -> bool:
    text = text.lower().strip()
    for m in memory_manager.search(text, limit=10):
        if m["text"].lower().strip() == text:
            return True
    return False

def should_store_fact(query: str, reply: str) -> bool:
    intent_words = ["who", "where", "what", "when"]
    return (
        any(w in query.lower() for w in intent_words)
        and len(reply.split()) > 6
    )

def stream_reply(text):
    """
    Splits the final text into tokens to simulate a stream 
    if the actual API stream wasn't used.
    """
    for token in text.split(" "):
        stream_queue.put(token + " ")
        time.sleep(0.02)  # Simulates typing speed
    stream_queue.put("__END__")

def thinking_level(query: str) -> str:
    q = query.lower()

    deep_keywords = {
        "architecture", "design", "optimize", "debug deeply",
        "step by step", "root cause", "full analysis"
    }

    mid_keywords = {
        "explain", "why", "how", "compare", "difference"
    }

    if any(k in q for k in deep_keywords) or len(q.split()) > 20:
        return "deep"

    if any(k in q for k in mid_keywords):
        return "mid"

    return "fast"

# ===================== HEARTBEAT =====================

def heartbeat_loop():
    global last_heartbeat
    while not shutdown_event.is_set():
        last_heartbeat = time.time()
        healing_arbiter.heartbeat()
        time.sleep(1)

threading.Thread(target=heartbeat_loop, daemon=True).start()

# ===================== BRAIN =====================

def brain_loop():
    global conversation_summary
    global last_heartbeat

    print("\n=== JARVIS ONLINE ===\n")

    while not shutdown_event.is_set() and not BrainManager.should_stop():
        try:    
            # Allow thinking while speaking
            pass

            try:
                source, query = command_queue.get(timeout=0.2)
                query = query.strip()
                if not is_meaningful_input(query):
                    continue
            except queue.Empty:
                continue

            # ===================== STOP / INTERRUPT =====================
            if query.strip() in {"stop", "jarvis stop"}:
                with speech_lock:
                    if audio_playback and audio_playback.is_playing():
                        audio_playback.stop()
                speech_finished.set()
                continue

            # ===================== TOOL CONFIRMATION HANDLER =====================
            with tool_confirm_lock:
                if pending_tool_confirmation["active"]:
                    elapsed = time.time() - pending_tool_confirmation["timestamp"]

                    if elapsed > TOOL_CONFIRM_TIMEOUT:
                        pending_tool_confirmation["active"] = False
                        reply = "Confirmation timed out. Action cancelled."
                        if ENABLE_UI:
                            stream_reply(reply)
                        speak(reply)
                        continue

                    if query in {"yes", "yeah", "yep", "confirm"}:
                        tool_name = pending_tool_confirmation["tool_name"]
                        tool_payload = pending_tool_confirmation["tool_payload"]
                        pending_tool_confirmation["active"] = False

                        result = tool_manager.ToolsManager.execute(tool_name, **tool_payload)
                        reply = f"Done. {result}"

                        if ENABLE_UI:
                            stream_reply(reply)
                        speak(reply)
                        continue

                    if query in {"no", "cancel", "stop"}:
                        pending_tool_confirmation["active"] = False
                        reply = "Alright, cancelled."
                        if ENABLE_UI:
                            stream_reply(reply)
                        speak(reply)
                        continue

            # ===================== FAST COMMANDS =====================
            if "time" in query:
                reply = datetime.datetime.now().strftime("The time is %I:%M %p")
                
                if ENABLE_UI:
                    stream_reply(reply)
                speak(reply)
                continue

            if "how many memories" in query:
                reply = f"I remember {memory_manager.size()} things."
                
                if ENABLE_UI:
                    stream_reply(reply)
                speak(reply)
                continue

            if "clear your memory" in query:
                memory_manager.clear()
                reply = "My memory has been cleared."
                
                if ENABLE_UI:
                    stream_reply(reply)
                speak(reply)
                continue

            if "screen" in query:
                def vision_task(q):
                    global _last_vision_time, last_heartbeat
                    with vision_lock:
                        now = time.time()
                        if now - _last_vision_time < VISION_COOLDOWN:
                            speak("Please wait before another screen analysis, sir.")
                            return
                        _last_vision_time = now
                    
                    last_heartbeat = time.time()
                    reply = vision_module.get_vision_analysis(q, session, Config.GROQ_API_KEY)
                    if reply:
                        if ENABLE_UI:
                            stream_reply(reply)
                        speak(reply)

                threading.Thread(target=vision_task,args=(query,),daemon=True).start()
                continue
            
            if "wake up" in query or "wake jarvis" in query:
                    reply = "Waking up, sir."
                    if ENABLE_UI:
                        stream_reply(reply)
                    speak(reply)
                    continue
            if "shut down" in query or "shutdown jarvis" in query:
                reply = "Shutting down all systems. Goodbye, sir."
                if ENABLE_UI:
                    stream_reply(reply)
                speak(reply)
                shutdown_event.set()
                time.sleep(0.5)
                os._exit(0) 
            if "restart yourself" in query:
                reply = "Restarting systems now, sir."
                if ENABLE_UI:
                    stream_reply(reply)
                speak(reply)
                shutdown_event.set()
                time.sleep(0.3)
                os._exit(42) #Special Restart Exit Code

            # ===================== CONVERSATION STATE (LOCKED) =====================
            with brain_lock:
                if (
                    conversation_history
                    and conversation_history[-1]["role"] == "user"
                    and conversation_history[-1]["content"] == query
                ):
                    continue

                conversation_history.append({"role": "user", "content": query})
                log_turn("user", query)

                # ===================== CONVERSATION SUMMARY =====================
                user_turns = [m for m in conversation_history if m["role"] == "user"]
                if len(user_turns) >= SUMMARY_TRIGGER_TURNS:
                    summary = summarize_conversation(conversation_history)
                    if summary:
                        conversation_summary = summary
                    
                    last_user = conversation_history[-1]
                    last_assistant = next(
                        (m for m in reversed(conversation_history) if m["role"] == "assistant"),
                        None
                    )

                    conversation_history.clear()
                    if last_assistant:
                        conversation_history.append(last_assistant)
                    conversation_history.append(last_user)

                conversation_history[:] = conversation_history[-MAX_CONTEXT_TURNS:]

                # ===================== MESSAGE BUILD =====================
                messages = []

                if conversation_summary:
                    messages.append({
                        "role": "system",
                        "content": f"Conversation summary so far:\n{conversation_summary}"
                    })

                last_assistant = next(
                    (m for m in reversed(conversation_history) if m["role"] == "assistant"),
                    None
                )
                if last_assistant:
                    entity = extract_entity_anchor(last_assistant["content"])
                    if entity:
                        messages.append({
                            "role": "system",
                            "content": f"The user is referring to: {entity}."
                        })

                messages.append({
                    "role": "system",
                    "content": (
                        "Style rules:\n"
                        "- Do NOT repeat full names once introduced.\n"
                        "- Use pronouns for follow-ups.\n"
                        "- Maintain conversational continuity."
                    )
                })

                memories = hybrid_memory_search(query, limit=5)
                if memories:
                    messages.append({
                        "role": "system",
                        "content": "Relevant long-term memories:\n" +
                                   "\n".join(f"- {m['text']}" for m in memories)
                    })

                messages.append({"role": "user", "content": query})

            # ===================== THINK (NO LOCK) =====================
            last_heartbeat = time.time()
            level = thinking_level(query)
            reply = stream_and_speak(messages, level)

            tool_name, tool_payload = None, None

            if isinstance(reply, str) and reply.strip().startswith("{"):
                try:
                    tool_name, tool_payload = tool_manager.parse_tool_call(reply)
                except Exception:
                    tool_name, tool_payload = None, None

            if tool_name:
                # 🔒 Require confirmation for dangerous tools
                if tool_manager.requires_confirmation(tool_name):
                    with tool_confirm_lock:

                        pending_tool_confirmation.update({
                            "active": True,
                            "tool_name": tool_name,
                            "tool_payload": tool_payload,
                            "timestamp": time.time()
                        })

                    confirm_msg = f"Do you want me to {tool_name.replace('_', ' ')}? Yes or no."
                    if ENABLE_UI:
                        stream_reply(confirm_msg)
                    speak(confirm_msg)
                    continue

                # ✅ Safe tools execute immediately
                tool_results = tool_manager.ToolsManager.execute(tool_name, **tool_payload)
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "tool", "content": str(tool_results)})
                reply = stream_and_speak(messages, level)

            if not reply:
                continue

            # ===================== POST-THINK STATE =====================
            with brain_lock:
                conversation_history.append({"role": "assistant", "content": reply})
                log_turn("assistant", reply)

            normalized = reply.lower().strip()
            if should_store_fact(query, reply) and not fact_already_known(normalized):
                memory_manager.add_memory(text=reply, tags=["fact"])

            
            pass
            
            if not speech_finished.wait(timeout=15):
                print("⚠️ TTS timeout — force reset")
                speech_finished.set()

        except Exception as e:
            print("Brain error:", repr(e))
            time.sleep(1)


# ===================== TEST HOOK =====================

def process_text_for_test(text: str):
    """
    Deterministic, synchronous processing path for tests.
    Does NOT touch audio, threads, or queues.
    """
    global conversation_summary
    with brain_lock:
        log_turn("user", text)

    messages = []

    # 1️⃣ Conversation summary
    if conversation_summary:
        messages.append({
            "role": "system",
            "content": f"Conversation summary so far:\n{conversation_summary}"
        })

    # 2️⃣ Hybrid memory
    memories = hybrid_memory_search(text, limit=5)
    if memories:
        messages.append({
            "role": "system",
            "content": "Relevant long-term memories:\n" +
                       "\n".join(f"- {m['text']}" for m in memories)
        })

    # 4️⃣ Current user query
    messages.append({
        "role": "user",
        "content": text
    })

    time.sleep(0.3)
    reply = groq(messages, use_cache=True)
    if not isinstance(reply, str):
        reply = "I'm having trouble responding right now."
    return reply

def get_conversation_text():
    """
    Returns full conversation text for tests.
    """
    return "\n".join(
        turn["content"] for turn in conversation_trace
    )

WATCHDOG_TIMEOUT = 90

def watchdog_loop():
    while not shutdown_event.is_set():
        time.sleep(5)

        if time.time() - last_heartbeat > WATCHDOG_TIMEOUT:
            print("🚨 Watchdog detected freeze. Restarting JARVIS core.")
            shutdown_event.set()
            os._exit(42)


def shutdown_handler(sig=None, frame=None):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump({
            "summary": conversation_summary,
            "trace": conversation_trace[-200:]
        }, f)
    os.replace(tmp, STATE_FILE)

    shutdown_event.set()
    time.sleep(0.5)
    os._exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ===================== START =====================

if __name__ == "__main__":
    try:
        # Start watchdog in a daemon thread
        threading.Thread(target=watchdog_loop, daemon=True).start()
        
        # Start healing arbiter
        healing_arbiter.start(
            queue_size_fn=lambda: command_queue.qsize(),
            brain_loop=brain_loop
        )
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        shutdown_handler()