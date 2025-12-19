from collections import defaultdict
from datetime import datetime
from logger import debug

_habits = defaultdict(list)

def log_activity(text):
    hour = datetime.now().hour
    _habits[hour].append(text)
    debug(f"Habit logged for hour {hour}: {text}")

def common_activity(hour=None):
    hour = hour or datetime.now().hour
    data = _habits.get(hour, [])
    return max(set(data), key=data.count) if data else None
