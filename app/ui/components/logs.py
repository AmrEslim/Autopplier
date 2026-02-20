import flet as ft
from datetime import datetime


class LogComponent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self._mounted = False

        self.log_view = ft.ListView(
            expand=True,
            spacing=2,
            auto_scroll=True,
        )

        clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip="Clear logs",
            on_click=lambda e: self.clear(),
        )

        self.controls = [
            ft.Row([
                ft.Text("Application Logs", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                clear_btn,
            ]),
            ft.Container(
                content=self.log_view,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                expand=True,
            )
        ]

    def did_mount(self):
        self._mounted = True
        try:
            self.update()
        except Exception:
            pass

    def will_unmount(self):
        self._mounted = False

    def add_log(self, message: str):
        """Append a timestamped log message. Safe to call from the Flet event loop."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.controls.append(
            ft.Text(
                f"[{timestamp}]  {message}",
                font_family="Consolas",
                size=12,
            )
        )
        if self._mounted:
            try:
                self.log_view.update()
            except Exception:
                pass

    def clear(self):
        self.log_view.controls.clear()
        if self._mounted:
            try:
                self.update()
            except Exception:
                pass
