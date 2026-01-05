import time
import json
import psutil
import requests
import threading
from config import Config
from brain_manager import BrainManager
import main

MEMORY_FILE = "healing_memory.json"

last_heartbeat = time.time()
last_heal_time = {}
HEAL_COOLDOWN = 10  # seconds

memory = []

# ===================== HEARTBEAT =====================
def heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()

# ===================== MEMORY =====================
def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-50:], f, indent=2)

memory = load_memory()

# ===================== EXPERIENCE BIAS =====================
def past_success_rate(action):
    relevant = [m for m in memory if m["decision"]["action"] == action]
    if not relevant:
        return 0.5
    return sum(1 for m in relevant if m["success"]) / len(relevant)

# ===================== SNAPSHOT =====================
def snapshot(symptom):
    return {
        "symptom": symptom,
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "queue": main.command_queue.qsize(),
        "heartbeat_age": round(time.time() - last_heartbeat, 2),
        "history": memory[-3:]
    }

# ===================== AI THINKING =====================
def think(snap):
    prompt = f"""
You are a calm, experienced human engineer.

SYSTEM STATE:
{json.dumps(snap, indent=2)}

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
            timeout=10
        )

        data = r.json()
        if "choices" not in data:
            return {"action": "observe", "confidence": 0.0, "explanation": "LLM unavailable"}

        decision = json.loads(data["choices"][0]["message"]["content"])

        # Cognitive bias
        decision["confidence"] *= past_success_rate(decision["action"])
        decision["confidence"] = round(decision["confidence"], 2)

        return decision

    except Exception as e:
        return {"action": "observe", "confidence": 0.0, "explanation": str(e)}

# ===================== EXECUTION =====================
def execute(action):
    try:
        if action == "observe":
            return True

        if action == "clear_queue":
            while not main.command_queue.empty():
                main.command_queue.get_nowait()
            return True

        if action == "restart_brain":
            if past_success_rate("clear_queue") > 0.4:
                BrainManager.restart(main.brain_loop)
                main.speak("Recovered from a core issue, sir.")
                return True
            return False

    except:
        return False

    return False

# ===================== CORE HEAL =====================
def heal(symptom):
    now = time.time()
    if symptom in last_heal_time and now - last_heal_time[symptom] < HEAL_COOLDOWN:
        return

    last_heal_time[symptom] = now

    snap = snapshot(symptom)
    decision = think(snap)
    success = execute(decision["action"])

    memory.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot": snap,
        "decision": decision,
        "success": success
    })
    save_memory()

    if decision["confidence"] < 0.6 and decision["explanation"]:
        main.speak(decision["explanation"])

# ===================== MONITOR =====================
def monitor():
    while True:
        time.sleep(3)

        if time.time() - last_heartbeat > 6:
            heal("heartbeat_delay")

        if psutil.virtual_memory().percent > 85:
            heal("memory_pressure")

        if main.command_queue.qsize() > 25:
            heal("queue_overflow")

# ===================== START =====================
def start():
    threading.Thread(target=monitor, daemon=True).start()
    print("🧠 Healing arbiter online.")
