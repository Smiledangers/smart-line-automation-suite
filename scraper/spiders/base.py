"""Base spider with retry and error handling."""
import logging
import time
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseSpider(ABC):
    """Base spider class with common functionality."""

    def __init__(
        self,
        name: str,
        max_retries: int = 3,
        retry_delay: int = 5,
        rate_limit: float = 1.0,
        timeout: int = 30,
    ):
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.stats = {
            "pages_scraped": 0,
            "items_extracted": 0,
            "errors": 0,
            "retries": 0,
            "start_time": None,
            "end_time": None,
        }

    def _rate_limit_wait(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.stats["retries"] += 1
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded: {e}")
        raise last_exception

    @abstractmethod
    def parse(self, response) -> List[Dict[str, Any]]:
        """Parse the response and extract items."""
        pass

    @abstractmethod
    def start_requests(self):
        """Generate initial requests."""
        pass

    def run(self):
        """Run the spider."""
        self.stats["start_time"] = datetime.utcnow()
        logger.info(f"Starting spider: {self.name}")

        try:
            for request in self.start_requests():
                self._rate_limit_wait()
                try:
                    result = self._retry_with_backoff(self.parse, request)
                    if result:
                        self.stats["items_extracted"] += len(result)
                        self.stats["pages_scraped"] += 1
                        logger.info(f"Extracted {len(result)} items")
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Error processing request: {e}")

        except Exception as e:
            logger.error(f"Spider error: {e}")
        finally:
            self.stats["end_time"] = datetime.utcnow()
            self._log_stats()

    def _log_stats(self):
        """Log spider statistics."""
        duration = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()
        logger.info(
            f"Spider {self.name} completed: "
            f"{self.stats['pages_scraped']} pages, "
            f"{self.stats['items_extracted']} items, "
            f"{self.stats['errors']} errors, "
            f"{self.stats['retries']} retries, "
            f"{duration:.2f}s"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get spider statistics."""
        return self.stats.copy()


class SpiderMiddleware:
    """Base middleware for spider."""

    def process_request(self, request):
        """Process request before sending."""
        return request

    def process_response(self, response):
        """Process response before parsing."""
        return response

    def process_item(self, item):
        """Process extracted item."""
        return item


class SpiderPipeline:
    """Base pipeline for processing items."""

    def open_spider(self, spider):
        """Called when spider opens."""
        pass

    def close_spider(self, spider):
        """Called when spider closes."""
        pass

    def process_item(self, item, spider):
        """Process extracted item."""
        return item