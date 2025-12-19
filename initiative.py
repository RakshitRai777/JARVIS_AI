import threading
from logger import info, debug

INTERRUPT_EVENT = threading.Event()

def trigger_interrupt():
    INTERRUPT_EVENT.set()
    info("Interrupt triggered")

def clear_interrupt():
    INTERRUPT_EVENT.clear()
    debug("Interrupt cleared")

def is_interrupted():
    state = INTERRUPT_EVENT.is_set()
    debug(f"Interrupt state checked: {state}")
    return state
