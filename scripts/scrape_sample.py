"""Sample scraping script."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import asyncio
import logging

from app.core.database import SessionLocal
from app.services.scraping_service import ScrapingJobService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_sample(url: str, website_type: str = "generic", priority: int = 1):
    """Run a sample scraping job."""
    db = SessionLocal()
    try:
        service = ScrapingJobService()
        job = service.create_job(
            db,
            {
                "url": url,
                "website_type": website_type,
                "priority": priority,
                "max_retries": 3,
            },
            user_id=1,  # Default user
        )

        logger.info(f"Created scraping job: {job.id} for {url}")
        logger.info(f"Job status: {job.status}")

        return job.id
    except Exception as e:
        logger.error(f"Error creating scraping job: {e}")
        return None
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Sample scraping script")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument(
        "--type", dest="website_type", default="generic", help="Website type"
    )
    parser.add_argument(
        "--priority", type=int, default=1, help="Job priority (1=low, 5=high)"
    )

    args = parser.parse_args()

    job_id = scrape_sample(args.url, args.website_type, args.priority)
    if job_id:
        logger.info(f"Scraping job created with ID: {job_id}")
        sys.exit(0)
    else:
        logger.error("Failed to create scraping job")
        sys.exit(1)


if __name__ == "__main__":
    main()