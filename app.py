import flet as ft
import threading
import queue
import time
import main
import os

# ================= GLOBAL STATE =================
ui_alive = True

# ================= START CORE (THREADED) =================

def ensure_core_running():
    """Starts the JARVIS brain in a background thread so the UI can load."""
    if not main.BrainManager.is_running():
        print("🧠 Starting JARVIS Brain in background...")
        
        # 1. Force main.py to recognize UI mode
        main.ENABLE_UI = True
        
        # 2. Start the brain loop in a separate thread
        # We use a lambda to start the arbiter which then runs the brain_loop
        core_thread = threading.Thread(
            target=lambda: main.healing_arbiter.start(main.command_queue.qsize, main.brain_loop),
            daemon=True,
            name="JarvisCoreThread"
        )
        core_thread.start()
        
        # 3. Mark the Manager as started
        main.BrainManager.start(main.brain_loop)
        print("✅ Core Thread spawned. Launching UI...")

# Initialize core before the UI blocks the main thread
ensure_core_running()

# ================= UI APP =================

def app(page: ft.Page):
    global ui_alive
    page.title = "JARVIS"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.bgcolor = "#020617"
    page.window_min_width = 450
    page.window_min_height = 650

    # ================= HEADER =================
    header = ft.Row(
        [
            ft.Text("JARVIS", size=24, weight="bold", color="#38bdf8"),
            ft.Container(
                content=ft.Text("ONLINE", size=10, weight="bold", color="#020617"),
                bgcolor="#38bdf8",
                padding=5,
                border_radius=5
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # ================= CHAT VIEW =================
    chat = ft.ListView(
        expand=True,
        spacing=12,
        auto_scroll=True,
        padding=10
    )

    # ================= INPUT =================
    input_box = ft.TextField(
        hint_text="Type a command...",
        expand=True,
        autofocus=True,
        border_radius=15,
        filled=True,
        bgcolor="#1e293b",
        border_color="#334155",
        on_submit=lambda _: send()
    )

    # ================= BUBBLE GENERATORS =================
    def user_bubble(text: str):
        return ft.Container(
            content=ft.Text(text, color="white"),
            alignment=ft.alignment.center_right,
            bgcolor="#334155",
            padding=12,
            border_radius=ft.border_radius.only(top_left=15, top_right=5, bottom_left=15, bottom_right=15),
            margin=ft.margin.only(left=50)
        )

    def assistant_bubble():
        return ft.Container(
            content=ft.Text("", color="#38bdf8"),
            alignment=ft.alignment.center_left,
            bgcolor="#0f172a",
            border=ft.border.all(1, "#38bdf8"),
            padding=12,
            border_radius=ft.border_radius.only(top_left=5, top_right=15, bottom_left=15, bottom_right=15),
            margin=ft.margin.only(right=50)
        )

    # ================= SEND LOGIC =================
    def send(e=None):
        text = input_box.value.strip()
        if not text:
            return

        # Add user message to UI
        chat.controls.append(user_bubble(text))
        
        # Send to main.py command queue
        main.command_queue.put(("ui", text))
        
        input_box.value = ""
        page.update()

    # ================= STREAM LISTENER =================
    def stream_listener():
        """Listens to main.stream_queue and updates the UI in real-time."""
        buffer = ""
        bubble = None

        while ui_alive:
            try:
                # Poll the queue from main.py
                token = main.stream_queue.get(timeout=0.1)

                if token == "__END__":
                    buffer = ""
                    bubble = None
                    page.update()
                    continue

                if bubble is None:
                    bubble = assistant_bubble()
                    chat.controls.append(bubble)
                    page.update()

                buffer += token
                bubble.content.value = buffer
                page.update()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ UI Stream Error: {e}")
            
            time.sleep(0.01)

    # Start the UI listener thread
    threading.Thread(target=stream_listener, daemon=True).start()

    # ================= LAYOUT =================
    page.add(
        header,
        ft.Divider(height=1, color="#1e293b"),
        chat,
        ft.Container(
            padding=10,
            content=ft.Row(
                [
                    input_box,
                    ft.IconButton(
                        icon=ft.Icons.SEND_ROUNDED,
                        icon_color="#38bdf8",
                        on_click=send
                    )
                ]
            )
        )
    )

    # Handle window close
    def on_close(e):
        global ui_alive
        ui_alive = False
        print("Shutting down UI...")

    page.on_close = on_close

# ================= RUN =================
if __name__ == "__main__":
    ft.app(target=app)