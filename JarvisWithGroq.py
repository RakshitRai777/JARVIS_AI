import os
import re
import json
import webbrowser
import threading
import speech_recognition as sr
import edge_tts
import asyncio
import psutil
import time
import pygame
import random
import requests
import subprocess
import win32com.client
import difflib
import yt_dlp
import vlc
import pythoncom
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from mailjet_rest import Client
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Google Calendar API imports
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from playlist_manager import playlist_manager


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please set it as an environment variable.")

wake_word_event = threading.Event()  # Event-based trigger for wake-word detection
alarms = []  # List to store alarm
CONVERSATION_FILE = "conversation_history.json"

# Log file for OS activities
SYSTEM_LOG_FILE = "os_operations.log"

# Global player instance to control song playback
player = None


# Import the new language configuration
from language_config import (
    LANGUAGE_VOICE_MAP,
    LANGUAGE_CODE_MAP,
    validate_language,
    get_voice_for_language,
    get_language_code,
    get_supported_languages
)

# Global variable to store the current voice and language
current_voice = "en-GB-RyanNeural"  # Default male voice
current_language = "english"  # Default language

# Helper: Translate text to a target language using Google Translate API
def translate_text(text, target_language_code):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_language_code,
            "dt": "t",
            "q": text,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return result[0][0][0]
        else:
            return text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

#Global variable to store current personality
personality_mode = "default" # Default personality

# Context Manager class to manage conversation context
class ContextManager:
    def __init__(self):
        self.context = {}

    def update_context(self, key, value):
        self.context[key] = value

    def get_context(self, key):
        return self.context.get(key, None)

    def clear_context(self):
        self.context.clear()

context_manager = ContextManager()

# Load past conversations
def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

# Save conversations
def save_conversation_history():
    with open(CONVERSATION_FILE, "w") as file:
        json.dump(conversation_history, file, indent=4)

conversation_history = load_conversation_history()

def adjust_max_tokens(user_input):
    if len(user_input.split()) < 10:  # Simple question
        return 200
    elif len(user_input.split()) < 20:  # Medium complexity question
        return 600
    else:  # Complex or open-ended question
        return 10000

def get_groq_response(query):
    # Add personality to system prompt
    global personality_mode
    system_prompt = f"You are an AI assistant named JARVIS. Your personality is '{personality_mode}'. Analyze the user's emotion and respond accordingly but do not say the emotion, say only the answer. Respond in the style of your current personality."
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # Updated model
        "messages": [
            {"role": "system", "content": system_prompt},
            *conversation_history,  # Include the conversation history
        ],
        "max_tokens": adjust_max_tokens(query),  # Dynamically adjust max_tokens
        "temperature": 0.7,
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

    try:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        return "Invalid response format."

def speak_threaded(text):
    # Use a new event loop for each thread to avoid blocking issues
    def run():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(speak(text))
        new_loop.close()
    threading.Thread(target=run, daemon=True).start()

async def speak(text: str):
    try:
        communicate = edge_tts.Communicate(text, current_voice)
        output_file = "output.mp3"
        await communicate.save(output_file)

        pygame.init()
        pygame.mixer.init()

        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.quit()
        pygame.mixer.quit()

        os.remove(output_file)
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

def listen_threaded():
    threading.Thread(target=listen, daemon=True).start()

