import asyncio
import logging
import json
import re
from datetime import datetime
from app.scraper.linkedin import LinkedInScraper
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_within_timeframe(posted_text: str, max_seconds: int = 7200) -> bool:
    """Checks if the job was posted within the given number of seconds."""
    text = posted_text.lower()
    max_hours = max_seconds / 3600

    if "just now" in text or "minute" in text or "second" in text:
        return True

    # E.g. "3 hours ago"
    match = re.search(r"(\d+)\s+hour", text)
    if match:
        return int(match.group(1)) <= max_hours

    # E.g. "2 days ago" — only relevant for longer timeframes
    if max_seconds >= 86400:
        match = re.search(r"(\d+)\s+day", text)
        if match:
            return int(match.group(1)) * 24 <= max_hours

    return False


async def run_scraper(
    log_callback=None,
    stop_event: asyncio.Event = None,
    progress_callback=None,
):
    """Entry point for the GUI.

    Args:
        log_callback:      Optional callable(msg: str) for real-time log output.
        stop_event:        asyncio.Event; set it to request a graceful stop.
        progress_callback: Optional callable(current, total, stage: str) for
                           progress updates. Stages: 'search', 'filter', 'fetch'.
    """
    if stop_event is None:
        stop_event = asyncio.Event()  # never-set fallback

    def stopped() -> bool:
        return stop_event.is_set()

    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    def progress(current: int, total: int, stage: str):
        if progress_callback:
            progress_callback(current, total, stage)

    log("Starting AutoApply AI...")

    # Reload settings so the latest .env values are used
    from importlib import reload
    import config.settings as cfg_mod
    reload(cfg_mod)
    from config.settings import settings as fresh_settings

    scraper = LinkedInScraper(headless=fresh_settings.HEADLESS_MODE)

    try:
        await scraper.start()

        # Try to login if credentials exist
        email = getattr(fresh_settings, "LINKEDIN_EMAIL", None)
        password = getattr(fresh_settings, "LINKEDIN_PASSWORD", None)
        if email and password:
            log("Logging in to LinkedIn...")
            try:
                await scraper.login({"email": email, "password": password})
            except Exception as e:
                log(f"Login failed, proceeding as guest: {e}")
        else:
            log("No login credentials found in settings, proceeding as guest.")

        # Load search params
        try:
            with open("data/inputs/search_params.json", "r") as f:
                search_params = json.load(f)
            keywords          = search_params.get("keywords", "Software Engineer")
            location          = search_params.get("location", "United States")
            limit             = search_params.get("limit", 25)
            timeframe         = search_params.get("timeframe", "r7200")
            job_type          = search_params.get("job_type", "")
            remote            = search_params.get("remote", "")
            experience_levels = search_params.get("experience_levels", [])
            exclude_easy_apply= search_params.get("exclude_easy_apply", False)
        except FileNotFoundError:
            log("search_params.json not found, using defaults.")
            keywords, location, limit = "Software Engineer", "United States", 25
            timeframe, job_type, remote, experience_levels = "r7200", "", "", []
            exclude_easy_apply = False

        # Parse timeframe seconds for recency filtering
        tf_seconds = int(timeframe.lstrip("r")) if timeframe.startswith("r") else 7200

        log(f"Searching for '{keywords}' in '{location}' (limit={limit}, timeframe={timeframe})...")
        jobs = await scraper.search_jobs(
            keywords, location,
            limit=limit,
            timeframe=timeframe,
            job_type=job_type,
            remote=remote,
            experience_levels=experience_levels,
            exclude_easy_apply=exclude_easy_apply,
        )

        log(f"Found {len(jobs)} jobs. Filtering by selected time frame...")
        progress(len(jobs), len(jobs), "search")
        if stopped():
            log("Stop requested — aborting.")
            return

        recent_jobs = [j for j in jobs if is_within_timeframe(j.get("posted_time", ""), tf_seconds)]
        log(f"{len(recent_jobs)} jobs match the time frame filter.")
        progress(len(recent_jobs), len(jobs), "filter")

        if recent_jobs:
            for i, job in enumerate(recent_jobs):
                if stopped():
                    log(f"Stop requested — halting after {i} descriptions fetched.")
                    break
                log(f"Fetching description {i+1}/{len(recent_jobs)}: {job['title']}")
                progress(i + 1, len(recent_jobs), "fetch")
                description = await scraper.get_job_description(job['link'], exclude_easy_apply=exclude_easy_apply)
                if exclude_easy_apply and description == "EASY_APPLY_SKIPPED":
                    log(f"Skipping {job['title']} (discovered to be Easy Apply)")
                    continue
                job['description'] = description
                # Interruptible sleep: check every 0.5 s
                for _ in range(2):
                    if stopped():
                        break
                    await asyncio.sleep(0.5)

            # Save whatever we managed to collect
            collected = [j for j in recent_jobs if 'description' in j]
            if collected:
                output_file = "recent_jobs.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(collected, f, indent=4, ensure_ascii=False)
                log(f"Saved {len(collected)} jobs to {output_file}")
        else:
            log("No recent jobs found matching the filters.")

    except Exception as e:
        log(f"Error: {e}")
        logger.error(f"An error occurred: {e}")
    finally:
        await scraper.close()
        log("Scraper closed.")


async def main():

    logger.info("Starting AutoApply AI...")
    
    scraper = LinkedInScraper(headless=settings.HEADLESS_MODE)
    
    try:
        await scraper.start()

        # Load search params
        try:
            with open("data/inputs/search_params.json", "r") as f:
                search_params = json.load(f)
            keywords = search_params.get("keywords", "Software Engineer")
            location = search_params.get("location", "United States")
            limit = search_params.get("limit", 25)
            exclude_easy_apply = search_params.get("exclude_easy_apply", False)
        except FileNotFoundError:
            logger.warning("search_params.json not found, using defaults.")
            keywords = "Software Engineer"
            location = "United States"
            limit = 25
            exclude_easy_apply = False

        # Test Search with higher limit
        jobs = await scraper.search_jobs(keywords, location, limit=limit, exclude_easy_apply=exclude_easy_apply)
        
        logger.info(f"Only processing jobs posted in the last 2 hours from the {len(jobs)} found.")
        
        recent_jobs = [job for job in jobs if is_within_last_two_hours(job.get("posted_time", ""))]
        
        logger.info(f"Found {len(recent_jobs)} jobs posted in the last 2 hours.")
        
        if recent_jobs:
            logger.info(f"Found {len(recent_jobs)} jobs posted in the last 2 hours. Fetching full descriptions...")
            
            # Limit to first 3 for testing speed, or let's do all if count is small
            # Given we only have ~5-10, we can do all.
            for i, job in enumerate(recent_jobs):
                logger.info(f"Fetching description for job {i+1}/{len(recent_jobs)}: {job['title']}")
                description = await scraper.get_job_description(job['link'], exclude_easy_apply=exclude_easy_apply)
                if exclude_easy_apply and description == "EASY_APPLY_SKIPPED":
                    logger.info(f"Skipping {job['title']} (discovered to be Easy Apply)")
                    continue
                job['description'] = description
                # Sleep briefly to be nice
                await asyncio.sleep(1)

            output_file = "recent_jobs.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(recent_jobs, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved recent jobs with descriptions to {output_file}")
            
            # Log first job's description length to verify
            if recent_jobs:
                 desc_preview = recent_jobs[0]['description'][:100].replace('\n', ' ')
                 logger.info(f"First job description preview: {desc_preview}...")
        else:
            logger.info("No jobs found in the last 2 hours.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
