import time
_last_activity = time.time()

def update_activity():
    global _last_activity
    _last_activity = time.time()

def is_idle(seconds=300):
    return time.time() - _last_activity > seconds
