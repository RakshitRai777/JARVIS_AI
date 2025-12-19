import time
import random
from logger import debug

def human_pause():
    pause = random.uniform(0.3, 0.7)
    debug(f"Human pause: {pause:.2f}s")
    time.sleep(pause)
