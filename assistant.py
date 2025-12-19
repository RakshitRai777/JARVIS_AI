import threading
from wakeword import WakeWordDetector
from speech import listen_command
from tts_engine import speak
from groq_ai import GroqAI
from interrupt_listener import interrupt_listener
from autonomy import autonomous_loop
from awareness import update_activity
from memory import add_short, get_short_context, get_long_facts
from habits import log_activity
from commands import handle_command
from config import ASSISTANT_NAME

def main():
    threading.Thread(target=interrupt_listener, daemon=True).start()
    threading.Thread(target=autonomous_loop, daemon=True).start()

    ai = GroqAI()
    wakeword = WakeWordDetector()

    speak(f"{ASSISTANT_NAME} online, sir.")

    while True:
        if wakeword.listen():
            update_activity()
            speak("Yes sir?")
            user = listen_command()

            if not user:
                continue

            log_activity(user)

            command = handle_command(user)
            if command:
                speak(command)
                continue

            prompt = f"""
You are FRIDAY.
Context:
{get_short_context()}
Facts:
{get_long_facts()}
User: {user}
"""
            response = ai.ask(prompt)
            add_short(user, response)
            speak(response)

if __name__ == "__main__":
    main()
