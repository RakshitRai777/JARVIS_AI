# memory_manager.py
"""
Long-term memory manager for JARVIS
----------------------------------
• Thread-safe
• Async write queue
• Embedding-backed
• Crash-proof
• 24/7 safe
"""

import json
import os
import time
import threading
import queue
from pathlib import Path
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

# ===================== PATHS =====================

BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE = BASE_DIR / "jarvis_memory.json"

# ===================== GLOBAL STATE =====================

_memory = []
_memory_lock = threading.Lock()
_memory_queue = queue.Queue(maxsize=100)

_embedding_model = None
_embedding_lock = threading.Lock()

MAX_MEMORY = 500          # hard cap
SAVE_INTERVAL = 5         # seconds

# ===================== EMBEDDING =====================

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def embed(text: str):
    try:
        model = get_embedding_model()
        vec = model.encode(text)
        return vec.tolist()
    except Exception:
        return None


# ===================== LOAD / SAVE =====================

def load():
    global _memory
    if not MEMORY_FILE.exists():
        _memory = []
        return

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        normalized = []
        for m in data:
            if not isinstance(m, dict):
                continue
            normalized.append({
                "text": m.get("text", ""),
                "tags": m.get("tags", []),
                "time": m.get("time", "unknown"),
                "embedding": m.get("embedding")
            })

        _memory = normalized[-MAX_MEMORY:]

    except Exception:
        _memory = []


def save():
    try:
        with _memory_lock:
            data = _memory[-MAX_MEMORY:]

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception:
        pass


# ===================== PUBLIC API =====================

def add_memory(text: str, tags=None):
    """
    Non-blocking memory add.
    Safe to call from brain loop.
    """
    if not text or not isinstance(text, str):
        return

    try:
        _memory_queue.put_nowait({
            "text": text.strip(),
            "tags": tags or [],
            "time": datetime.utcnow().isoformat()
        })
    except queue.Full:
        pass


def search(query: str, limit=5):
    """
    Fast keyword search (no embeddings).
    """
    q = query.lower()
    results = []

    with _memory_lock:
        for m in reversed(_memory):
            if q in m["text"].lower():
                results.append(m)
            if len(results) >= limit:
                break

    return results


def vector_search(query: str, limit=5):
    """
    Semantic search using cosine similarity.
    """
    with _memory_lock:
        memories = [m for m in _memory if m.get("embedding")]

    if not memories:
        return []

    try:
        q_vec = np.array(embed(query))
        if q_vec is None:
            return []

        scored = []
        for m in memories:
            v = np.array(m["embedding"])
            score = float(
                np.dot(q_vec, v) /
                (np.linalg.norm(q_vec) * np.linalg.norm(v) + 1e-8)
            )
            scored.append((m, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:limit]]

    except Exception:
        return []


def size():
    with _memory_lock:
        return len(_memory)


def clear():
    with _memory_lock:
        _memory.clear()
    save()


# ===================== BACKGROUND WORKER =====================

def _memory_worker():
    last_save = time.time()

    while True:
        try:
            item = _memory_queue.get(timeout=1)
        except queue.Empty:
            item = None

        if item:
            entry = {
                "text": item["text"],
                "tags": item["tags"],
                "time": item["time"],
                "embedding": embed(item["text"])
            }

            with _memory_lock:
                _memory.append(entry)
                if len(_memory) > MAX_MEMORY:
                    _memory[:] = _memory[-MAX_MEMORY:]

        if time.time() - last_save >= SAVE_INTERVAL:
            save()
            last_save = time.time()


# ===================== INIT =====================

load()
threading.Thread(target=_memory_worker, daemon=True).start()
