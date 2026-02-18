import flet as ft
import threading
import asyncio
from app.ui.components.logs import LogComponent


class DashboardComponent(ft.Container):
    def __init__(self, log_component: LogComponent):
        super().__init__()
        self.log_component = log_component
        self.is_running = False
        self.padding = 20
        self._stop_event: threading.Event = None
        self._flet_loop: asyncio.AbstractEventLoop = None  # captured on start

        self.status_text = ft.Text("Status: Idle", color=ft.Colors.GREY)
        self.start_btn = ft.ElevatedButton(
            content=ft.Text("Start Scraping"),
            on_click=self.toggle_scraping,
            style=ft.ButtonStyle(color=ft.Colors.GREEN),
        )

        self.content = ft.Column([
            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(
                [self.status_text, self.start_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Text("Recent Activity will appear here..."),
        ])

    # ── helpers ───────────────────────────────────────────────────────────

    def _safe_update(self):
        if self.page:
            try:
                self.update()
            except Exception:
                pass

    def _schedule_on_flet(self, fn):
        """Run fn() on the Flet event loop from any thread."""
        loop = self._flet_loop
        if loop and loop.is_running():
            loop.call_soon_threadsafe(fn)
        else:
            # fallback: just call directly (already on the right thread)
            fn()

    def _ui_set_running(self):
        self.status_text.value = "Status: Running"
        self.status_text.color = ft.Colors.GREEN
        self.start_btn.content = ft.Text("Stop Scraping")
        self.start_btn.style = ft.ButtonStyle(color=ft.Colors.RED)
        self.start_btn.disabled = False
        self._safe_update()

    def _ui_set_stopping(self):
        self.start_btn.content = ft.Text("Stopping…")
        self.start_btn.disabled = True
        self._safe_update()

    def _ui_set_idle(self):
        self.is_running = False
        self._stop_event = None
        self.status_text.value = "Status: Idle"
        self.status_text.color = ft.Colors.GREY
        self.start_btn.content = ft.Text("Start Scraping")
        self.start_btn.style = ft.ButtonStyle(color=ft.Colors.GREEN)
        self.start_btn.disabled = False
        self._safe_update()

    # ── event handlers ────────────────────────────────────────────────────

    def toggle_scraping(self, e):
        if not self.is_running:
            self.start_scraping()
        else:
            self.request_stop()

    def start_scraping(self):
        self.is_running = True
        self._stop_event = threading.Event()
        # Capture the Flet event loop while we're on it
        self._flet_loop = asyncio.get_event_loop()

        self.log_component.add_log("Starting scraper...")
        self._ui_set_running()

        stop_event = self._stop_event

        def target():
            from app.main import run_scraper
            asyncio.run(run_scraper(self._thread_safe_log, stop_event))
            # Schedule UI reset back on the Flet event loop
            self._schedule_on_flet(self._finish_scraping)

        threading.Thread(target=target, daemon=True).start()

    def request_stop(self):
        if self._stop_event:
            self._stop_event.set()
        self.log_component.add_log("Stop requested — waiting for current step to finish…")
        self._ui_set_stopping()

    def _finish_scraping(self):
        """Must be called on the Flet event loop thread."""
        self.log_component.add_log("Scraper finished/stopped.")
        self._ui_set_idle()

    def _thread_safe_log(self, message: str):
        """Log callback safe to call from the background scraper thread."""
        self._schedule_on_flet(lambda: self.log_component.add_log(message))
