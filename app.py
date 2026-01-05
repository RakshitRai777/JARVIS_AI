import flet as ft
import threading
import time
import main

# ================= START BRAIN =================
def start_brain():
    if not main.BrainManager.is_running():
        threading.Thread(target=main.load_vosk, daemon=True).start()
        threading.Thread(target=main.listener, daemon=True).start()
        main.healing_arbiter.start()
        main.BrainManager.start(main.brain_loop)

start_brain()

# ================= UI =================
def app(page: ft.Page):
    page.title = "JARVIS"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    input_box = ft.TextField(
        hint_text="Message JARVIS...",
        expand=True,
        autofocus=True,
        on_submit=lambda e: send()
    )

    def user_bubble(text):
        return ft.Container(
            content=ft.Text(text),
            alignment=ft.alignment.center_right,
            bgcolor="#1f2937",
            padding=10,
            border_radius=10
        )

    def assistant_bubble():
        return ft.Container(
            content=ft.Text(""),
            alignment=ft.alignment.center_left,
            bgcolor="#0f172a",
            padding=10,
            border_radius=10
        )

    def send():
        text = input_box.value.strip()
        if not text:
            return
        chat.controls.append(user_bubble(text))
        main.command_queue.put(text.lower())
        input_box.value = ""
        page.update()

    def stream_listener():
        buffer = ""
        bubble = None

        while True:
            try:
                token = main.stream_queue.get(timeout=0.1)

                if token == "__END__":
                    buffer = ""
                    bubble = None
                    continue

                if not bubble:
                    bubble = assistant_bubble()
                    chat.controls.append(bubble)

                buffer += token
                bubble.content.value = buffer
                page.update()

            except:
                pass

            time.sleep(0.03)

    threading.Thread(target=stream_listener, daemon=True).start()

    page.add(
        chat,
        ft.Row([
            input_box,
            ft.IconButton(icon=ft.Icons.SEND, on_click=lambda e: send())
        ])
    )

ft.app(target=app)
