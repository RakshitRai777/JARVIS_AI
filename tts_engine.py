import pyttsx3
import random
import time
from interrupt import is_interrupted, clear_interrupt

engine = pyttsx3.init()
engine.setProperty("volume", 1.0)

def speak(text):
    clear_interrupt()
    engine.setProperty("rate", random.randint(165, 175))
    engine.say(text)

    engine.runAndWait()

    while engine.isBusy():
        if is_interrupted():
            engine.stop()
            clear_interrupt()
            return
        time.sleep(0.05)
