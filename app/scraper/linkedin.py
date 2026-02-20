import logging
import asyncio
import random
from typing import List, Dict, Any

from app.scraper.base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    """
    Scraper implementation for LinkedIn.
    """

    async def login(self, credentials: Dict[str, str]):
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            raise ValueError("Email and password are required for LinkedIn login.")

        try:
            self.logger.info("Navigating to LinkedIn login page...")
            await self.page.goto("https://www.linkedin.com/login")
            
            self.logger.info("Filling login credentials...")
            await self.page.fill("#username", email)
            await self.page.fill("#password", password)
            
            await self.page.click("button[type='submit']")
            await self.page.wait_for_url("https://www.linkedin.com/feed/", timeout=15000)
            self.logger.info("Successfully logged in to LinkedIn.")
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise

    async def search_jobs(self, query: str, location: str, limit: int = 25, **kwargs) -> List[Dict[str, Any]]:
        """
        Searches for jobs with pagination support.
        Args:
            limit:             Maximum number of jobs to fetch.
            timeframe:         LinkedIn f_TPR value, e.g. 'r7200'.
            job_type:          LinkedIn f_JT value, e.g. 'F' for Full-time.
            remote:            LinkedIn f_WT value, e.g. '2' for Remote.
            experience_levels: List of LinkedIn f_E codes, e.g. ['2', '3'].
        """
        if not self.page:
            raise RuntimeError("Browser not started.")

        timeframe         = kwargs.get("timeframe", "r86400")
        job_type          = kwargs.get("job_type", "")
        remote            = kwargs.get("remote", "")
        experience_levels = kwargs.get("experience_levels", [])
        exclude_easy_apply= kwargs.get("exclude_easy_apply", False)

        self.logger.info(f"Searching for '{query}' in '{location}' (Limit: {limit})...")
        if exclude_easy_apply:
            self.logger.info("Will exclude jobs with 'Easy Apply'.")

        all_jobs = []
        offset = 0

        while len(all_jobs) < limit:
            # Build URL with all active filters
            params = f"keywords={query}&location={location}&f_TPR={timeframe}&start={offset}"
            if job_type:
                params += f"&f_JT={job_type}"
            if remote:
                params += f"&f_WT={remote}"
            if experience_levels:
                params += "&f_E=" + "%2C".join(experience_levels)
            search_url = f"https://www.linkedin.com/jobs/search/?{params}"
            self.logger.info(f"Fetching jobs from offset {offset}...")
            
            try:
                await self.page.goto(search_url)
                
                # Wait for job list
                try:
                    await self.page.wait_for_selector(".jobs-search__results-list li", timeout=10000)
                except:
                    self.logger.warning(f"No more jobs found at offset {offset}.")
                    break
                
                # Get all job cards on current page
                job_cards = await self.page.query_selector_all(".jobs-search__results-list li")
                self.logger.info(f"Found {len(job_cards)} job cards on page.")
                
                if not job_cards:
                    break

                for card in job_cards:
                    if len(all_jobs) >= limit:
                        break
                        
                    try:
                        title_elem = await card.query_selector("h3.base-search-card__title")
                        company_elem = await card.query_selector("h4.base-search-card__subtitle")
                        location_elem = await card.query_selector("span.job-search-card__location")
                        link_elem = await card.query_selector("a.base-card__full-link")
                        time_elem = await card.query_selector("time")
                        
                        title = await title_elem.inner_text() if title_elem else "Unknown"
                        company = await company_elem.inner_text() if company_elem else "Unknown"
                        location = await location_elem.inner_text() if location_elem else "Unknown"
                        link = await link_elem.get_attribute("href") if link_elem else "Unknown"
                        posted_time = await time_elem.inner_text() if time_elem else "Unknown"
                        
                        if link != "Unknown":
                            if exclude_easy_apply:
                                card_text = await card.inner_text()
                                if "easy apply" in card_text.lower() or "apply with linkedin" in card_text.lower():
                                    self.logger.info(f"Skipping '{title}' because it has Easy Apply.")
                                    continue
                                    
                            all_jobs.append({
                                "title": title.strip(),
                                "company": company.strip(),
                                "location": location.strip(),
                                "link": link.split("?")[0],
                                "posted_time": posted_time.strip()
                            })
                    except Exception as e:
                        pass # Squelch minor card errors
                
                # Prepare for next page
                offset += 25
                import random
                await asyncio.sleep(random.uniform(2, 5)) # Random politeness delay
                
            except Exception as e:
                self.logger.error(f"Error extracting jobs at offset {offset}: {e}")
                break
        
        return all_jobs

    async def get_job_description(self, job_url: str, exclude_easy_apply: bool = False) -> str:
        """
        Navigates to the job URL and extracts the full description.
        """
        if not self.page:
            return "Error: Browser not started."
            
        import random
        import asyncio

        for attempt in range(3):
            try:
                # Create a new page for the job view
                page = await self.context.new_page()
                await page.goto(job_url)
                
                # Random delay to mimic human behavior
                await asyncio.sleep(random.uniform(1, 3))
                
                # Helper to expand "See more" if it exists
                try:
                    await page.click("button.show-more-less-html__button", timeout=2000)
                except:
                    pass 
                    
                # Wait for description container
                await page.wait_for_selector(".show-more-less-html__markup, .description__text, #job-details", timeout=5000)
                
                if exclude_easy_apply:
                    # Check for "Easy Apply" or "Apply with LinkedIn" button
                    page_html = await page.content()
                    normalized = page_html.lower()
                    if ("easy apply" in normalized and "jobs-apply-button" in normalized) or "apply-link-onsite" in normalized:
                        self.logger.info(f"Skipping Easy Apply job: {job_url}")
                        await page.close()
                        return "EASY_APPLY_SKIPPED"
                        
                description_elem = await page.query_selector(".show-more-less-html__markup")
                if not description_elem:
                     description_elem = await page.query_selector(".description__text")
                if not description_elem:
                     description_elem = await page.query_selector("#job-details")
                     
                description = await description_elem.inner_text() if description_elem else "Description not found."
                
                await page.close()
                return description.strip()
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1}/3 failed for {job_url}: {e}")
                if 'page' in locals():
                    await page.close()
                await asyncio.sleep(random.uniform(2, 5))
        
        return "Failed to extract description."

    async def apply(self, job_url: str, resume_path: str, user_data: Dict[str, Any]):
        if not self.page:
            raise RuntimeError("Browser not started.")
            
        self.logger.info(f"Navigating to job: {job_url}")
        await self.page.goto(job_url)
        
        # TODO: Implement Easy Apply logic
        pass
