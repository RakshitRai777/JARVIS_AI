from datetime import datetime
import threading

# -------------------------
# GLOBAL LOGGER SETTINGS
# -------------------------

LOG_ENABLED = True          # Turn logging ON/OFF globally
LOG_LEVEL = "INFO"          # INFO | WARN | ERROR | DEBUG
SHOW_THREAD = False         # Show thread name if needed

LEVEL_PRIORITY = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "ERROR": 40
}

_lock = threading.Lock()


# -------------------------
# CORE LOGGER FUNCTION
# -------------------------

def log(message: str, level: str = "INFO"):
    """
    Central logging function for JARVIS / FRIDAY.
    Usage:
        log("System online")
        log("Wake word detected", "INFO")
        log("Speech interrupted", "WARN")
        log("Microphone failure", "ERROR")
        log("Debug details", "DEBUG")
    """

    if not LOG_ENABLED:
        return

    level = level.upper()

    if LEVEL_PRIORITY.get(level, 0) < LEVEL_PRIORITY.get(LOG_LEVEL, 0):
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    thread_name = threading.current_thread().name

    prefix = f"[{timestamp}] [{level}]"

    if SHOW_THREAD:
        prefix += f" [{thread_name}]"

    with _lock:
        print(f"{prefix} {message}", flush=True)


# -------------------------
# CONVENIENCE WRAPPERS
# -------------------------

def info(message: str):
    log(message, "INFO")


def warn(message: str):
    log(message, "WARN")


def error(message: str):
    log(message, "ERROR")


def debug(message: str):
    log(message, "DEBUG")


# -------------------------
# RUNTIME CONTROLS
# -------------------------

def enable():
    global LOG_ENABLED
    LOG_ENABLED = True


def disable():
    global LOG_ENABLED
    LOG_ENABLED = False


def set_level(level: str):
    """
    Change log level at runtime.
    Example:
        set_level("DEBUG")
    """
    global LOG_LEVEL
    LOG_LEVEL = level.upper()
