import time
import json
import psutil
import requests
import threading
from pathlib import Path

from config import Config
from brain_manager import BrainManager

# ===================== STATE =====================

MEMORY_FILE = Config.BASE_DIR / "healing_memory.json"

_last_heartbeat = time.time()
_last_heal_time = {}
HEAL_COOLDOWN = 10  # seconds

_memory = []
_stop_event = threading.Event()

# ===================== HEARTBEAT =====================

def heartbeat():
    global _last_heartbeat
    _last_heartbeat = time.time()

# ===================== MEMORY =====================

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_memory():
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(_memory[-50:], f, indent=2)
    except Exception:
        pass

_memory = load_memory()

# ===================== EXPERIENCE BIAS =====================

def past_success_rate(action: str) -> float:
    relevant = [m for m in _memory if m["decision"]["action"] == action]
    if not relevant:
        return 0.5
    return sum(1 for m in relevant if m["success"]) / len(relevant)

# ===================== SNAPSHOT =====================

def snapshot(symptom: str, queue_size: int) -> dict:
    return {
        "symptom": symptom,
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "queue_size": queue_size,
        "heartbeat_age": round(time.time() - _last_heartbeat, 2),
        "recent_actions": _memory[-3:]
    }

# ===================== THINK =====================

def think(snapshot: dict) -> dict:
    """
    AI-assisted decision with safe fallback.
    """
    prompt = f"""
You are a calm senior systems engineer.

SYSTEM SNAPSHOT:
{json.dumps(snapshot, indent=2)}

Choose safest action:
- observe
- clear_queue
- restart_brain

Respond ONLY JSON:
{{"action":"...", "confidence":0-1, "explanation":"short"}}
"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {Config.GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 150
            },
            timeout=8
        )

        data = r.json()
        content = data["choices"][0]["message"]["content"]
        decision = json.loads(content)

        bias = past_success_rate(decision["action"])
        decision["confidence"] = round(decision["confidence"] * bias, 2)
        return decision

    except Exception:
        # 🔥 SAFE FALLBACK (NO AI)
        return {"action": "observe", "confidence": 0.0, "explanation": "fallback"}

# ===================== EXECUTION =====================

def execute(action: str, brain_loop) -> bool:
    try:
        if action == "observe":
            return True

        if action == "clear_queue":
            return True  # handled by brain safely

        if action == "restart_brain":
            if BrainManager.is_running():
                BrainManager.restart(brain_loop)
            return True

    except Exception:
        return False

    return False

# ===================== HEAL =====================

def heal(symptom: str, queue_size: int, brain_loop):
    now = time.time()

    if symptom in _last_heal_time:
        if now - _last_heal_time[symptom] < HEAL_COOLDOWN:
            return

    _last_heal_time[symptom] = now

    snap = snapshot(symptom, queue_size)
    decision = think(snap)
    success = execute(decision["action"], brain_loop)
    print(f"🩺 Heal[{symptom}] → {decision['action']} ({decision['confidence']})")

    _memory.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot": snap,
        "decision": decision,
        "success": success
    })
    save_memory()

# ===================== MONITOR =====================

def monitor(queue_size_fn, brain_loop):
    while not _stop_event.is_set():
        time.sleep(3)

        if time.time() - _last_heartbeat > 6:
            heal("heartbeat_delay", queue_size_fn(), brain_loop)

        if psutil.virtual_memory().percent > 85:
            heal("memory_pressure", queue_size_fn(), brain_loop)

        if queue_size_fn() > 25:
            heal("queue_overflow", queue_size_fn(), brain_loop)

# ===================== CONTROL =====================

def start(queue_size_fn, brain_loop):
    _stop_event.clear()
    threading.Thread(
        target=monitor,
        args=(queue_size_fn, brain_loop),
        daemon=True
    ).start()
    print("🧠 Healing arbiter online")

def stop():
    _stop_event.set()
