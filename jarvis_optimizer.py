import os
import json
import time
import hashlib
from functools import lru_cache
from datetime import datetime, timedelta
import threading
from typing import Dict, Any, Optional

class JarvisOptimizer:
    """Speed optimization layer for JARVIS AI system"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.conversation_limit = 5  # Keep only last 5 exchanges
        
    def _generate_cache_key(self, query: str, context: str = "") -> str:
        """Generate unique cache key for queries"""
        combined = f"{query}_{context}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached_response(self, query: str, context: str = "") -> Optional[str]:
        """Get cached response if available and not expired"""
        cache_key = self._generate_cache_key(query, context)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data['expires']:
                return cached_data['response']
            else:
                del self.cache[cache_key]
        
        return None
    
    def cache_response(self, query: str, response: str, context: str = ""):
        """Cache response with TTL"""
        cache_key = self._generate_cache_key(query, context)
        self.cache[cache_key] = {
            'response': response,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl),
            'timestamp': datetime.now()
        }
    
    def optimize_conversation_history(self, history: list) -> list:
        """Limit conversation history to reduce API payload"""
        return history[-self.conversation_limit:] if len(history) > self.conversation_limit else history
    
    def is_simple_command(self, query: str) -> bool:
        """Check if query can be handled without LLM"""
        simple_patterns = [
            "weather", "time", "date", "volume", "mute", "unmute",
            "system status", "list processes", "recent files",
            "play", "pause", "stop", "resume"
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in simple_patterns)
    
    def get_system_info_cache(self) -> Dict[str, Any]:
        """Cache system information for faster access"""
        cache_key = "system_info"
        
        cached = self.get_cached_response(cache_key)
        if cached:
            return json.loads(cached)
        
        # This would be populated by actual system calls
        system_info = {
            "cpu": "Loading...",
            "memory": "Loading...",
            "disk": "Loading...",
            "timestamp": datetime.now().isoformat()
        }
        
        self.cache_response(cache_key, json.dumps(system_info))
        return system_info
    
    def clear_expired_cache(self):
        """Remove expired cache entries"""
        expired_keys = []
        for key, data in self.cache.items():
            if datetime.now() >= data['expires']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]

# Global optimizer instance
optimizer = JarvisOptimizer()

# Background thread to clean expired cache
def cache_cleanup_worker():
    while True:
        time.sleep(60)  # Clean every minute
        optimizer.clear_expired_cache()

# Start cleanup thread
threading.Thread(target=cache_cleanup_worker, daemon=True).start()
