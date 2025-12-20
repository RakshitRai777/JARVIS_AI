import gradio as gr
import main
import vision_module

# Add this global or in a state to manage the mic
def handle_input(text, audio, input_mode):
    # If the user is in Mic mode, we process the audio
    if input_mode == "Microphone" and audio is not None:
        # Here you would call your Vosk/Speech logic
        # For now, let's assume it transcribes to text
        return f"JARVIS heard you via Mic: {audio}"
    
    # Text mode logic
    if any(w in text.lower() for w in ["look", "screen", "see"]):
        return vision_module.get_vision_analysis(text, main.session, main.GROQ_API_KEY)
    
    return main.get_groq_response(text)

with gr.Blocks() as demo:
    gr.Markdown("# 🎙️ J.A.R.V.I.S. Control Console")
    
    with gr.Row():
        with gr.Column(scale=2):
            # THE TOGGLE: Switch between Text and Mic
            input_mode = gr.Radio(
                ["Text", "Microphone"], 
                label="Input Mode", 
                value="Text"
            )
            
            # THE WAVEFORM: This shows the live bars when recording
            mic_input = gr.Audio(
                sources=["microphone"], 
                type="filepath", 
                label="Live Voice Command",
                visible=False,
                streaming=True # This enables the live waveform
            )
            
            text_input = gr.Textbox(label="Type to JARVIS", visible=True)
            
            # Logic to swap visibility based on toggle
            def toggle_inputs(mode):
                if mode == "Microphone":
                    return gr.update(visible=False), gr.update(visible=True)
                return gr.update(visible=True), gr.update(visible=False)

            input_mode.change(toggle_inputs, inputs=input_mode, outputs=[text_input, mic_input])
            
            chatbot = gr.Chatbot(label="Conversation History")
            submit_btn = gr.Button("Execute Command")
            
            submit_btn.click(
                fn=handle_input, 
                inputs=[text_input, mic_input, input_mode], 
                outputs=chatbot
            )

        with gr.Column(scale=1):
            gr.Label("System Status: ONLINE")
            last_scan = gr.Image(label="Last Screen Capture", value="temp_resized.png")
            wipe_btn = gr.Button("Clear Session History", variant="danger")
            wipe_btn.click(fn=main.wipe_system_memory, outputs=None)

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())