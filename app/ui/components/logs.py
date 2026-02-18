import flet as ft


class LogComponent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self._pending_logs = []  # messages buffered while the tab is hidden

        self.log_view = ft.ListView(
            expand=True,
            spacing=2,
            auto_scroll=True,
        )

        self.controls = [
            ft.Text("Application Logs", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=self.log_view,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                expand=True,
            )
        ]

    def did_mount(self):
        """Flush buffered logs when the Logs tab becomes the active view."""
        if self._pending_logs:
            for msg in self._pending_logs:
                self.log_view.controls.append(ft.Text(msg, font_family="Consolas"))
            self._pending_logs.clear()
            try:
                self.update()
            except Exception:
                pass

    def add_log(self, message: str):
        """Append a log message. Safe to call at any time."""
        self.log_view.controls.append(ft.Text(message, font_family="Consolas"))
        # Try to push a live update; if the control isn't mounted yet, buffer it
        try:
            self.log_view.update()
        except Exception:
            self._pending_logs.append(message)

    def clear(self):
        self._pending_logs.clear()
        self.log_view.controls.clear()
        try:
            self.update()
        except Exception:
            pass
