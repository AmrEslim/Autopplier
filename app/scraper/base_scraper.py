import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class BaseScraper(ABC):
    """
    Abstract base class for job scrapers.
    Defines the interface for all specific job board scrapers.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Optional[Any] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]

    async def start(self):
        """Initializes the Playwright browser and context with randomized User-Agent."""
        import random
        self.playwright = await async_playwright().start()
        user_agent = random.choice(self.user_agents)
        self.logger.info(f"Starting browser with User-Agent: {user_agent}")
        
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(user_agent=user_agent)
        self.page = await self.context.new_page()
        self.logger.info("Browser started.")

    async def close(self):
        """Closes the browser and stops Playwright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Browser closed.")

    @abstractmethod
    async def login(self, credentials: Dict[str, str]):
        """
        Logs into the job board.
        
        Args:
            credentials: A dictionary containing 'email' and 'password' (or other required fields).
        """
        pass

    @abstractmethod
    async def search_jobs(self, query: str, location: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Searches for jobs based on query and location.
        
        Returns:
            A list of job dictionaries containing details like title, company, url, etc.
        """
        pass

    @abstractmethod
    async def apply(self, job_url: str, resume_path: str, user_data: Dict[str, Any]):
        """
        Applies to a specific job.
        
        Args:
            job_url: The URL of the job posting.
            resume_path: Path to the resume file.
            user_data: User profile data for form filling.
        """
        pass
