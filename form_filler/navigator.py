from playwright.sync_api import sync_playwright, Page, BrowserContext
from typing import Optional
from config.settings import settings

class Navigator:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
        if not self.browser:
            self.browser = self.playwright.chromium.launch(headless=settings.HEADLESS_MODE)
        if not self.context:
            self.context = self.browser.new_context()
        if not self.page:
            self.page = self.context.new_page()

    @property
    def current_page(self) -> Optional[Page]:
        return self.page

    def go_to(self, url: str):
        if not self.page:
            self.start()
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
    
    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