def listen():
    """Enhanced listen function with better error handling and debug logging."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("DEBUG: Microphone initialized successfully")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("DEBUG: Ambient noise adjusted")
            print("Listening for a command...")
            
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                print("DEBUG: Audio captured successfully")
                
                try:
                    result = recognizer.recognize_google(audio, language="en-GB")
                    print(f"DEBUG: Recognized text: {result}")
                    return result.lower().strip() if result else ""
                except sr.UnknownValueError:
                    print("DEBUG: Could not understand the command (UnknownValueError)")
                    return ""
                except sr.RequestError as e:
                    print(f"DEBUG: Speech Recognition service error: {e}")
                    return ""
                    
            except sr.WaitTimeoutError:
                print("DEBUG: Timeout - No command detected within 5 seconds")
                return ""
            except Exception as e:
                print(f"DEBUG: Error during audio capture: {e}")
                return ""
                
    except OSError as e:
        print(f"DEBUG: Microphone access error: {e}")
        print("DEBUG: Please check microphone permissions and connection")
        return ""
    except Exception as e:
        print(f"DEBUG: Unexpected error in listen(): {e}")
        return ""

def get_title():
    return random.choice(["Sir", "Boss", "Master"])

def set_personality(mode):
    """Sets the personality mode."""
    global personality_mode
    personality_mode = mode
    return f"Personality mode changed to {mode}."

# Fetch installed applications
def get_installed_apps():
    app_paths = {}
    possible_dirs = [
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users\\%USERNAME%\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"
    ]
    
    for directory in possible_dirs:
        if os.path.exists(directory):
            for app in os.listdir(directory):
                app_name = app.replace(".exe", "").lower()
                app_paths[app_name] = os.path.join(directory, app)

    shell = win32com.client.Dispatch("WScript.Shell")
    start_menu_path = os.path.expandvars(r"C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs")
    for root, dirs, files in os.walk(start_menu_path):
        for file in files:
            if file.endswith(".lnk"):
                shortcut = shell.CreateShortcut(os.path.join(root, file))
                app_name = file.replace(".lnk", "").lower()
                app_paths[app_name] = shortcut.TargetPath
    return app_paths

# Launch an application
def launch_application(app_name):
    installed_apps = get_installed_apps()
    app_names = list(installed_apps.keys())
    match = difflib.get_close_matches(app_name.lower(), app_names, n=1, cutoff=0.5)
    if match:
        app_path = installed_apps[match[0]]
        try:
            subprocess.Popen(app_path, shell=True)
            return f"Launching {match[0].title()}, {get_title()}."
        except Exception as e:
            return f"Couldn't open {match[0].title()}, {get_title()}. Error: {e}"
    else:
        return f"Application not found, {get_title()}. Try another name."

# Close an application
def close_application(app_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if app_name.lower() in proc.info['name'].lower():
            proc.terminate()
            return f"Closing {proc.info['name']}, {get_title()}."
    return f"Application {app_name} not found, {get_title()}."


# Open a website
def open_website(website_name):
    if not website_name:
        return "Please specify a website, sir."
    
    # Extract domain name for a cleaner response
    site_name = website_name.replace("www.", "").split(".")[0].capitalize()

    if not website_name.startswith("http"):
        website_name = "https://www." + website_name if "." in website_name else f"https://www.google.com/search?q={website_name}"
    
    try:
        webbrowser.open(website_name)
        return f"Opening {site_name}, sir."
    except Exception as e:
        return f"Sorry, I couldn't open the website. Error: {e}"

# --- OS-Focused Enhancements ---
def log_os_operation(operation, details):
    """Logs OS-related operations to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {operation}: {details}\n"
    with open(SYSTEM_LOG_FILE, "a") as log_file:
        log_file.write(log_entry)

def get_system_stats():
    """Returns CPU, memory, and disk usage."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent
    return {
        "cpu": cpu_usage,
        "memory": memory_usage,
        "disk": disk_usage
    }

def monitor_system_resources(threshold=80):
    """Checks if CPU/memory exceeds a threshold."""
    stats = get_system_stats()
    alerts = []
    if stats["cpu"] > threshold:
        alerts.append(f"High CPU usage: {stats['cpu']}%")
    if stats["memory"] > threshold:
        alerts.append(f"High memory usage: {stats['memory']}%")
    return alerts

def list_recent_files(directory=".", limit=5):
    """Lists recently modified files in a directory."""
    files = []
    for entry in os.scandir(directory):
        if entry.is_file():
            files.append({
                "name": entry.name,
                "modified": datetime.fromtimestamp(entry.stat().st_mtime)
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files[:limit]

def get_running_processes():
    """Lists all running processes (like Task Manager)."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        processes.append({
            "pid": proc.info['pid'],
            "name": proc.info['name'],
            "cpu": proc.info['cpu_percent'],
            "memory": proc.info['memory_percent']
        })
    return processes

def mute_system_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMute(1, None)  # 1 = mute, 0 = unmute

def unmute_system_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    # Explicitly check and unmute if needed
    if volume.GetMute() == 1:
        volume.SetMute(0, None)

