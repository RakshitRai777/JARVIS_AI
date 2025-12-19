import os
import requests
from dotenv import load_dotenv
from config import GROQ_MODEL
from logger import info, error, debug

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    error("GROQ_API_KEY not found in environment")

class GroqAI:
    def ask(self, prompt: str) -> str | None:
        debug("Sending request to Groq API")

        url = "https://api.groq.com/openai/v1/chat/completions"

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are FRIDAY, a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            data = response.json()

            if "choices" not in data:
                error(f"Groq API returned unexpected response: {data}")
                return None

            content = data["choices"][0]["message"]["content"]
            info("Groq API response received")
            return content

        except Exception as e:
            error(f"Groq API request failed: {e}")
            return None
