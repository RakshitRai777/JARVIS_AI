"""
Iron-Man Style JARVIS Alarm System
A sophisticated alarm system for JARVIS with voice control and visual feedback
"""

import os
import json
import threading
import time
import pygame
import datetime
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Initialize pygame for audio
pygame.init()
pygame.mixer.init()

@dataclass
class Alarm:
    """Represents a single alarm"""
    id: str
    time: str  # HH:MM format
    label: str
    sound_file: str
    enabled: bool = True
    recurring: bool = False
    days: List[str] = None  # ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    snooze_count: int = 0
    max_snoozes: int = 3
    created_at: str = ""

    def __post_init__(self):
        if self.days is None:
            self.days = []
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()

def get_title():
    """Get Iron-Man style title for JARVIS"""
    return random.choice(["Sir", "Boss", "Master", "Mr. Stark", "Tony"])

class IronManAlarmSystem:
    """Sophisticated alarm system with Iron-Man style interface"""
    
    def __init__(self, config_file: str = "jarvis_alarms.json"):
        self.config_file = config_file
        self.alarms: List[Alarm] = []
        self.is_running = False
        self.alarm_thread = None
        self.current_alarm = None
        self.load_alarms()
        
        # Iron-Man style sound effects
        self.sounds = {
            'alarm': "Morning_Alarm.mp3",
            'notification': "notification.mp3",
            'startup': "jarvis_startup.mp3"
        }
        
    def load_alarms(self):
        """Load alarms from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.alarms = [Alarm(**alarm) for alarm in data]
        except Exception as e:
            print(f"JARVIS: Error loading alarms: {e}")
            self.alarms = []
    
    def save_alarms(self):
        """Save alarms to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump([asdict(alarm) for alarm in self.alarms], f, indent=2)
        except Exception as e:
            print(f"JARVIS: Error saving alarms: {e}")
    
    def add_alarm(self, time_str: str, label: str, sound_file: str = "Morning_Alarm.mp3", 
                  recurring: bool = False, days: List[str] = None) -> str:
        """Add a new alarm with Iron-Man style feedback"""
        alarm_id = f"alarm_{int(time.time())}"
        alarm = Alarm(
            id=alarm_id,
            time=time_str,
            label=label,
            sound_file=sound_file,
            recurring=recurring,
            days=days or []
        )
        
        self.alarms.append(alarm)
        self.save_alarms()
        
        return f"Alarm '{label}' set for {time_str}, {get_title()}."
    
    def remove_alarm(self, alarm_id: str) -> str:
        """Remove an alarm"""
        alarm = next((a for a in self.alarms if a.id == alarm_id), None)
        if alarm:
            self.alarms.remove(alarm)
            self.save_alarms()
            return f"Alarm '{alarm.label}' removed, {get_title()}."
        return "Alarm not found."
    
    def list_alarms(self) -> List[Dict]:
        """List all alarms"""
        return [asdict(alarm) for alarm in self.alarms]
    
    def start_alarm_monitor(self):
        """Start the Iron-Man style alarm monitoring"""
        if self.is_running:
            return "Alarm system already running."
        
        self.is_running = True
        self.alarm_thread = threading.Thread(target=self._monitor_alarms, daemon=True)
        self.alarm_thread.start()
        return "Iron-Man alarm system activated, sir."
    
    def stop_alarm_monitor(self):
        """Stop the alarm monitoring"""
        if not self.is_running:
            return "Alarm system not running."
        
        self.is_running = False
        if self.alarm_thread:
            self.alarm_thread.join(timeout=1)
        return "Iron-Man alarm system deactivated."
    
    def _monitor_alarms(self):
        """Background monitoring for alarms"""
        while self.is_running:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%a").lower()[:3]
            
            for alarm in self.alarms:
                if not alarm.enabled:
                    continue
                
                # Check if it's time for the alarm
                if alarm.time == current_time:
                    # Check recurring days if applicable
                    if alarm.recurring and alarm.days and current_day not in alarm.days:
                        continue
                    
                    # Trigger alarm
                    self._trigger_alarm(alarm)
            
            time.sleep(30)  # Check every 30 seconds
    
    def _trigger_alarm(self, alarm: Alarm):
        """Trigger an alarm with Iron-Man style presentation"""
        self.current_alarm = alarm
        
        # Play alarm sound
        sound_path = alarm.sound_file
        if os.path.exists(sound_path):
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play(-1)  # Loop until stopped
        
        # Iron-Man style announcement
        announcement = f"Good morning, {get_title()}. It's time for {alarm.label}."
        print(f"🚨 IRON-MAN ALARM: {announcement}")
        
        # Wait for acknowledgment or snooze
        self._handle_alarm_response(alarm)
    
    def _handle_alarm_response(self, alarm: Alarm):
        """Handle user response to alarm (snooze/stop)"""
        # This would integrate with voice commands
        # For now, we'll auto-stop after 1 minute
        time.sleep(60)
        pygame.mixer.music.stop()
        
        if alarm.snooze_count < alarm.max_snoozes:
            # Snooze for 5 minutes
            snooze_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%H:%M")
            alarm.snooze_count += 1
            print(f"⏰ Snoozed for 5 minutes. {alarm.max_snoozes - alarm.snooze_count} snoozes remaining.")
        else:
            print("🔕 Maximum snoozes reached. Alarm dismissed.")
            alarm.enabled = False
        
        self.save_alarms()
    
    def snooze_alarm(self, minutes: int = 5) -> str:
        """Snooze current alarm"""
        if self.current_alarm:
            snooze_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%H:%M")
            self.current_alarm.snooze_count += 1
            self.add_alarm(snooze_time, f"Snoozed: {self.current_alarm.label}", self.current_alarm.sound_file)
            return f"Alarm snoozed for {minutes} minutes, {get_title()}."
        return "No active alarm to snooze."
    
    def dismiss_alarm(self) -> str:
        """Dismiss current alarm"""
        if self.current_alarm:
            pygame.mixer.music.stop()
            self.current_alarm = None
            return "Alarm dismissed, sir."
        return "No active alarm to dismiss."