def play_alarm():
    """Function to play the JARVIS alarm sound."""
    try:
        # Create VLC instance first
        instance = vlc.Instance()
        if instance:
            media_player = instance.media_player_new()
            if media_player:
                # Use a relative path or check if file exists
                alarm_file = "Morning_Alarm.mp3"  # Use the file that exists in your directory
                if os.path.exists(alarm_file):
                    media = instance.media_new(alarm_file)
                    if media:
                        media_player.set_media(media)
                        media_player.play()
                        time.sleep(10)  # Allow the sound to play for a while
                        media_player.stop()
                    else:
                        print("Failed to create media for alarm")
                else:
                    print(f"Alarm file not found: {alarm_file}")
            else:
                print("Failed to create media player for alarm")
        else:
            print("Failed to create VLC instance for alarm")
    except Exception as e:
        print(f"Error playing alarm: {e}")


def check_alarms():
    """Continuously checks for alarm triggers."""
    while True:
        now = datetime.now().strftime("%H:%M")
        for alarm in alarms:
            if now == alarm:
                print(f"JARVIS: Alarm for {now} triggered!")
                play_alarm()
                alarms.remove(alarm)  # Remove the alarm after triggering
        time.sleep(30)  # Check every 30 seconds


def set_alarm(alarm_time):
    """Function to add an alarm to the list."""
    alarms.append(alarm_time)
    print(f"JARVIS: Alarm set for {alarm_time}, sir.")


# Run the alarm checking function in a background thread
threading.Thread(target=check_alarms, daemon=True).start()

def get_weather(city):
    try:
        # Enhanced web scraping for global weather data
        city = city.strip()
        
        # Updated Google search approach with better selectors
        search_url = f"https://www.google.com/search?q=weather+in+{city.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # More robust element finding with multiple selectors
        temp_selectors = ['span.wob_t', 'span[data-unit="°C"]', 'div.BNeawe.iBp4i.AP7Wnd']
        condition_selectors = ['div.wob_dcp', 'div.BNeawe.tAd8D.AP7Wnd', 'span#wob_dc']
        
        temperature = None
        condition = None
        
        # Try multiple temperature selectors
        for selector in temp_selectors:
            temp_elem = soup.select_one(selector)
            if temp_elem:
                temp_text = temp_elem.get_text().strip()
                if temp_text and any(char.isdigit() for char in temp_text):
                    temperature = temp_text
                    break
        
        # Try multiple condition selectors
        for selector in condition_selectors:
            cond_elem = soup.select_one(selector)
            if cond_elem:
                cond_text = cond_elem.get_text().strip()
                if cond_text and not any(char.isdigit() for char in cond_text):
                    condition = cond_text
                    break
        
        if temperature and condition:
            return f"The current temperature in {city} is {temperature} with {condition}."
        
        # Fallback: Try to extract from search results
        all_text = soup.get_text()
        weather_patterns = [
            r'(\d+°[CF])',  # Temperature pattern
            r'(Sunny|Cloudy|Rainy|Partly cloudy|Clear|Overcast|Snow|Thunderstorm)',  # Weather conditions
        ]
        
        import re
        temp_match = re.search(weather_patterns[0], all_text)
        condition_match = re.search(weather_patterns[1], all_text, re.IGNORECASE)
        
        if temp_match and condition_match:
            temp = temp_match.group(1)
            condition = condition_match.group(1).capitalize()
            return f"The current temperature in {city} is {temp} with {condition}."
        
        return f"Could not retrieve weather information for {city}. Please check the city name and try again."
    
    except requests.exceptions.Timeout:
        return f"Request timed out while fetching weather for {city}. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error connecting to weather services for {city}: {e}"
    except Exception as e:
        return f"An error occurred while fetching weather for {city}: {e}"

def get_latest_news(place):
    search_url = f"https://www.bbc.co.uk/search?q={place}&filter=news"
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = []
        for item in soup.find_all('li', class_='css-1gkxz2s'):
            headline = item.find('a')
            if headline:
                headlines.append(headline.get_text())
        if headlines:
            return "Here are the latest news headlines: " + ", ".join(headlines[:5])
        else:
            return "Sorry, I couldn't find any news at the moment."
    except Exception as e:
        return f"Error retrieving news: {e}"

