import datetime
import webbrowser
import subprocess

def handle_command(text):
    text = text.lower()

    if "time" in text:
        return datetime.datetime.now().strftime("Time is %I:%M %p")

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube."

    if "open chrome" in text:
        subprocess.Popen("chrome")
        return "Opening Chrome."

    return None
