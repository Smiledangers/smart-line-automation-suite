"""Retry middleware with exponential backoff."""
import logging
import time
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryMiddleware:
    """Middleware for retrying failed requests."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.stats = {"retries": 0, "successes": 0, "failures": 0}

    def process_request(self, request):
        """Add retry metadata to request."""
        request._retry_count = 0
        request._retry_delay = 0
        return request

    def should_retry(self, response) -> bool:
        """Determine if request should be retried."""
        if not response:
            return True
        # Retry on server errors or specific status codes
        return response.status_code >= 500

    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        import random

        delay = min(
            self.base_delay * (self.exponential_base ** retry_count), self.max_delay
        )
        # Add random jitter (±25%)
        jitter = delay * 0.25 * random.uniform(-1, 1)
        return delay + jitter

    def get_stats(self) -> dict:
        """Get retry statistics."""
        return self.stats.copy()


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying functions with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (backoff ** attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}. "
                            f"Waiting {sleep_time:.2f}s"
                        )
                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}"
                        )
            raise last_exception

        return wrapper

    return decorator


class RateLimitMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(self, requests_per_second: float = 1.0, burst_size: int = 5):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.token_bucket = burst_size

    def process_request(self, request):
        """Apply rate limiting to request."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        # Refill tokens
        self.token_bucket = min(
            self.burst_size, self.token_bucket + elapsed * self.requests_per_second
        )

        if self.token_bucket < 1:
            # Wait for token to be available
            wait_time = (1 - self.token_bucket) * self.min_interval
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            self.token_bucket = 0
        else:
            self.token_bucket -= 1

        self.last_request_time = time.time()
        return request

    def process_response(self, response):
        """Process response."""
        return response


class ErrorLoggingMiddleware:
    """Middleware for logging errors."""

    def __init__(self):
        self.errors = []
        self.error_count = 0

    def process_request(self, request):
        """Log request."""
        logger.debug(f"Request: {request.url}")
        return request

    def process_response(self, response):
        """Log response status."""
        if response.status_code >= 400:
            logger.warning(f"Error response: {response.status_code} for {response.url}")
            self.errors.append({"url": response.url, "status": response.status_code})
            self.error_count += 1
        return response

    def process_exception(self, exception):
        """Log exception."""
        logger.error(f"Request exception: {exception}")
        self.errors.append({"exception": str(exception)})
        self.error_count += 1

    def get_errors(self) -> list:
        """Get logged errors."""
        return self.errors.copy()

    def get_error_count(self) -> int:
        """Get error count."""
        return self.error_count