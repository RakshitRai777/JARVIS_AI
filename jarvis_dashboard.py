
from flask import Flask, request, render_template_string, jsonify
import threading
import os
import asyncio
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from JarvisWithGroq import process_command

app = Flask(__name__)

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS Remote Dashboard</title>
    <style>
        body { font-family: Arial; background: #181c20; color: #fff; }
        .container { max-width: 500px; margin: 40px auto; background: #23272b; padding: 30px; border-radius: 10px; }
        h1 { text-align: center; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        button { background: #007bff; color: #fff; font-weight: bold; cursor: pointer; }
        button:hover { background: #0056b3; }
        #response { margin-top: 20px; background: #111; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>JARVIS Remote</h1>
        <form id="commandForm">
            <input type="text" id="command" placeholder="Type your command (e.g., play music, set alarm, open chrome)" required />
            <button type="submit">Send</button>
        </form>
        <div id="response"></div>
    </div>
    <script>
        document.getElementById('commandForm').onsubmit = async function(e) {
            e.preventDefault();
            const cmd = document.getElementById('command').value;
            const resDiv = document.getElementById('response');
            resDiv.innerText = 'Sending...';
            const resp = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            });
            const data = await resp.json();
            resDiv.innerText = data.response;
        };
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json()
    command = data.get('command', '')
    response = process_command(command)
    return jsonify({'response': response})

if __name__ == '__main__':
    # Run Flask in a separate thread if you want to keep JARVIS running in the main thread
    app.run(host='0.0.0.0', port=5000, debug=True)
