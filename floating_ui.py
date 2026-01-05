import flet as ft
import main

def floating(page: ft.Page):
    page.window_width = 60
    page.window_height = 60
    page.window_always_on_top = True

    page.add(
        ft.GestureDetector(
            on_tap=lambda e: main.command_queue.put("jarvis"),
            content=ft.Container(
                width=50, height=50, bgcolor="blue",
                content=ft.Text("🎙️", size=24),
                alignment=ft.alignment.center
            )
        )
    )

ft.app(target=floating)
