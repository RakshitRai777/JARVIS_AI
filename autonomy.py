import time
from tts_engine import speak
from awareness import is_idle
from habits import common_activity

def autonomous_loop():
    while True:
        if is_idle(600):
            habit = common_activity()
            if habit:
                speak(f"Sir, you often work on {habit} around this time.")
        time.sleep(60)
