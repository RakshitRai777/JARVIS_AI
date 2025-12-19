import json
import os
from logger import debug, info

MEMORY_DIR = "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

SHORT_FILE = f"{MEMORY_DIR}/short.json"
LONG_FILE = f"{MEMORY_DIR}/long.json"

def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def add_short(user, assistant):
    data = _load(SHORT_FILE)
    data.append({"user": user, "assistant": assistant})
    _save(SHORT_FILE, data[-6:])
    info("Short-term memory updated")

def get_short_context():
    return "\n".join(
        f"User: {d['user']} | FRIDAY: {d['assistant']}"
        for d in _load(SHORT_FILE)
    )

def add_long(text):
    data = _load(LONG_FILE)
    data.append(text)
    _save(LONG_FILE, data)
    info("Long-term memory updated")

def get_long_facts():
    return "\n".join(_load(LONG_FILE))
