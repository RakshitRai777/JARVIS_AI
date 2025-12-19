import webbrowser
import datetime
from logger import info

def handle_command(text):
    text = text.lower()

    if "time" in text:
        response = f"The time is {datetime.datetime.now().strftime('%I:%M %p')}."
        info("Handled time command")
        return response

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        info("Opening YouTube")
        return "Opening YouTube."

    return None
