import flet as ft
import json
import os
from dotenv import set_key, dotenv_values

ENV_PATH = ".env"

# LinkedIn time-frame filter values (f_TPR param)
TIMEFRAME_OPTIONS = {
    "Past 1 Hour":   "r3600",
    "Past 2 Hours":  "r7200",
    "Past 6 Hours":  "r21600",
    "Past 12 Hours": "r43200",
    "Past 24 Hours": "r86400",
    "Past 3 Days":   "r259200",
    "Past Week":     "r604800",
}

JOB_TYPE_OPTIONS = {
    "Any":        "",
    "Full-time":  "F",
    "Part-time":  "P",
    "Contract":   "C",
    "Internship": "I",
}

EXPERIENCE_OPTIONS = {
    "Internship":  "1",
    "Entry Level": "2",
    "Associate":   "3",
    "Mid-Senior":  "4",
    "Director":    "5",
    "Executive":   "6",
}

REMOTE_OPTIONS = {
    "Any":     "",
    "On-site": "1",
    "Remote":  "2",
    "Hybrid":  "3",
}



def _section_header(title: str, icon: str) -> ft.Row:
    return ft.Row(
        [
            ft.Icon(icon, color=ft.Colors.BLUE_400, size=18),
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
        ],
        spacing=8,
    )


