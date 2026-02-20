import logging
import asyncio
import random
from typing import List, Dict, Any

from app.scraper.base_scraper import BaseScraper


class EUStartupsScraper(BaseScraper):
    """
    Scraper implementation for EU-Startups job board
    (https://www.eu-startups.com/startup-jobs/).

    The page uses the WP Job Board plugin.  Each listing is a
    `.wpjb-grid-row` div with sub-columns for title/company,
    location/type, and date.
    """

    BASE_URL = "https://www.eu-startups.com/startup-jobs/"

    async def login(self, credentials: Dict[str, str]):
        """EU-Startups does not require login — this is a no-op."""
        self.logger.info("EU-Startups is a public site — no login required.")

    async def search_jobs(
        self, query: str, location: str, limit: int = 25, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrapes job listings from the EU-Startups job board.
        The `query` parameter filters job titles (case-insensitive).
        Pagination uses the /page/N/ URL pattern.
        """
        if not self.page:
            raise RuntimeError("Browser not started.")

        self.logger.info(
            f"Scraping EU-Startups job board (filter='{query}', limit={limit})..."
        )

        all_jobs: List[Dict[str, Any]] = []
        page_num = 1

        while len(all_jobs) < limit:
            # Build paginated URL
            if page_num == 1:
                url = self.BASE_URL
            else:
                url = f"{self.BASE_URL}page/{page_num}/"

            self.logger.info(f"Fetching page {page_num}: {url}")

            try:
                await self.page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1, 3))

                # Wait for WP Job Board rows to load
                try:
                    await self.page.wait_for_selector(
                        ".wpjb-grid-row", timeout=10000
                    )
                except Exception:
                    self.logger.warning(
                        f"No job listings found on page {page_num}. Stopping."
                    )
                    break

                # Extract jobs from this page
                jobs = await self._extract_jobs_from_page(query)

                if not jobs:
                    self.logger.info(
                        f"No (matching) jobs on page {page_num}. Stopping."
                    )
                    break

                for job in jobs:
                    if len(all_jobs) >= limit:
                        break
                    all_jobs.append(job)

                self.logger.info(
                    f"Collected {len(all_jobs)} jobs so far."
                )

                # Check for next page link
                next_link = await self.page.query_selector(
                    ".wpjb-paginate-links a.next.page-numbers"
                )
                if not next_link:
                    self.logger.info("No more pages available.")
                    break

                page_num += 1
                await asyncio.sleep(random.uniform(2, 4))

            except Exception as e:
                self.logger.error(f"Error on page {page_num}: {e}")
                break

        self.logger.info(
            f"Finished scraping EU-Startups. Total jobs: {len(all_jobs)}"
        )
        return all_jobs

    # ------------------------------------------------------------------
    async def _extract_jobs_from_page(
        self, query: str
    ) -> List[Dict[str, Any]]:
        """
        Extracts job data from the current page using WP Job Board selectors.
        Filters by `query` if non-empty (matches against title).
        """
        results: List[Dict[str, Any]] = []

        # Each job listing is a .wpjb-grid-row div
        cards = await self.page.query_selector_all(".wpjb-grid-row.wpjb-click-area")

        if not cards:
            # Fallback: try without .wpjb-click-area
            cards = await self.page.query_selector_all(".wpjb-grid-row")

        self.logger.info(f"Found {len(cards)} job cards on page.")

        for card in cards:
            try:
                # Title & link  (.wpjb-col-title .wpjb-line-major a)
                title_elem = await card.query_selector(
                    ".wpjb-col-title .wpjb-line-major a"
                )
                if not title_elem:
                    continue

                title = (await title_elem.inner_text()).strip()
                link = (await title_elem.get_attribute("href")) or ""

                # Optional keyword filter (case-insensitive)
                if query and query.lower() not in title.lower():
                    continue

                # Company name  (.wpjb-col-title .wpjb-sub)
                company_elem = await card.query_selector(
                    ".wpjb-col-title .wpjb-sub"
                )
                company = ""
                if company_elem:
                    company = (await company_elem.inner_text()).strip()

                # Location  (.wpjb-col-location .wpjb-icon-location)
                location_elem = await card.query_selector(
                    ".wpjb-col-location .wpjb-icon-location"
                )
                job_location = ""
                if location_elem:
                    job_location = (await location_elem.inner_text()).strip()

                # Job type  (.wpjb-col-location .wpjb-sub)
                type_elem = await card.query_selector(
                    ".wpjb-col-location .wpjb-sub"
                )
                job_type = ""
                if type_elem:
                    job_type = (await type_elem.inner_text()).strip()

                # Date posted  (.wpjb-grid-col-right .wpjb-line-major)
                date_elem = await card.query_selector(
                    ".wpjb-grid-col-right .wpjb-line-major"
                )
                posted_time = ""
                if date_elem:
                    posted_time = (await date_elem.inner_text()).strip()

                results.append(
                    {
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "link": link,
                        "posted_time": posted_time,
                        "job_type": job_type,
                        "source": "EU-Startups",
                    }
                )
            except Exception as e:
                self.logger.debug(f"Skipping card: {e}")

        return results

    # ------------------------------------------------------------------
    async def get_job_description(
        self, job_url: str, exclude_easy_apply: bool = False
    ) -> str:
        """
        Navigates to a job listing page and extracts the full description.
        """
        if not self.page:
            return "Error: Browser not started."

        for attempt in range(3):
            try:
                page = await self.context.new_page()
                await page.goto(job_url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1, 3))

                # WP Job Board uses .wpjb-job-content for the description
                content_elem = await page.query_selector(
                    ".wpjb-job-content"
                )
                if not content_elem:
                    # Fallback selectors
                    content_elem = await page.query_selector(
                        ".entry-content, .td-post-content, article .content"
                    )
                if not content_elem:
                    content_elem = await page.query_selector("article")

                description = ""
                if content_elem:
                    description = (await content_elem.inner_text()).strip()
                else:
                    description = "Description not found."

                await page.close()
                return description

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/3 failed for {job_url}: {e}"
                )
                if "page" in locals():
                    try:
                        await page.close()
                    except Exception:
                        pass
                await asyncio.sleep(random.uniform(2, 4))

        return "Failed to extract description."

    # ------------------------------------------------------------------
    async def apply(
        self, job_url: str, resume_path: str, user_data: Dict[str, Any]
    ):
        """
        EU-Startups does not support direct applications — this is a no-op.
        """
        self.logger.info(
            "EU-Startups does not support direct applications."
        )
