import pyttsx3
import random
import time
from interrupt import is_interrupted, clear_interrupt
from logger import info, warn, debug

engine = pyttsx3.init()
engine.setProperty("volume", 1.0)

def speak(text):
    info("TTS started")
    clear_interrupt()

    engine.setProperty("rate", random.randint(165, 175))
    engine.say(text)
    engine.runAndWait()

    while engine.isBusy():
        if is_interrupted():
            warn("Speech interrupted")
            engine.stop()
            clear_interrupt()
            return
        time.sleep(0.05)

    debug("TTS finished")
