import json
import os
import time
from typing import List

MEMORY_FILE = "jarvis_memory.json"
MAX_MEMORIES = 500

def _load():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def _save(memories):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories[-MAX_MEMORIES:], f, indent=2)

_memories = _load()

def add_memory(text: str, tags: List[str] = None):
    if not text or len(text.strip()) < 10:
        return
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "text": text.strip(),
        "tags": tags or []
    }
    _memories.append(entry)
    _save(_memories)

def search(query: str, limit: int = 5):
    if not query:
        return []
    q = query.lower()
    scored = []
    for m in _memories:
        score = 0
        if q in m["text"].lower():
            score += 2
        for t in m.get("tags", []):
            if t.lower() in q:
                score += 1
        if score > 0:
            scored.append((score, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]

def size():
    return len(_memories)

def clear():
    _memories.clear()
    _save(_memories)
