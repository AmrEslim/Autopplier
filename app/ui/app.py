import flet as ft
import logging
from app.ui.components.logs import LogComponent
from app.ui.components.dashboard import DashboardComponent
from app.ui.components.settings import SettingsComponent
from app.ui.components.results import ResultsComponent

# Configure logging to also print to console for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(page: ft.Page):
    page.title = "AutoApply AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1000
    page.window_height = 800

    # Components
    log_component = LogComponent()
    dashboard = DashboardComponent(log_component)
    settings_tab = SettingsComponent()

    results_tab = ResultsComponent()

    views = [dashboard, log_component, results_tab, settings_tab]

    # Content area — swapped on nav change
    content_area = ft.Container(
        content=dashboard,
        expand=True,
        padding=20,
    )

    def nav_changed(e):
        content_area.content = views[e.control.selected_index]
        content_area.update()

    # NavigationBar is the correct tab-like widget in Flet 0.80.5
    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(
                label="Dashboard",
                icon=ft.icons.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.icons.Icons.DASHBOARD,
            ),
            ft.NavigationBarDestination(
                label="Logs",
                icon=ft.icons.Icons.TERMINAL_OUTLINED,
                selected_icon=ft.icons.Icons.TERMINAL,
            ),
            ft.NavigationBarDestination(
                label="Results",
                icon=ft.icons.Icons.WORK_OUTLINE,
                selected_icon=ft.icons.Icons.WORK,
            ),
            ft.NavigationBarDestination(
                label="Settings",
                icon=ft.icons.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.Icons.SETTINGS,
            ),
        ],
        selected_index=0,
        on_change=nav_changed,
    )

    page.add(
        ft.Column(
            [content_area, nav],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    ft.run(main)
