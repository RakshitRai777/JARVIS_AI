import os
import requests
from dotenv import load_dotenv
from config import GROQ_MODEL

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

class GroqAI:
    def ask(self, prompt):
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        headers = {"Authorization": f"Bearer {API_KEY}"}
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers
        )
        return r.json()["choices"][0]["message"]["content"]
