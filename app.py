from flask import Flask, render_template, request, jsonify, session
import os
import sys
import json
import asyncio
import threading
from datetime import datetime
import JarvisWithGroq as jarvis

app = Flask(__name__)
app.secret_key = 'jarvis-scifi-secret-key-2024'

# Global variables for JARVIS state
current_status = "Idle"
conversation_history = []
system_stats = {
    "cpu": 0,
    "memory": 0,
    "disk": 0
}

@app.route('/')
def dashboard():
    return render_template('cortana.html')

@app.route('/api/status')
def get_status():
    """Get current JARVIS status"""
    return jsonify({
        "status": current_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/system-stats')
def get_system_stats():
    """Get system statistics"""
    try:
        stats = jarvis.get_system_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversation', methods=['POST'])
def process_command():
    """Process voice/text commands"""
    try:
        data = request.json
        command = data.get('command', '')
        
        if command:
            try:
                response = jarvis.process_command(command.lower())
                # Trigger voice response asynchronously
                import threading
                threading.Thread(target=jarvis.speak_threaded, args=(response,)).start()
            except Exception as e:
                # Log the error and return a friendly message
                print(f"Error processing command: {e}")
                response = "Sorry, I encountered an error processing your request."
            
            conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user": command,
                "jarvis": response
            })
            
            # Keep only last 50 conversations
            if len(conversation_history) > 50:
                conversation_history.pop(0)
                
            return jsonify({
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
        
        return jsonify({"error": "No command provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversation/history')
def get_conversation_history():
    """Get conversation history"""
    return jsonify(conversation_history)

@app.route('/api/alarms', methods=['GET', 'POST', 'DELETE'])
def manage_alarms():
    """Manage alarms"""
    if request.method == 'GET':
        return jsonify(jarvis.alarms)
    
    elif request.method == 'POST':
        data = request.json
        alarm_time = data.get('time')
        if alarm_time:
            jarvis.set_alarm(alarm_time)
            return jsonify({"message": f"Alarm set for {alarm_time}"})
        return jsonify({"error": "No time provided"}), 400
    
    elif request.method == 'DELETE':
        data = request.json
        alarm_time = data.get('time')
        if alarm_time and alarm_time in jarvis.alarms:
            jarvis.alarms.remove(alarm_time)
            return jsonify({"message": f"Alarm {alarm_time} removed"})
        return jsonify({"error": "Alarm not found"}), 404

@app.route('/api/calendar/events')
def get_calendar_events():
    """Get calendar events"""
    try:
        events = jarvis.list_calendar_events()
        return jsonify({"events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather/<city>')
def get_weather(city):
    """Get weather information"""
    try:
        weather = jarvis.get_weather(city)
        return jsonify({"weather": weather})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/music/play', methods=['POST'])
def play_music():
    """Play music"""
    try:
        data = request.json
        song = data.get('song')
        if song:
            # Run async function in thread
            def run_play():
                asyncio.run(jarvis.play_youtube_song(song))
            
            thread = threading.Thread(target=run_play)
            thread.start()
            
            return jsonify({"message": f"Playing {song}"})
        return jsonify({"error": "No song provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/music/control', methods=['POST'])
def control_music():
    """Control music playback"""
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'pause':
            response = jarvis.pause_song()
        elif action == 'resume':
            response = jarvis.resume_song()
        elif action == 'stop':
            response = jarvis.stop_song()
        else:
            return jsonify({"error": "Invalid action"}), 400
            
        return jsonify({"message": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/volume/<action>')
def control_volume(action):
    """Control system volume"""
    try:
        if action == 'mute':
            jarvis.mute_system_volume()
            return jsonify({"message": "Volume muted"})
        elif action == 'unmute':
            jarvis.unmute_system_volume()
            return jsonify({"message": "Volume unmuted"})
        elif action == 'up':
            # Increase volume (mock implementation)
            return jsonify({"message": "Volume increased"})
        elif action == 'down':
            # Decrease volume (mock implementation)
            return jsonify({"message": "Volume decreased"})
        return jsonify({"error": "Invalid action"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
