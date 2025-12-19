import gradio as gr
import threading
import time

from groq_ai import GroqAI
from tts_engine import speak
from memory import get_short_context, get_long_facts
from awareness import update_activity

ai = GroqAI()

STATUS = "Idle"

def ask_jarvis(text):
    global STATUS
    update_activity()
    STATUS = "Thinking"

    if not text.strip():
        return "⚠️ Please enter a command."

    response = ai.ask(text)

    STATUS = "Speaking"
    threading.Thread(target=speak, args=(response,), daemon=True).start()

    STATUS = "Idle"
    return response

def system_status():
    return STATUS

with gr.Blocks(theme=gr.themes.Base(), css="""
body {
    background-color: #0b0f1a;
}
.gr-button {
    background: linear-gradient(90deg,#00f5ff,#0066ff);
    color: black;
    font-weight: bold;
}
""") as app:

    gr.Markdown("""
    # 🧠 **FRIDAY**
    ### *Futuristic AI Assistant Interface*
    """)

    with gr.Row():
        input_box = gr.Textbox(
            label="Command",
            placeholder="Ask FRIDAY...",
            scale=4
        )
        ask_btn = gr.Button("EXECUTE", scale=1)

    output_box = gr.Textbox(
        label="FRIDAY Response",
        lines=6
    )

    with gr.Row():
        status_box = gr.Textbox(
            label="System Status",
            value="Idle",
            interactive=False
        )

    ask_btn.click(
        ask_jarvis,
        inputs=input_box,
        outputs=output_box
    )

    gr.Markdown("### 🧠 Memory Snapshot")
    gr.Textbox(value=get_short_context(), label="Recent Context")
    gr.Textbox(value=get_long_facts(), label="Long-Term Memory")

    gr.Markdown("### ⚙️ Live Status")
    gr.Button("Refresh Status").click(
        system_status,
        outputs=status_box
    )

app.launch()