class SettingsComponent(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = ft.padding.all(24)
        self.expand = True

        # ── Search params ──────────────────────────────────────────────────
        self.keyword_input = ft.TextField(
            label="Job Keywords",
            value="Software Engineer",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            filled=True,
        )
        self.location_input = ft.TextField(
            label="Location",
            value="Berlin",
            prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
            border_radius=8,
            filled=True,
        )
        self.limit_input = ft.TextField(
            label="Max Jobs to Scrape",
            value="50",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.FORMAT_LIST_NUMBERED,
            border_radius=8,
            filled=True,
            width=200,
        )

        # ── Time frame ─────────────────────────────────────────────────────
        self.timeframe_dropdown = ft.Dropdown(
            label="Time Frame",
            options=[ft.dropdown.Option(k) for k in TIMEFRAME_OPTIONS],
            value="Past 2 Hours",
            border_radius=8,
            filled=True,
        )

        # ── Job type ───────────────────────────────────────────────────────
        self.job_type_dropdown = ft.Dropdown(
            label="Job Type",
            options=[ft.dropdown.Option(k) for k in JOB_TYPE_OPTIONS],
            value="Any",
            border_radius=8,
            filled=True,
        )

        # ── Remote filter ──────────────────────────────────────────────────
        self.remote_dropdown = ft.Dropdown(
            label="Work Mode",
            options=[ft.dropdown.Option(k) for k in REMOTE_OPTIONS],
            value="Any",
            border_radius=8,
            filled=True,
        )

        # ── Experience level checkboxes ────────────────────────────────────
        self.exp_checkboxes: dict[str, ft.Checkbox] = {
            label: ft.Checkbox(label=label, value=False)
            for label in EXPERIENCE_OPTIONS
        }

        # ── Headless mode ──────────────────────────────────────────────────
        self.headless_switch = ft.Switch(
            label="Headless Mode (run browser in background)",
            value=False,
            active_color=ft.Colors.BLUE_400,
        )

        self.exclude_easy_apply_checkbox = ft.Checkbox(
            label="Exclude Easy Apply jobs", 
            value=False,
            active_color=ft.Colors.BLUE_400
        )

        # ── Credentials ────────────────────────────────────────────────────
        self.email_input = ft.TextField(
            label="LinkedIn Email",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_radius=8,
            filled=True,
        )
        self.password_input = ft.TextField(
            label="LinkedIn Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            border_radius=8,
            filled=True,
        )
        self.openai_key_input = ft.TextField(
            label="OpenAI API Key",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY_OUTLINED,
            border_radius=8,
            filled=True,
        )

        # ── Save button & snackbar ─────────────────────────────────────────
        self.save_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SAVE_OUTLINED, size=18),
                    ft.Text("Save All Settings"),
                ],
                tight=True,
                spacing=8,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self.save_settings,
        )

        self.load_settings()
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        exp_row = ft.Row(
            [cb for cb in self.exp_checkboxes.values()],
            wrap=True,
            spacing=4,
            run_spacing=4,
        )

        self.content = ft.Column(
            [
                # ── Page title ──────────────────────────────────────────
                ft.Row(
                    [
                        ft.Icon(ft.Icons.TUNE, color=ft.Colors.WHITE, size=24),
                        ft.Text("Settings", size=22, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),

                # ── Search Parameters ───────────────────────────────────
                _section_header("Search Parameters", ft.Icons.MANAGE_SEARCH),
                ft.ResponsiveRow(
                    [
                        ft.Column([self.keyword_input],  col={"xs": 12, "md": 6}),
                        ft.Column([self.location_input], col={"xs": 12, "md": 6}),
                    ],
                    spacing=12,
                ),
                self.limit_input,

                ft.Divider(height=1, color=ft.Colors.OUTLINE),

                # ── Filters ─────────────────────────────────────────────
                _section_header("Job Filters (LinkedIn)", ft.Icons.FILTER_LIST),
                ft.ResponsiveRow(
                    [
                        ft.Column([self.timeframe_dropdown], col={"xs": 12, "md": 4}),
                        ft.Column([self.job_type_dropdown],  col={"xs": 12, "md": 4}),
                        ft.Column([self.remote_dropdown],    col={"xs": 12, "md": 4}),
                    ],
                    spacing=12,
                ),

                # Experience level
                ft.Text("Experience Level", size=12, color=ft.Colors.GREY_400),
                ft.Container(
                    content=exp_row,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),

                ft.Container(height=8),
                self.exclude_easy_apply_checkbox,

                ft.Divider(height=1, color=ft.Colors.OUTLINE),

                # ── Browser ─────────────────────────────────────────────
                _section_header("Browser Options", ft.Icons.WEB_OUTLINED),
                self.headless_switch,

                ft.Divider(height=1, color=ft.Colors.OUTLINE),

                # ── Credentials ─────────────────────────────────────────
                _section_header("Credentials", ft.Icons.SECURITY_OUTLINED),
                ft.ResponsiveRow(
                    [
                        ft.Column([self.email_input],    col={"xs": 12, "md": 6}),
                        ft.Column([self.password_input], col={"xs": 12, "md": 6}),
                    ],
                    spacing=12,
                ),
                self.openai_key_input,

                ft.Divider(height=1, color=ft.Colors.OUTLINE),

                # ── Save ────────────────────────────────────────────────
                ft.Row([self.save_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ──────────────────────────────────────────────────────────────────────
    def load_settings(self):
        # Load search params JSON
        try:
            with open("data/inputs/search_params.json", "r") as f:
                data = json.load(f)
            self.keyword_input.value    = data.get("keywords", "Software Engineer")
            self.location_input.value   = data.get("location", "Berlin")
            self.limit_input.value      = str(data.get("limit", 50))

            # Reverse-lookup timeframe label from stored value
            stored_tpr = data.get("timeframe", "r7200")
            inv_tf = {v: k for k, v in TIMEFRAME_OPTIONS.items()}
            self.timeframe_dropdown.value = inv_tf.get(stored_tpr, "Past 2 Hours")

            # Job type
            stored_jt = data.get("job_type", "")
            inv_jt = {v: k for k, v in JOB_TYPE_OPTIONS.items()}
            self.job_type_dropdown.value = inv_jt.get(stored_jt, "Any")

            # Remote
            stored_rm = data.get("remote", "")
            inv_rm = {v: k for k, v in REMOTE_OPTIONS.items()}
            self.remote_dropdown.value = inv_rm.get(stored_rm, "Any")

            # Experience
            stored_exp = data.get("experience_levels", [])
            inv_exp = {v: k for k, v in EXPERIENCE_OPTIONS.items()}
            for code in stored_exp:
                label = inv_exp.get(code)
                if label and label in self.exp_checkboxes:
                    self.exp_checkboxes[label].value = True
                    
            self.exclude_easy_apply_checkbox.value = data.get("exclude_easy_apply", False)

        except FileNotFoundError:
            pass

        # Load .env credentials
        env = dotenv_values(ENV_PATH)
        self.email_input.value      = env.get("LINKEDIN_EMAIL", "")
        self.password_input.value   = env.get("LINKEDIN_PASSWORD", "")
        self.openai_key_input.value = env.get("OPENAI_API_KEY", "")
        self.headless_switch.value  = env.get("HEADLESS_MODE", "False").lower() == "true"

    # ──────────────────────────────────────────────────────────────────────
    def save_settings(self, e):
        # Collect experience codes
        selected_exp = [
            EXPERIENCE_OPTIONS[label]
            for label, cb in self.exp_checkboxes.items()
            if cb.value
        ]

        # Build search params
        data = {
            "keywords":          self.keyword_input.value.strip(),
            "location":          self.location_input.value.strip(),
            "limit":             int(self.limit_input.value or 50),
            "timeframe":         TIMEFRAME_OPTIONS.get(self.timeframe_dropdown.value, "r7200"),
            "job_type":          JOB_TYPE_OPTIONS.get(self.job_type_dropdown.value, ""),
            "remote":            REMOTE_OPTIONS.get(self.remote_dropdown.value, ""),
            "experience_levels": selected_exp,
            "exclude_easy_apply": self.exclude_easy_apply_checkbox.value,
        }

        os.makedirs("data/inputs", exist_ok=True)
        with open("data/inputs/search_params.json", "w") as f:
            json.dump(data, f, indent=4)

        # Update .env
        set_key(ENV_PATH, "LINKEDIN_EMAIL",    self.email_input.value.strip())
        set_key(ENV_PATH, "LINKEDIN_PASSWORD",  self.password_input.value)
        set_key(ENV_PATH, "OPENAI_API_KEY",     self.openai_key_input.value.strip())
        set_key(ENV_PATH, "HEADLESS_MODE",      str(self.headless_switch.value))

        e.page.show_dialog(
            ft.SnackBar(content="✅ Settings saved successfully!")
        )
