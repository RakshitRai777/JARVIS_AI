import unittest
from unittest.mock import patch, MagicMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import JarvisWithGroq as jarvis

class TestJarvis(unittest.TestCase):

    def test_translate_text(self):
        text = "Hello"
        translated = jarvis.translate_text(text, "fr")
        self.assertIsInstance(translated, str)

    def test_get_title(self):
        title = jarvis.get_title()
        self.assertIn(title, ["Sir", "Boss", "Master"])

    def test_set_personality(self):
        response = jarvis.set_personality("friendly")
        self.assertEqual(response, "Personality mode changed to friendly.")
        self.assertEqual(jarvis.personality_mode, "friendly")

    @patch('JarvisWithGroq.requests.post')
    def test_get_groq_response(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        response = jarvis.get_groq_response("Hello")
        self.assertEqual(response, "Test response")

    def test_mute_unmute_system_volume(self):
        try:
            jarvis.mute_system_volume()
            jarvis.unmute_system_volume()
        except Exception as e:
            self.fail(f"mute/unmute_system_volume raised Exception unexpectedly: {e}")

    def test_add_list_delete_calendar_event(self):
        # These tests require valid Google credentials and token.pickle
        # Here we just check if functions exist and callable
        self.assertTrue(callable(jarvis.add_calendar_event))
        self.assertTrue(callable(jarvis.list_calendar_events))
        self.assertTrue(callable(jarvis.delete_calendar_event))

    @patch('JarvisWithGroq.speak_threaded')
    def test_play_youtube_song(self, mock_speak):
        # Test async function by running event loop
        async def run_play():
            await jarvis.play_youtube_song("test song")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_play())
        mock_speak.assert_called()

    def test_process_command(self):
        response = jarvis.process_command("change personality to happy")
        self.assertIn("Personality changed to happy", response)

    def test_alarm_functions(self):
        jarvis.set_alarm("23:59")
        self.assertIn("23:59", jarvis.alarms)

if __name__ == '__main__':
    unittest.main()
