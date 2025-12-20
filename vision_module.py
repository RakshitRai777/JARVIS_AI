import pyautogui
import base64
import os
import requests
from PIL import Image

def get_vision_analysis(user_query, session, api_key):
    raw_path = "temp_screen.png"
    resized_path = "temp_resized.png"
    
    try:
        # 1. Capture and Resize
        pyautogui.screenshot(raw_path)
        img = Image.open(raw_path)
        img.thumbnail((1280, 720)) 
        img.save(resized_path, "PNG", optimize=True)

        with open(resized_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        # 2. Use the verified working Model ID
        MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Sir, I have analyzed the screen for you. Regarding your request '{user_query}':"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            "temperature": 0.2
        }

        response = session.post(url, headers=headers, json=payload, timeout=30)
        res = response.json()

        if 'choices' in res:
            return res['choices'][0]['message']['content']
        else:
            return f"I encountered an error with the vision server: {res.get('error', {}).get('message')}"

    except Exception as e:
        return f"Visual sensors are experiencing interference: {e}"
    finally:
        # Manual history/temp wipe as per user instructions
        for p in [raw_path, resized_path]:
            if os.path.exists(p):
                os.remove(p)