from collections import defaultdict
from datetime import datetime

_habits = defaultdict(list)

def log_activity(text):
    _habits[datetime.now().hour].append(text)

def common_activity(hour=None):
    hour = hour or datetime.now().hour
    data = _habits.get(hour, [])
    return max(set(data), key=data.count) if data else None
