import pyttsx3
import time
import random

engine = pyttsx3.init()
engine.setProperty("volume", 1.0)

for voice in engine.getProperty("voices"):
    if "david" in voice.name.lower():
        engine.setProperty("voice", voice.id)
        break

def speak(text, rate=1.0):
    engine.setProperty("rate", int(170 * rate))
    time.sleep(random.uniform(0.15, 0.35))
    engine.say(text)
    engine.runAndWait()
