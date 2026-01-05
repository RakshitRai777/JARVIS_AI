import threading
import time

class BrainManager:
    _brain_thread = None
    _lock = threading.Lock()
    _running = False

    @classmethod
    def start(cls, brain_loop):
        with cls._lock:
            if cls._running:
                return
            cls._running = True
            cls._brain_thread = threading.Thread(
                target=brain_loop, daemon=True
            )
            cls._brain_thread.start()

    @classmethod
    def restart(cls, brain_loop):
        with cls._lock:
            cls._running = False
            time.sleep(0.5)
            cls.start(brain_loop)

    @classmethod
    def is_running(cls):
        return cls._running
