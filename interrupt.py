import threading

INTERRUPT_EVENT = threading.Event()

def trigger_interrupt():
    INTERRUPT_EVENT.set()

def clear_interrupt():
    INTERRUPT_EVENT.clear()

def is_interrupted():
    return INTERRUPT_EVENT.is_set()
