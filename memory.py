# memory.py
import json
import os
from datetime import datetime

MEMORY_DIR = "memory"
SHORT = os.path.join(MEMORY_DIR, "short_term.json")
LONG = os.path.join(MEMORY_DIR, "long_term.json")

os.makedirs(MEMORY_DIR, exist_ok=True)


def _safe_load(path):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception:
        # auto-heal corrupted memory
        return []


def _safe_save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------- SHORT TERM ----------
def add_short(user, assistant):
    data = _safe_load(SHORT)
    data.append({
        "user": user,
        "assistant": assistant,
        "time": datetime.now().isoformat()
    })
    data = data[-6:]  # keep last 6
    _safe_save(SHORT, data)


def get_short_context():
    data = _safe_load(SHORT)
    return " | ".join(
        f"User: {d['user']} / FRIDAY: {d['assistant']}"
        for d in data[-3:]
    )


# ---------- LONG TERM ----------
def add_long(text):
    data = _safe_load(LONG)
    data.append({
        "fact": text,
        "time": datetime.now().isoformat()
    })
    _safe_save(LONG, data)


def get_long_facts():
    data = _safe_load(LONG)
    return " | ".join(d["fact"] for d in data[-5:])
