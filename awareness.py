import time
from logger import debug

_last_activity = time.time()

def update_activity():
    global _last_activity
    _last_activity = time.time()
    debug("User activity updated")

def is_idle(seconds=300):
    idle = time.time() - _last_activity > seconds
    debug(f"Idle check: {idle}")
    return idle
