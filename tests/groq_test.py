import sys
import os
import requests

# Add project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {Config.GROQ_API_KEY}"},
    json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 50
    },
    timeout=30
)

print("STATUS:", r.status_code)
print("RESPONSE:", r.text)