# Add the email sending function
def send_email(recipient, subject, text_part, html_part):
    api_key = '2001047198444aba43aa59f1cf6fcf24'
    api_secret = 'f4135e88b350e803dbd1c1677c7b3da9'
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "jarvisai77777770@gmail.com",
                    "Name": "Rakshit Rai"
                },
                "To": [
                    {
                        "Email": "recipient",
                        "Name": "recipient.split('@')[0]"
                    }
                ],
                "Subject": subject,
                "TextPart": text_part,
                "HTMLPart": html_part
            }
        ]
    }

    result = mailjet.send.create(data=data)
    return result.status_code, result.json()

# Background Wake-Word Listener
def background_wake_word_listener():
    """Enhanced wake word detection with better error handling and debug logging."""
    recognizer = sr.Recognizer()
    
    while True:
        try:
            with sr.Microphone() as source:
                print("DEBUG: Wake word listener - Microphone initialized")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("DEBUG: Wake word listener - Listening...")
                
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    print("DEBUG: Wake word listener - Audio captured")
                    
                    try:
                        query = recognizer.recognize_google(audio, language="en-GB")
                        print(f"DEBUG: Wake word listener - Recognized: '{query}'")
                        
                        if query and "jarvis" in query.lower():
                            print("DEBUG: Wake word 'jarvis' detected!")
                            wake_word_event.set()
                            print("DEBUG: Wake word event set successfully")
                        else:
                            print("DEBUG: No wake word detected in this audio")
                            
                    except sr.UnknownValueError:
                        print("DEBUG: Wake word listener - Could not understand audio")
                    except sr.RequestError as e:
                        print(f"DEBUG: Wake word listener - Recognition error: {e}")
                        
                except sr.WaitTimeoutError:
                    print("DEBUG: Wake word listener - Timeout, no speech detected")
                except Exception as e:
                    print(f"DEBUG: Wake word listener - Audio capture error: {e}")
                    
        except OSError as e:
            print(f"DEBUG: Wake word listener - Microphone error: {e}")
            print("DEBUG: Please check microphone permissions")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"DEBUG: Wake word listener - Unexpected error: {e}")
            time.sleep(1)

# Add a global variable to store conversation history
conversation_history = []

async def play_youtube_song(song_name):
    global player
    pythoncom.CoInitialize()  # Initialize COM

    # Stop any currently playing song before starting a new one
    if player is not None:
        try:
            player.stop()
        except Exception as e:
            print(f"Error stopping previous player: {e}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            
            if info and 'entries' in info and info['entries']:
                video = info['entries'][0]
                url = video.get('url')
                
                if url:
                    # Add to playlist manager
                    track = playlist_manager.current_track
                    if not track or track.title != video.get('title', ''):
                        playlist_manager.add_track(
                            title=video.get('title', 'Unknown'),
                            artist=video.get('uploader', '')
                        )
                    
                    print(f"Playing: {video.get('title', 'Unknown')}")
                    # Create VLC instance and media player
                    instance = vlc.Instance('--no-xlib')
                    if instance:
                        player = instance.media_player_new()
                        if player:
                            media = instance.media_new(url)
                            if media:
                                player.set_media(media)
                                
                                # Auto-play next track when current ends
                                def on_end(event):
                                    print("Playback finished. Auto-playing next track...")
                                    next_track = playlist_manager.play_next_track()
                                    if next_track:
                                        asyncio.create_task(play_youtube_song(next_track.title))
                                    else:
                                        print("No more tracks in queue")
                                
                                event_manager = player.event_manager()
                                event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, on_end)
                                player.play()
                                speak_threaded(f"Playing {video.get('title', 'Unknown')}, {get_title()}.")
                            else:
                                print("Failed to create media")
                                speak_threaded(f"Sorry, {get_title()}. I couldn't play that song.")
                        else:
                            print("Failed to create media player")
                            speak_threaded(f"Sorry, {get_title()}. I couldn't create the media player.")
                    else:
                        print("Failed to create VLC instance")
                        speak_threaded(f"Sorry, {get_title()}. I couldn't initialize the media player.")
                else:
                    print("No URL found for video")
                    speak_threaded(f"Sorry, {get_title()}. I couldn't find a playable version of that song.")
            else:
                print("No video found")
                speak_threaded(f"Sorry, {get_title()}. I couldn't find that song on YouTube.")
    except Exception as e:
        print(f"Error playing YouTube song: {e}")
        speak_threaded(f"Sorry, {get_title()}. There was an error playing the song.")
    finally:
        pythoncom.CoUninitialize()  # Uninitialize COM

