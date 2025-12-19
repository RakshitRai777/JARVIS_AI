import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqAI:
    def ask(self, prompt):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are FRIDAY, a calm, intelligent, human-like male AI. "
                        "Adapt emotionally and respond naturally."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.45,
            "max_tokens": 400
        }

        r = requests.post(
            URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=payload,
            timeout=15
        )
        return r.json()["choices"][0]["message"]["content"].strip()
