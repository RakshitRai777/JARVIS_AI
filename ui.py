import gradio as gr
import threading

from groq_ai import GroqAI
from tts_engine import speak
from memory import get_short_context, get_long_facts
from awareness import update_activity
from logger import info

ai = GroqAI()
STATUS = "Idle"

def ask_jarvis(text):
    global STATUS
    update_activity()

    if not text.strip():
        return "⚠️ Please enter a command."

    info(f"UI input received: {text}")
    STATUS = "Thinking"

    response = ai.ask(text)

    STATUS = "Speaking"
    threading.Thread(target=speak, args=(response,), daemon=True).start()

    STATUS = "Idle"
    return response

def system_status():
    return STATUS

with gr.Blocks(theme=gr.themes.Base()) as app:
    gr.Markdown("# 🧠 FRIDAY")

    input_box = gr.Textbox(placeholder="Ask FRIDAY...")
    output_box = gr.Textbox(lines=6)

    gr.Button("EXECUTE").click(ask_jarvis, input_box, output_box)

    gr.Markdown("### Memory")
    gr.Textbox(value=get_short_context())
    gr.Textbox(value=get_long_facts())

app.launch()
