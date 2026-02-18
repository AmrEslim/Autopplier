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

def is_within_last_two_hours(posted_text: str) -> bool:
    """Checks if the job was posted within the last 2 hours."""
    text = posted_text.lower()
    if "just now" in text or "minute" in text or "second" in text:
        return True
    
    # Check for hours. E.g. "1 hour ago"
    match = re.search(r"(\d+)\s+hour", text)
    if match:
        hours = int(match.group(1))
        return hours < 2
    
    return False

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
        except FileNotFoundError:
            logger.warning("search_params.json not found, using defaults.")
            keywords = "Software Engineer"
            location = "United States"
            limit = 25

        # Test Search with higher limit
        jobs = await scraper.search_jobs(keywords, location, limit=limit)
        
        logger.info(f"Only processing jobs posted in the last 2 hours from the {len(jobs)} found.")
        
        recent_jobs = [job for job in jobs if is_within_last_two_hours(job.get("posted_time", ""))]
        
        logger.info(f"Found {len(recent_jobs)} jobs posted in the last 2 hours.")
        
        if recent_jobs:
            logger.info(f"Found {len(recent_jobs)} jobs posted in the last 2 hours. Fetching full descriptions...")
            
            # Limit to first 3 for testing speed, or let's do all if count is small
            # Given we only have ~5-10, we can do all.
            for i, job in enumerate(recent_jobs):
                logger.info(f"Fetching description for job {i+1}/{len(recent_jobs)}: {job['title']}")
                description = await scraper.get_job_description(job['link'])
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