# Global alarm system instance
alarm_system = IronManAlarmSystem()

# Voice command integration functions
def set_alarm_voice(time_str: str, label: str, recurring: bool = False, days: List[str] = None) -> str:
    """Set alarm via voice command"""
    return alarm_system.add_alarm(time_str, label, recurring=recurring, days=days)

def list_alarms_voice() -> str:
    """List all alarms via voice"""
    alarms = alarm_system.list_alarms()
    if not alarms:
        return "No alarms set, sir."
    
    response = "Here are your Iron-Man alarms:\n"
    for alarm in alarms:
        status = "Active" if alarm['enabled'] else "Disabled"
        recurring = "Recurring" if alarm['recurring'] else "One-time"
        response += f"- {alarm['time']} - {alarm['label']} ({status}, {recurring})\n"
    
    return response

def start_alarms_voice() -> str:
    """Start alarm system via voice"""
    return alarm_system.start_alarm_monitor()

def stop_alarms_voice() -> str:
    """Stop alarm system via voice"""
    return alarm_system.stop_alarm_monitor()

# Integration with main JARVIS system
def integrate_alarm_system():
    """Integrate the Iron-Man alarm system with JARVIS"""
    # Start the alarm monitoring
    alarm_system.start_alarm_monitor()
    
    # Add voice commands
    voice_commands = {
        "set alarm": set_alarm_voice,
        "list alarms": list_alarms_voice,
        "start alarms": start_alarms_voice,
        "stop alarms": stop_alarms_voice,
        "snooze alarm": alarm_system.snooze_alarm,
        "dismiss alarm": alarm_system.dismiss_alarm
    }
    
    return "Iron-Man alarm system integrated with JARVIS, sir."

# Initialize on import
if __name__ == "__main__":
    integrate_alarm_system()
    print("🚨 Iron-Man Alarm System Ready! 🚨")
