import threading
import time
import traceback


class BrainManager:
    _brain_thread = None
    _lock = threading.Lock()
    _running = False
    _stop_event = threading.Event()

    @classmethod
    def _run_wrapper(cls, brain_loop):
        """
        Wraps brain_loop to detect crashes and reset state cleanly.
        """
        try:
            brain_loop()
        except Exception:
            print("❌ Brain crashed:")
            traceback.print_exc()
        finally:
            # Brain exited unexpectedly or normally
            with cls._lock:
                cls._running = False
                cls._stop_event.clear()
                cls._brain_thread = None
            print("⚠️ Brain thread exited")

    @classmethod
    def start(cls, brain_loop):
        with cls._lock:
            # If thread exists and is alive, do nothing
            if cls._brain_thread and cls._brain_thread.is_alive():
                return

            cls._stop_event.clear()
            cls._running = True

            cls._brain_thread = threading.Thread(
                target=cls._run_wrapper,
                args=(brain_loop,),
                daemon=True
            )
            cls._brain_thread.start()
            print("🧠 Brain started")

    @classmethod
    def restart(cls, brain_loop):
        with cls._lock:
            print("♻️ Restarting brain")
            cls._stop_event.set()
            cls._running = False

        # Give old thread time to exit
        time.sleep(0.5)
        cls.start(brain_loop)

    @classmethod
    def is_running(cls):
        return (
            cls._brain_thread is not None
            and cls._brain_thread.is_alive()
            and cls._running
        )

    @classmethod
    def should_stop(cls):
        """
        Optional: brain_loop can check this for graceful exits.
        """
        return cls._stop_event.is_set()
