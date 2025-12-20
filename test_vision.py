import os
import base64
import requests
import pyautogui
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def test_vision():
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY missing.")
        return

    raw_path = "test_screen.png"
    resized_path = "test_resized.png"
    
    try:
        print("📸 Capturing screen...")
        pyautogui.screenshot(raw_path)
        
        # Resize to stay under the 4MB limit
        img = Image.open(raw_path)
        img.thumbnail((1280, 720)) 
        img.save(resized_path, "PNG", optimize=True)

        with open(resized_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        # This is currently the ONLY model on Groq accepting the content array (images)
        MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze the screenshot and describe it for an AI assistant."},
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "temperature": 0.1
        }

        print(f"🧠 Processing with {MODEL}...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res = response.json()

        if 'choices' in res:
            print("\n" + "="*30)
            print("JARVIS VISION OUTPUT:")
            print("="*30)
            print(res['choices'][0]['message']['content'])
        else:
            print("❌ API Error:", res.get('error', {}).get('message', 'Unknown error'))

    except Exception as e:
        print(f"❌ Failure: {e}")
    finally:
        # Cleanup as requested in your preferences
        for p in [raw_path, resized_path]:
            if os.path.exists(p):
                os.remove(p)
                print(f"🧹 Cleaned up: {p}")

if __name__ == "__main__":
    test_vision()