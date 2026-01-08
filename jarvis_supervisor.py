# jarvis_supervisor.py
"""
JARVIS Supervisor
-----------------
• Owns core lifecycle
• Handles crashes & restarts
• Prevents infinite crash loops
• Graceful shutdown with hard-kill fallback
• 24/7 safe
"""

import subprocess
import sys
import io
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Optional

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CORE = "main.py"
RESTART_CODE = 42

RESTART_DELAY = 1.5          # seconds
MAX_FAST_RESTARTS = 5
FAST_RESTART_WINDOW = 20     # seconds
KILL_TIMEOUT = 5             # seconds

_restart_times = []
_shutdown = False
_current_proc = None


# ===================== SIGNAL HANDLING =====================

def handle_signal(sig, frame):
    global _shutdown
    print("\n🛑 Supervisor shutting down...")
    _shutdown = True

    if _current_proc and _current_proc.poll() is None:
        try:
            _current_proc.terminate()
        except Exception:
            pass


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


# ===================== RESTART THROTTLE =====================

def should_throttle_restart():
    now = time.time()
    _restart_times.append(now)

    while _restart_times and now - _restart_times[0] > FAST_RESTART_WINDOW:
        _restart_times.pop(0)

    return len(_restart_times) >= MAX_FAST_RESTARTS


# ===================== CORE LAUNCH =====================

def run_core():
    global _current_proc
    print("🚀 Starting JARVIS core...")

    _current_proc = subprocess.Popen(
        [sys.executable, CORE],
        stdin=None,              # 🔥 avoid pipe deadlocks
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    return _current_proc


# ===================== MAIN LOOP =====================

def main():
    global _shutdown, _current_proc

    while not _shutdown:
        proc = run_core()

        try:
            code = proc.wait()
        except KeyboardInterrupt:
            _shutdown = True
            break

        if _shutdown:
            break

        if code == 0:
            print("✅ Core shut down cleanly.")
            break

        if code == RESTART_CODE:
            print("🔁 Core requested restart.")
        else:
            print(f"❌ Core crashed (exit code {code}).")

        if should_throttle_restart():
            print("🧯 Too many crashes. Cooling down...")
            time.sleep(10)
            _restart_times.clear()
        else:
            time.sleep(RESTART_DELAY)

    # ===================== CLEAN EXIT =====================

    if _current_proc and _current_proc.poll() is None:
        print("🧹 Terminating core...")
        _current_proc.terminate()
        try:
            _current_proc.wait(timeout=KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            print("🔥 Core unresponsive, killing...")
            _current_proc.kill()

    _restart_times.clear()
    print("👋 Supervisor exiting.")


if __name__ == "__main__":
    main()
