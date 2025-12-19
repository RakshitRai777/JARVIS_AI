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

# 🔹 Central logger
from logger import info, warn, error, debug


def main():
    info("Starting FRIDAY core systems")

    # Background systems
    threading.Thread(
        target=interrupt_listener,
        daemon=True,
        name="InterruptListener"
    ).start()
    info("Interrupt listener started")

    threading.Thread(
        target=autonomous_loop,
        daemon=True,
        name="AutonomyLoop"
    ).start()
    info("Autonomy loop started")

    ai = GroqAI()
    wakeword = WakeWordDetector()

    speak(f"{ASSISTANT_NAME} online, sir.")
    info(f"{ASSISTANT_NAME} is online and ready")

    while True:
        info("Listening for wake word...")
        if wakeword.listen():
            info("Wake word detected")

            update_activity()
            speak("Yes sir?")
            info("Prompted user for command")

            user = listen_command()

            if not user:
                warn("No speech detected after wake word")
                continue

            info(f"User said: {user}")
            log_activity(user)

            # Handle direct commands (open apps, time, etc.)
            command_response = handle_command(user)
            if command_response:
                info(f"Command handled locally: {command_response}")
                speak(command_response)
                continue

            # AI prompt
            prompt = f"""
You are FRIDAY.
Context:
{get_short_context()}
Facts:
{get_long_facts()}
User: {user}
"""

            debug("Sending prompt to Groq AI")
            response = ai.ask(prompt)

            if not response:
                error("AI returned empty response")
                speak("Sorry sir, something went wrong.")
                continue

            info(f"FRIDAY response: {response}")
            add_short(user, response)
            speak(response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        warn("FRIDAY shutdown requested by user")
    except Exception as e:
        error(f"Fatal error in assistant: {e}")
