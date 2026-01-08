import unittest
from unittest.mock import patch
import main


class TestConversationContinuity(unittest.TestCase):

    def fake_groq(self, messages):
        full_context = " ".join(m["content"] for m in messages).lower()

        if "president of india" in full_context:
            return "The President of India is Droupadi Murmu."
        if "where is she from" in full_context:
            return "She is from Odisha."
        return "OK"

    @patch("main.groq")
    def test_follow_up_question(self, mock_groq):
        mock_groq.side_effect = self.fake_groq

        # First turn
        r1 = main.process_text_for_test("Who is the president of India?")
        self.assertIn("Droupadi Murmu", r1)

        # Follow-up turn
        r2 = main.process_text_for_test("Where is she from?")
        self.assertIn("Odisha", r2)

        # Verify continuity via trace
        history = " ".join(m["content"] for m in main.conversation_trace)
        self.assertIn("Droupadi Murmu", history)
        self.assertIn("Odisha", history)
