import requests
import schedule
import time
import json
import pygame

# Initialize the Groq API endpoint and API key
groq_api_endpoint = "https://api.groq.com/openai/v1/chat/completions"
groq_api_key = "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"

# Initialize the pygame mixer
pygame.init()
pygame.mixer.init()

# Define the alarm flow
def set_alarm(alarm_time, message, sound_file):
    # Create a new Groq query
    query = {
        "query": "alarm",
        "parameters": {
            "time": alarm_time,
            "message": message
        }
    }

    # Execute the query using the requests library
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(groq_api_endpoint, headers=headers, data=json.dumps(query))

    # Schedule the alarm using the schedule library
    schedule.every().day.at(alarm_time).do(trigger_alarm, message, sound_file)

def trigger_alarm(message, sound_file):
    # Trigger the alarm (e.g., print a message or play a sound)
    print(f"Alarm triggered: {message}")
    play_sound(sound_file)

def play_sound(sound_file):
    # Play the custom sound file
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()

# Example usage
alarm_time = "11:00"  # 8:00 AM
message = "Good morning! Time to wake up!"
sound_file = "Morning_Alarm.mp3"  # Replace with your sound file path
set_alarm(alarm_time, message, sound_file)

# Run the scheduling loop
while True:
    schedule.run_pending()
    time.sleep(1)