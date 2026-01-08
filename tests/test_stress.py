import time
import unittest
from unittest.mock import patch

import main
from brain_manager import BrainManager


class TestJarvisStress(unittest.TestCase):

    @patch("main.speak", lambda *_: None)
    @patch("main.groq", lambda *_: "OK")
    def test_high_frequency_input(self):
        """
        Rapid-fire commands to test stability.
        """

        BrainManager.start(main.brain_loop)
        time.sleep(0.5)

        # Wake JARVIS
        main.command_queue.put(("voice", "jarvis"))
        time.sleep(0.2)

        start = time.time()

        for i in range(100):
            main.command_queue.put(("voice", f"what is test number {i}?"))

        time.sleep(2)

        duration = time.time() - start

        self.assertLess(duration, 5, "Stress test took too long")
        self.assertTrue(BrainManager.is_running(), "Brain loop crashed")

        BrainManager._running = False
