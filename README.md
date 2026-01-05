# JARVIS_AI 🧠✨  
### A Self-Healing, Multimodal AI Assistant with Memory, Voice, Vision & Streaming UI

JARVIS_AI is a **modular, autonomous AI assistant** inspired by Iron Man’s JARVIS.  
It combines **voice interaction, vision reasoning, long-term memory, self-healing intelligence, and a ChatGPT-style streaming UI** into a single, robust system.

Unlike typical AI demos, this project focuses on **engineering reliability, autonomy, and real-world stability**.

---

## 🌟 Why JARVIS_AI?

Most AI assistants are:
- Simple scripts
- Fragile over time
- Hard to debug
- Not designed for long-running execution

**JARVIS_AI is built as a system, not a script.**

It features:
- 🧠 A single authoritative brain loop  
- 🧬 Autonomous self-healing logic  
- 🧵 Thread-safe concurrency  
- 🧪 Built-in diagnostics  
- 🔁 Streaming, human-like interaction  

---

## 🚀 Key Features

### 🧠 Core Intelligence
- LLM-powered reasoning using **Groq (LLaMA-3.3-70B)**
- Context-aware responses
- Memory-augmented prompting
- Graceful degradation on failures

### 🎙️ Voice Interaction
- Wake-word activation (“Jarvis”)
- Continuous **offline** speech recognition (Vosk)
- Natural, non-overlapping text-to-speech (Edge-TTS)
- Fully hands-free operation

### 👁️ Vision Reasoning
- Screen capture and OCR-based perception
- Structured visual understanding
- LLM-powered interpretation of on-screen content

### 💬 ChatGPT-Style UI
- Token-by-token streaming responses
- Text + voice synchronized output
- Clean, modern interface (Flet)

### 🧬 Self-Healing System
- Continuous monitoring (CPU, RAM, queues)
- AI-driven diagnostics and recovery decisions
- Rate-limited restarts to prevent instability
- Experience-based confidence learning

### 🧠 Long-Term Memory
- Persistent memory across restarts
- Relevance-based recall
- Safe memory size limits
- Manual inspection and clearing

### 🧪 Reliability & Safety
- Automated system self-test (`test_jarvis.py`)
- Thread-safe architecture
- Queue backpressure protection
- Graceful failure handling

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Groq API** — LLaMA-3.3-70B
- **Vosk** — offline speech recognition
- **Edge-TTS** — natural speech synthesis
- **Flet** — ChatGPT-style UI
- **Tesseract OCR** — vision perception
- **SoundDevice / SimpleAudio** — audio I/O
- **Threading & AsyncIO** — concurrency control

---

## 📦 Installation

```bash
git clone https://github.com/RakshitRai777/JARVIS_AI.git
cd JARVIS_AI
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
```

---

## ▶️ Usage

Run the assistant:

```bash
python app.py
```

Say **“Jarvis”** to activate voice mode.

### Example Commands
- `what time is it`
- `what is on my screen`
- `remember that my name is Rakshit`
- `how many memories do you have`
- `clear your memory`

Responses are streamed in real time with synchronized voice output.

---

## 🧪 System Health Check

Run the built-in diagnostic test:

```bash
python test_jarvis.py
```

If successful, JARVIS reports:

> **Everything is working properly without any type of errors.**

---

## 🛠️ Troubleshooting

If something isn’t working:
- Ensure all dependencies are installed
- Verify the Groq API key in `.env`
- Check microphone and speaker access
- Run `python test_jarvis.py` for diagnostics

---

## ⚠️ Limitations

- Vision is OCR-based (not object detection)
- Requires internet access for LLM reasoning
- Not designed as a commercial voice assistant

---

## 🗺️ Roadmap

Planned improvements:
- Vision summarization before speech
- “Thinking…” indicator in UI
- User profile and preference modeling
- System health dashboard
- Embedding-based memory retrieval

---

## 📜 License

Licensed under the **MIT License** — see the `LICENSE` file for details.

---

## 💡 Inspiration

Inspired by cinematic AI systems like JARVIS, this project explores how **autonomous, stable, and human-like AI assistants** can be engineered using modern tools and sound system design.

---
