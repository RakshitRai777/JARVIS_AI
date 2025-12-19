import time
from tts_engine import speak
from awareness import is_idle
from habits import common_activity
from logger import info, debug

def autonomous_loop():
    info("Autonomy loop started")

    while True:
        if is_idle(600):
            debug("Idle detected for 10 minutes")
            habit = common_activity()
            if habit:
                info(f"Autonomous suggestion triggered: {habit}")
                speak(f"Sir, you often work on {habit} around this time.")
        time.sleep(60)
