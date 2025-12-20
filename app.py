import gradio as gr
import main
import vision_module
import threading
import time

# =====================================================
# GEMINI + SCI-FI JARVIS CSS + ANIMATIONS
# =====================================================
custom_css = """
body {
    background: radial-gradient(circle at top, #0b1220, #05070d);
    color: #e6e6e6;
    font-family: "Google Sans", Inter, system-ui;
}

footer, header { display: none !important; }
.gradio-container { background: transparent !important; }

#jarvis-shell {
    max-width: 860px;
    margin: auto;
    padding-top: 20px;
    position: relative;
}

/* Title */
#jarvis-title {
    text-align: center;
    font-size: 26px;
    letter-spacing: 6px;
    color: #8ab4f8;
    text-shadow: 0 0 18px rgba(138,180,248,0.45);
    margin-bottom: 10px;
}

/* Floating hologram orb */
#jarvis-orb {
    position: absolute;
    top: -20px;
    right: -20px;
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: radial-gradient(circle, #8ab4f8, #1a73e8);
    box-shadow: 0 0 30px rgba(138,180,248,0.7);
    animation: float 4s ease-in-out infinite;
}

@keyframes float {
    0% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
    100% { transform: translateY(0); }
}

/* Chat panel */
.gr-chatbot {
    background: rgba(15, 20, 35, 0.65) !important;
    border-radius: 18px;
    padding: 12px;
    border: 1px solid rgba(138,180,248,0.15);
    box-shadow: 0 0 30px rgba(138,180,248,0.08);
}

/* Fade-in messages */
.gr-chatbot .message {
    animation: fadeIn 0.35s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

/* User / Bot */
.gr-chatbot .message.user {
    background: linear-gradient(135deg, #1a2338, #111827) !important;
    border-radius: 16px;
    padding: 14px;
    margin: 10px 0;
    text-align: right;
}

.gr-chatbot .message.bot {
    background: linear-gradient(135deg, #0f1a2b, #0b1220) !important;
    border-radius: 16px;
    padding: 14px;
    margin: 10px 0;
    border-left: 3px solid #8ab4f8;
}

/* Remove icons */
.gr-chatbot .message-buttons { display: none !important; }

/* Thinking dots */
.thinking::after {
    content: " .";
    animation: dots 1.5s steps(5, end) infinite;
}

@keyframes dots {
    0%, 20% { content: " ."; }
    40% { content: " .."; }
    60% { content: " ..."; }
    80%, 100% { content: " ...."; }
}

/* Voice waveform animation */
.wave {
    display: flex;
    gap: 4px;
    margin-top: 6px;
}

.wave span {
    width: 4px;
    height: 16px;
    background: #8ab4f8;
    animation: wave 1s infinite ease-in-out;
}

.wave span:nth-child(2) { animation-delay: 0.1s; }
.wave span:nth-child(3) { animation-delay: 0.2s; }
.wave span:nth-child(4) { animation-delay: 0.3s; }

@keyframes wave {
    0%, 100% { height: 8px; }
    50% { height: 20px; }
}

/* Input */
textarea {
    background: rgba(15,20,35,0.85) !important;
    color: #fff !important;
    border-radius: 16px !important;
    border: 1px solid rgba(138,180,248,0.25) !important;
    padding: 14px !important;
}

textarea::placeholder { color: #9aa0a6; }

button {
    background: linear-gradient(135deg, #8ab4f8, #5f9cff) !important;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 600;
    color: #0b1220 !important;
}
"""

# =====================================================
# Chat logic with THINKING + SPEAKING FX
# =====================================================
def jarvis_chat(message, history):
    if not message.strip():
        return history

    history.append((message, "<span class='thinking'>Thinking</span>"))
    yield history

    time.sleep(0.6)

    if any(w in message.lower() for w in ["look", "screen", "scan"]):
        response = vision_module.get_vision_analysis(
            message, main.session, main.GROQ_API_KEY
        )
    else:
        response = main.get_groq_response(message)

    # Speak + waveform
    main.speak(response)
    response_html = (
        response +
        "<div class='wave'><span></span><span></span><span></span><span></span></div>"
    )

    history[-1] = (message, response_html)
    yield history


# =====================================================
# UI
# =====================================================
with gr.Blocks(title="J.A.R.V.I.S", css=custom_css) as demo:
    gr.Markdown("<div id='jarvis-title'>J.A.R.V.I.S</div>")

    with gr.Column(elem_id="jarvis-shell"):
        gr.HTML("<div id='jarvis-orb'></div>")
        chatbot = gr.Chatbot(height=520, show_label=False)

        with gr.Row():
            msg = gr.Textbox(placeholder="Ask J.A.R.V.I.S…", container=False, scale=8)
            send = gr.Button("➤", scale=1)

        send.click(jarvis_chat, [msg, chatbot], chatbot)
        msg.submit(jarvis_chat, [msg, chatbot], chatbot)
        send.click(lambda: "", None, msg)
        msg.submit(lambda: "", None, msg)


# =====================================================
# Background systems
# =====================================================
if __name__ == "__main__":
    threading.Thread(target=main.load_vosk, daemon=True).start()
    threading.Thread(target=main.background_listener, daemon=True).start()
    demo.launch()
