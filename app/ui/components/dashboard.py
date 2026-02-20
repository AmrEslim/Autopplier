import asyncio
from datetime import datetime
import flet as ft
from app.ui.components.logs import LogComponent


class DashboardComponent(ft.Container):
    def __init__(self, log_component: LogComponent, results_tab=None):
        super().__init__()
        self.log_component = log_component
        self.results_tab = results_tab
        self.is_running = False
        self.padding = 20
        self._stop_event: asyncio.Event = None

        # ── Status row ────────────────────────────────────────────────────
        self.status_text = ft.Text("Status: Idle", color=ft.Colors.GREY, size=14)
        self.last_run_text = ft.Text("Last run: never", color=ft.Colors.GREY_600, size=12, italic=True)

        self.start_btn = ft.ElevatedButton(
            content=ft.Text("Start Scraping"),
            on_click=self.toggle_scraping,
            style=ft.ButtonStyle(color=ft.Colors.GREEN),
        )

        # ── Stats cards ───────────────────────────────────────────────────
        self._total_found   = 0
        self._recent_count  = 0
        self._fetch_current = 0
        self._fetch_total   = 0

        self.found_text   = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_300)
        self.recent_text  = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
        self.fetched_text = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_300)

        # ── Progress bar ──────────────────────────────────────────────────
        self.progress_bar = ft.ProgressBar(
            value=0,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.GREY_800,
            visible=False,
        )
        self.progress_label = ft.Text("", size=11, color=ft.Colors.GREY_400, visible=False)

        # ── Layout ────────────────────────────────────────────────────────
        self.content = ft.Column([
            # Header
            ft.Row([
                ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.last_run_text,
            ]),
            ft.Row(
                [self.status_text, self.start_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),

            # Stats cards
            ft.Row([
                self._stat_card("Jobs Found", self.found_text, ft.Colors.BLUE_900),
                self._stat_card("Match Filter", self.recent_text, ft.Colors.GREEN_900),
                self._stat_card("Descriptions", self.fetched_text, ft.Colors.ORANGE_900),
            ], spacing=12),

            # Progress bar
            ft.Container(height=8),
            self.progress_label,
            ft.Container(height=4),
            self.progress_bar,
        ], spacing=8)

    # ── Stat card builder ─────────────────────────────────────────────────

    def _stat_card(self, label: str, value_text: ft.Text, bg: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=11, color=ft.Colors.GREY_400),
                value_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            expand=True,
            padding=ft.padding.symmetric(vertical=14, horizontal=10),
            border_radius=10,
            bgcolor=bg,
            border=ft.border.all(1, ft.Colors.GREY_800),
        )

    # ── Safe update ───────────────────────────────────────────────────────

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass

    # ── UI state helpers ──────────────────────────────────────────────────

    def _reset_stats(self):
        self.found_text.value   = "—"
        self.recent_text.value  = "—"
        self.fetched_text.value = "—"
        self.progress_bar.value   = 0
        self.progress_bar.visible = False
        self.progress_label.value   = ""
        self.progress_label.visible = False

    def _set_running(self):
        self.status_text.value = "Status: Running"
        self.status_text.color = ft.Colors.GREEN
        self.start_btn.content = ft.Text("Stop Scraping")
        self.start_btn.style   = ft.ButtonStyle(color=ft.Colors.RED)
        self.start_btn.disabled = False
        self._safe_update()

    def _set_stopping(self):
        self.start_btn.content  = ft.Text("Stopping…")
        self.start_btn.disabled = True
        self._safe_update()

    def _set_idle(self):
        self.is_running = False
        self._stop_event = None
        self.status_text.value  = "Status: Idle"
        self.status_text.color  = ft.Colors.GREY
        self.start_btn.content  = ft.Text("Start Scraping")
        self.start_btn.style    = ft.ButtonStyle(color=ft.Colors.GREEN)
        self.start_btn.disabled = False
        self.progress_bar.visible   = False
        self.progress_label.visible = False
        self._safe_update()

    # ── Progress callback (called from run_scraper) ───────────────────────

    def _on_progress(self, current: int, total: int, stage: str):
        if stage == "search":
            self.found_text.value = str(total)
            try:
                self.found_text.update()
            except Exception:
                pass

        elif stage == "filter":
            self.recent_text.value = str(current)
            # Show progress bar only if there are descriptions to fetch
            if current > 0:
                self.progress_bar.value   = 0
                self.progress_bar.visible = True
                self.progress_label.value   = f"Fetching descriptions: 0 / {current}"
                self.progress_label.visible = True
            try:
                self.update()
            except Exception:
                pass

        elif stage == "fetch":
            ratio = current / total if total else 0
            self.fetched_text.value       = f"{current}/{total}"
            self.progress_bar.value       = ratio
            self.progress_label.value     = f"Fetching descriptions: {current} / {total}"
            try:
                self.fetched_text.update()
                self.progress_bar.update()
                self.progress_label.update()
            except Exception:
                pass

    # ── Event handlers ────────────────────────────────────────────────────

    def toggle_scraping(self, e):
        if not self.is_running:
            self.page.run_task(self._run_scraping_task)
        else:
            self._request_stop()

    async def _run_scraping_task(self):
        """Runs entirely on the Flet event loop — no thread-safety issues."""
        from app.main import run_scraper

        self.is_running = True
        self._stop_event = asyncio.Event()
        self._reset_stats()
        self.log_component.add_log("Starting scraper...")
        self._set_running()

        await run_scraper(
            log_callback=self.log_component.add_log,
            stop_event=self._stop_event,
            progress_callback=self._on_progress,
        )

        self.last_run_text.value = f"Last run: {datetime.now().strftime('%d %b %Y, %H:%M')}"
        self.log_component.add_log("Scraper finished/stopped.")
        self._set_idle()

        # Auto-refresh the Results tab
        if self.results_tab is not None:
            self.results_tab.refresh()

    def _request_stop(self):
        if self._stop_event:
            self._stop_event.set()
        self.log_component.add_log("Stop requested — waiting for current step to finish…")
        self._set_stopping()
