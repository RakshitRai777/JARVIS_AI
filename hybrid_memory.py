# hybrid_memory.py
"""
Hybrid Memory System for JARVIS
--------------------------------
• Keyword search (fast recall)
• Semantic vector reranking (deep relevance)
• Lazy-loaded embedding model
• Thread-safe
• Restart-safe
• Memory-bounded
• Silent-failure (NEVER crashes brain)
"""

from memory_manager import search as keyword_search
from memory_manager import get_embedding_model
import threading

# ===================== GLOBALS =====================

_model = None
_model_lock = threading.Lock()

_embedding_cache = {}          # text -> embedding tensor
_embedding_cache_lock = threading.Lock()

MAX_VECTOR_CANDIDATES = 30     # hard safety cap per query
MAX_EMBED_CACHE_SIZE = 500     # prevents unbounded RAM growth


# ===================== MODEL LOADER =====================

def get_model():
    """
    Lazy-loads the sentence transformer.
    Safe for:
    - multiple threads
    - restarts
    - healing arbiter resets
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ===================== VECTOR SEARCH =====================

def vector_search(query: str, memories: list, limit: int = 5) -> list:
    """
    Semantic reranking of keyword hits.
    NEVER raises exceptions.
    """
    if not memories:
        return []

    try:
        model = get_embedding_model()

        # Normalize query
        query = query.strip().lower()
        if not query:
            return []

        # Hard cap to avoid overload
        memories = memories[:MAX_VECTOR_CANDIDATES]

        # Encode query
        query_emb = model.encode(query, convert_to_tensor=True)

        mem_embs = []
        valid_memories = []

        with _embedding_cache_lock:
            for m in memories:
                text = m.get("text")
                if not text:
                    continue

                # Cache embeddings
                if text not in _embedding_cache:
                    _embedding_cache[text] = model.encode(
                        text, convert_to_tensor=True
                    )

                    # Cache size guard
                    if len(_embedding_cache) > MAX_EMBED_CACHE_SIZE:
                        _embedding_cache.pop(next(iter(_embedding_cache)))

                mem_embs.append(_embedding_cache[text])
                valid_memories.append(m)

        if not mem_embs:
            return []

        scores = util.cos_sim(query_emb, mem_embs)[0]

        ranked = sorted(
            zip(valid_memories, scores),
            key=lambda x: float(x[1]),
            reverse=True
        )

        return [m for m, _ in ranked[:limit]]

    except Exception:
        # 🔥 Absolute rule: hybrid memory must NEVER crash JARVIS
        return []


# ===================== HYBRID SEARCH =====================

def hybrid_memory_search(query: str, limit: int = 5) -> list:
    """
    Full hybrid retrieval pipeline:
    1. Keyword recall
    2. Semantic rerank
    3. Deduplication
    4. Safe bounded output

    Used directly by brain_loop.
    """
    try:
        query = query.strip().lower()
        if not query:
            return []

        # Step 1: keyword recall
        keyword_hits = keyword_search(query, limit=limit * 2)

        if not keyword_hits:
            return []

        # Step 2: semantic rerank
        vector_hits = vector_search(query, keyword_hits, limit)

        # Step 3: deduplicate
        seen = set()
        final = []

        for m in keyword_hits + vector_hits:
            text = m.get("text")
            if not text or text in seen:
                continue
            seen.add(text)
            final.append(m)

        return final[:limit]

    except Exception:
        # 🔥 Silent failure — memory is non-critical intelligence
        return []
