import webbrowser
import datetime

def handle_command(text):
    text = text.lower()

    if "time" in text:
        return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}."

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube."

    return None