def pause_song():
    """Pauses the currently playing song."""
    global player
    try:
        if player is not None and player.is_playing():
            player.pause()
            return "Song paused, boss."
        return "No song is playing."
    except Exception as e:
        print(f"Error pausing song: {e}")
        return "Error pausing the song."

def resume_song():
    """Resumes the song if it was paused."""
    global player
    try:
        if player is not None:
            player.play()
            return "Resuming song."
        return "No song is available to resume."
    except Exception as e:
        print(f"Error resuming song: {e}")
        return "Error resuming the song."

def stop_song():
    """Stops the currently playing song."""
    global player
    try:
        if player is not None:
            player.stop()
            return "Song stopped, sir."
        return "No song is playing."
    except Exception as e:
        print(f"Error stopping song: {e}")
        return "Error stopping the song."

def deadlock_watchdog(interval=10):
    """Periodically checks for deadlocks in the main thread."""
    while True:
        time.sleep(interval)
        threads = threading.enumerate()
        thread_states = {}

        #Collect thread states
        for thread in threads:
            if thread.is_alive():
                thread_states[thread.name] = thread
            
        #Detect potential deadlocks
        #For simplicity, we assume threads stuck for too long are in deadlock
        for thread_name, thread in thread_states.items():
            if not thread.is_alive():
                continue
            # Check if the thread is stuck (e.g., not progressing)
            # You can add custom logic here to detect specific deadlock scenarios
            try:
                if hasattr(thread, "_target") and thread._target:
                    print(f"Thread {thread_name} is running target: {thread._target}")
            except Exception as e:
                print(f"Error checking thread {thread_name}: {e}")
        
        # Attempt to resolve deadlocks
        # For example, restart or terminate stuck threads
        for thread_name, thread in thread_states.items():
            if not thread.is_alive():
                print(f"Thread {thread_name} is not alive. Attempting to resolve...")
                # Add logic to restart or terminate the thread
                # Example: Restart the thread by creating a new instance
                # Note: This requires the thread's target function to be restartable
                try:
                    if hasattr(thread, "_target") and thread._target:
                        new_thread = threading.Thread(target=thread._target, name=thread_name)
                        new_thread.start()
                        print(f"Restarted thread {thread_name}.")
                except Exception as e:
                    print(f"Failed to restart thread {thread_name}: {e}")

# Start the deadlock watchdog in a separate thread
threading.Thread(target=deadlock_watchdog, daemon=True).start()


