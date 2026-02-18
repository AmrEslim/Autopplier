import flet as ft
import json
import os


class ResultsComponent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 10

        self.results_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.only(right=8),
        )

        self.count_text = ft.Text("No results loaded.", color=ft.Colors.GREY_400, italic=True)

        self.controls = [
            ft.Row([
                ft.Text("Results", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.count_text,
                ft.IconButton(
                    icon=ft.icons.Icons.REFRESH,
                    tooltip="Reload results from file",
                    on_click=lambda e: self.load_results(),
                ),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(),
            self.results_list,
        ]

    def did_mount(self):
        self.load_results()

    def load_results(self):
        self.results_list.controls.clear()
        path = "recent_jobs.json"
        if not os.path.exists(path):
            self.count_text.value = "No results file found. Run the scraper first."
            self.count_text.color = ft.Colors.ORANGE_400
            if self.page:
                self.update()
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        except Exception as ex:
            self.count_text.value = f"Error reading results: {ex}"
            self.count_text.color = ft.Colors.RED_400
            if self.page:
                self.update()
            return

        if not jobs:
            self.count_text.value = "0 jobs found."
            self.count_text.color = ft.Colors.GREY_400
        else:
            self.count_text.value = f"{len(jobs)} job(s) found"
            self.count_text.color = ft.Colors.GREEN_400

        for job in jobs:
            self.results_list.controls.append(self._build_job_card(job))

        if self.page:
            self.update()

    def _build_job_card(self, job: dict) -> ft.Container:
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        location = job.get("location", "")
        posted = job.get("posted_time", "")
        link = job.get("link", "")
        description = job.get("description", "No description available.")
        # Truncate description for preview
        preview = description[:300].replace("\n", " ") + ("..." if len(description) > 300 else "")

        expanded_ref = [False]
        desc_text = ft.Text(preview, size=12, color=ft.Colors.GREY_300, selectable=True)
        toggle_btn = ft.TextButton("Show more", style=ft.ButtonStyle(color=ft.Colors.BLUE_300))

        def toggle_desc(e):
            if expanded_ref[0]:
                desc_text.value = preview
                toggle_btn.text = "Show more"
            else:
                desc_text.value = description
                toggle_btn.text = "Show less"
            expanded_ref[0] = not expanded_ref[0]
            desc_text.update()
            toggle_btn.update()

        toggle_btn.on_click = toggle_desc

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Row([
                            ft.Icon(ft.icons.Icons.BUSINESS, size=14, color=ft.Colors.BLUE_300),
                            ft.Text(company, size=13, color=ft.Colors.BLUE_300),
                            ft.Text("·", color=ft.Colors.GREY_500),
                            ft.Icon(ft.icons.Icons.LOCATION_ON, size=14, color=ft.Colors.GREY_400),
                            ft.Text(location, size=13, color=ft.Colors.GREY_400),
                            ft.Text("·", color=ft.Colors.GREY_500),
                            ft.Icon(ft.icons.Icons.ACCESS_TIME, size=14, color=ft.Colors.GREY_400),
                            ft.Text(posted, size=13, color=ft.Colors.GREY_400),
                        ], spacing=4, wrap=True),
                    ], expand=True, spacing=4),
                    ft.IconButton(
                        icon=ft.icons.Icons.OPEN_IN_NEW,
                        tooltip="Open on LinkedIn",
                        icon_color=ft.Colors.BLUE_400,
                        on_click=lambda e, url=link: self.page.launch_url(url) if self.page else None,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                desc_text,
                toggle_btn,
            ], spacing=6),
            padding=ft.padding.all(16),
            border_radius=10,
            bgcolor=ft.Colors.GREY_900,
            border=ft.border.all(1, ft.Colors.GREY_800),
        )
