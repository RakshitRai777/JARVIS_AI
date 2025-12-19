# assistant.py
# FRIDAY – JARVIS-style AI Assistant (Optimized)

from wakeword import WakeWordDetector
from tts_engine import speak
from groq_ai import GroqAI
from config import ASSISTANT_NAME
from memory import add_short, add_long, get_short_context, get_long_facts
from humanize import human_pause

# Whisper is heavy → load ONLY after wake word
whisper_loaded = False
listen_command = None


def should_store_long(text: str) -> bool:
    triggers = [
        "my name is",
        "remember this",
        "remember that",
        "this is important",
        "important"
    ]
    return any(t in text.lower() for t in triggers)


def main():
    global whisper_loaded, listen_command

    print("🔧 Initializing FRIDAY core systems...")
    wakeword = WakeWordDetector()
    ai = GroqAI()

    speak(f"{ASSISTANT_NAME} systems online. Ready, sir.")
    print(f"🔥 Say '{ASSISTANT_NAME}' to wake me.")

    while True:
        # 🟢 WAIT FOR WAKE WORD (FAST + LIGHT)
        if not wakeword.listen():
            continue

        # 🧠 Lazy-load Whisper (ONLY ONCE)
        if not whisper_loaded:
            print("🔊 Loading Whisper speech engine...")
            from speech import listen_command  # Whisper-based
            whisper_loaded = True

        human_pause()
        speak("Yes sir?")
        print("🎤 Listening...")

        # 🎤 SPEECH → TEXT
        user_text = listen_command()

        if not user_text:
            speak("I didn't catch that.")
            continue

        print(f"🧠 User said: {user_text}")

        # 📴 EXIT COMMAND
        if user_text.lower() in ["exit", "quit", "shutdown friday"]:
            speak("Shutting down. Goodbye sir.")
            break

        # 🧠 BUILD CONTEXT
        short_context = get_short_context()
        long_facts = get_long_facts()

        prompt = f"""
You are FRIDAY, a calm, intelligent, human-like AI assistant.

Long-term memory:
{long_facts}

Recent conversation:
{short_context}

User says:
{user_text}

Respond concisely, naturally, and professionally like JARVIS.
"""

        # 🤖 GROQ AI RESPONSE
        response = ai.ask(prompt)

        # 🧠 STORE SHORT-TERM MEMORY
        add_short(user_text, response)

        # 🧠 STORE LONG-TERM MEMORY IF IMPORTANT
        if should_store_long(user_text):
            add_long(user_text)
            speak("I'll remember that, sir.")

        print(f"🤖 FRIDAY: {response}")
        speak(response)


if __name__ == "__main__":
    main()