# --- New function for unified command processing ---
def process_command(query):
    # Import the alarm system
    from jarvis_alarm_system_fixed import alarm_system, set_alarm_voice, list_alarms_voice
    
    # Calendar commands
    if "add event" in query or "schedule event" in query:
        # Example: "add event Meeting at 2025-08-09T15:00:00"
        match = re.search(r'(?:add|schedule) event ([\w\s]+) at ([\d\-T:]+)', query)
        if match:
            summary = match.group(1).strip()
            start_time = match.group(2).strip()
    global conversation_history, current_voice, personality_mode, current_language
    # Personality change command
    if "change personality to" in query:
        match = re.search(r"change personality to ([a-zA-Z ]+)", query)
        if match:
            new_mode = match.group(1).strip().lower()
            personality_mode = new_mode
            return f"Personality changed to {new_mode} mode."
        else:
            return "Please specify a personality mode to change to."

    # Query current personality
    if "what is your personality" in query or "current personality" in query:
        return f"My current personality mode is {personality_mode}."

    if "exit" in query or "stop listening" in query or "bye jarvis" in query:
        save_conversation_history()
        return "Okay, I'll go back to sleep."

    elif "weather" in query:
        city = query.replace("weather in", "").strip()
        if city:
            weather_info = get_weather(city)
            return f"{weather_info}, {get_title()}."
        else:
            return "Please specify the city name."

    elif "set alarm for" in query:
        time_part = query.replace("set alarm for", "").strip()
        from jarvis_alarm_system_fixed import set_alarm_voice
        return set_alarm_voice(time_part, "Alarm")
    
    elif "list alarms" in query:
        from jarvis_alarm_system_fixed import list_alarms_voice
        return list_alarms_voice()
    
    elif "snooze alarm" in query:
        from jarvis_alarm_system_fixed import alarm_system
        return alarm_system.snooze_alarm()
    
    elif "dismiss alarm" in query:
        from jarvis_alarm_system_fixed import alarm_system
        return alarm_system.dismiss_alarm()

    elif "open" in query:
        app_name = query.replace("open", "").strip()
        if ".com" in app_name or ".org" in app_name or ".net" in app_name:
            response = open_website(app_name)
        else:
            response = launch_application(app_name)
        return response

    elif "play" in query:
        song_name = query.replace("play", "").strip()
        # For dashboard, just trigger the song and return a message
        threading.Thread(target=asyncio.run, args=(play_youtube_song(song_name),), daemon=True).start()
        return f"Playing {song_name}."

    elif "pause" in query or "pause the song" in query:
        response = pause_song()
        return response

    elif "resume" in query or "resume the song" in query:
        response = resume_song()
        return response

    elif "stop" in query or "stop the song" in query:
        response = stop_song()
        return response

    # Voice and Language Switching command
    elif "change voice to" in query or "change language to" in query or "switch to" in query:
        lang_match = re.search(r"(?:change voice to|change language to|switch to) ([a-zA-Z ]+)", query)
        if lang_match:
            lang = lang_match.group(1).strip().lower()
            
            # Validate and get the voice
            if validate_language(lang):
                current_voice = get_voice_for_language(lang)
                current_language = lang
                
                # Get language code for translation
                lang_code = get_language_code(lang)
                
                # Create appropriate response
                language_name = lang.title()
                
                # Check if it's a specific variant
                if "male" in lang or "female" in lang:
                    response = f"Voice changed to {language_name}."
                else:
                    response = f"Language changed to {language_name} with appropriate voice."
                
                # Add supported languages hint for invalid requests
                supported_langs = ", ".join(get_supported_languages()[:10])
                print(f"DEBUG: Language changed to {lang} with voice {current_voice}")
                
                return response
            else:
                supported_langs = ", ".join(get_supported_languages()[:10])
                return f"Sorry, I don't support '{lang}'. Supported languages include: {supported_langs}, and more. Try saying 'change language to spanish' or 'switch to german'."
        else:
            return "Please specify a language to change to. For example: 'change language to spanish' or 'switch to french'."

    # OS-Specific Commands
    elif "system status" in query:
        stats = get_system_stats()
        return f"CPU: {stats['cpu']}%, Memory: {stats['memory']}%, Disk: {stats['disk']}%"

    elif "list processes" in query:
        processes = get_running_processes()[:5]
        response = " | ".join([f"{p['name']} (CPU: {p['cpu']}%)" for p in processes])
        return f"Running processes: {response}"

    elif "recent files" in query:
        files = list_recent_files()
        response = ", ".join([f['name'] for f in files])
        return f"Recent files: {response}"

    elif "increase volume" in query:
        try:
            # Use pycaw to increase volume by a step
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_volume = volume.GetMasterVolumeLevelScalar()
            new_volume = min(current_volume + 0.1, 1.0)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
            return "Volume increased, sir."
        except Exception as e:
            return f"Sorry, I couldn't increase the volume. {e}"
    elif "decrease volume" in query:
        try:
            # Use pycaw to decrease volume by a step
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_volume = volume.GetMasterVolumeLevelScalar()
            new_volume = max(current_volume - 0.1, 0.0)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
            return "Volume decreased, sir."
        except Exception as e:
            return f"Sorry, I couldn't decrease the volume. {e}"
    elif "mute volume" in query:
        try:
            mute_system_volume()
            return "Volume muted, sir."
        except Exception as e:
            return "Sorry, I couldn't mute the volume."
    elif "unmute volume" in query:
        try:
            unmute_system_volume()
            return "Volume unmuted, sir."
        except Exception as e:
            return "Sorry, I couldn't unmute the volume."
    elif "shutdown" in query:
        os.system("shutdown /s /t 1")
        return "Shutting down the system, sir."
    elif "send email" in query:
        # For dashboard, email flow is not interactive. You can extend this to accept JSON payloads.
        return "Email feature is only available via voice for now."
    else:
        # LLM fallback
        conversation_history.append({"role": "user", "content": query})
        context_manager.update_context("last_query", query)
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"You are an AI assistant named JARVIS. Your personality is '{personality_mode}'. Analyze the user's emotion and respond accordingly but do not say the emotion, say only the answer. Respond in the style of your current personality."},
                *conversation_history,
            ],
            "max_tokens": adjust_max_tokens(query),
            "temperature": 0.7,
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            full_response = result["choices"][0]["message"]["content"].strip()
            # Remove markdown asterisks used for bold/italic highlighting
            full_response = full_response.replace("*", "")
            detected_emotion = "neutral"
            emotion_match = re.search(r"Emotion:\s*(\w+)", full_response, re.IGNORECASE)
            if emotion_match:
                detected_emotion = emotion_match.group(1).lower()
                actual_response = re.sub(r"Emotion:\s*\w+\s*", "", full_response).strip()
            else:
                actual_response = full_response
            conversation_history.append({"role": "assistant", "content": actual_response})
            if detected_emotion == "sad":
                actual_response = f"I'm here for you, {get_title()}. {actual_response}"
            elif detected_emotion == "happy":
                actual_response = f"That's great to hear, {get_title()}! {actual_response}"
            elif detected_emotion == "angry":
                actual_response = f"I understand your frustration, {get_title()}. {actual_response}"
            elif detected_emotion == "excited":
                actual_response = f"Wow! That sounds amazing, {get_title()}! {actual_response}"
            return actual_response
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return "Sorry, I couldn't generate a response."


