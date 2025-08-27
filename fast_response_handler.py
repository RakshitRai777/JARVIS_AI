import asyncio
import json
from typing import Dict, Any, Optional
from jarvis_optimizer import optimizer

class FastResponseHandler:
    """Handles fast responses for common queries"""
    
    def __init__(self):
        self.weather_cache = {}
        self.system_cache = {}
        self.last_system_check = None
    
    def handle_weather(self, city: str) -> Optional[str]:
        """Fast weather response with caching"""
        cache_key = f"weather_{city}"
        cached = optimizer.get_cached_response(cache_key)
        
        if cached:
            return cached
        
        # This would call actual weather API
        # For now, return cached format
        response = f"Weather information for {city} would be fetched here"
        optimizer.cache_response(cache_key, response)
        return response
    
    def handle_system_status(self) -> str:
        """Fast system status response"""
        cache_key = "system_status"
        cached = optimizer.get_cached_response(cache_key)
        
        if cached:
            return cached
        
        # Simulate system info
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        
        response = f"System Status - CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%"
        optimizer.cache_response(cache_key, response)
        return response
    
    def handle_time_date(self) -> str:
        """Fast time/date response"""
        from datetime import datetime
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')} and date is {now.strftime('%B %d, %Y')}"
    
    def handle_simple_command(self, query: str) -> Optional[str]:
        """Handle simple commands without LLM"""
        query_lower = query.lower()
        
        # Time/Date commands
        if any(word in query_lower for word in ["what time", "current time", "what's the time"]):
            return self.handle_time_date()
        
        # System commands
        if "system status" in query_lower or "system info" in query_lower:
            return self.handle_system_status()
        
        # Volume commands
        if "mute" in query_lower:
            return "Volume muted"
        if "unmute" in query_lower:
            return "Volume unmuted"
        
        return None

# Global handler instance
fast_handler = FastResponseHandler()