# --- Voice/assistant loop now uses process_command ---
async def handle_commands():
    global conversation_history, current_voice, personality_mode
    await speak(f"Yes, {get_title()}! How can I assist you today?")

    while True:
        query = listen()
        if not query:
            continue

        response = process_command(query)
        # Only exit loop if user said exit/stop/bye
        if response == "Okay, I'll go back to sleep.":
            await speak(response)
            wake_word_event.clear()
            break

        # For music, play, etc., the action is already triggered, just speak the response
        await speak(response)


async def main():
    """Enhanced main function with better error handling and startup diagnostics."""
    print("=== JARVIS Voice Assistant Starting ===")
    print("DEBUG: Checking microphone availability...")
    
    # Test microphone before starting
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("DEBUG: Microphone test successful")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("DEBUG: Ambient noise adjustment complete")
    except Exception as e:
        print(f"DEBUG: Microphone test failed: {e}")
        print("DEBUG: Please check microphone permissions and connection")
        return
    
    print("DEBUG: Starting wake word listener...")
    threading.Thread(target=background_wake_word_listener, daemon=True).start()
    
    print("DEBUG: JARVIS is ready and listening for 'jarvis' wake word")
    print("DEBUG: Say 'jarvis' to activate voice commands")
    
    try:
        while True:
            print("DEBUG: Waiting for wake word...")
            wake_word_event.wait()  # Wait for wake-word event to be set
            print("DEBUG: Wake word event received")
            wake_word_event.clear()  # Reset wake-word event
            print("DEBUG: Starting command handler...")
            await handle_commands()  # Start handling user commands
            print("DEBUG: Command handler finished, returning to wake word listening")
            # After handling commands, continue listening for wake word endlessly
    except KeyboardInterrupt:
        print("\nDEBUG: JARVIS shutting down...")
    except Exception as e:
        print(f"DEBUG: Error in main loop: {e}")
    finally:
        print("DEBUG: Exiting main loop.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nJARVIS: Goodbye!")
    except Exception as e:
        print(f"JARVIS: Error starting up: {e}")
