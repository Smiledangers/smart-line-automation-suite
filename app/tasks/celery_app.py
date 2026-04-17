"""Celery application configuration and tasks."""
import logging
import time
from typing import Any, Dict, Optional
from celery import Celery, Task
from celery.exceptions import MaxRetriesExceededError
from celery.signals import task_success, task_failure, task_retry

from app.core.config import get_settings

settings = get_settings()

# Configure Celery
app = Celery(
    "smart_line_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.celery_app",
    ],
)

# Celery configuration
app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configure logging
logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise e


circuit_breaker = CircuitBreaker(
    failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
)


class BaseTask(Task):
    """Base task class with logging and error handling."""

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        logger.info(f"Task {self.name} [{task_id}] succeeded with result: {retval}")

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        logger.error(f"Task {self.name} [{task_id}] failed with exception: {exc}")

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        logger.warning(f"Task {self.name} [{task_id}] retrying due to: {exc}")


@app.task(bind=True, base=BaseTask, max_retries=3, default_retry_delay=60)
def process_line_message(self, user_id: str, message: str) -> Dict[str, Any]:
    """
    Process incoming LINE message asynchronously.

    Args:
        user_id: LINE user ID (primitive str)
        message: Message text (primitive str)

    Returns:
        Dict with processing result
    """
    logger.info(f"Processing LINE message from user {user_id}: {message}")

    try:
        # Simulate processing - replace with actual LINE AI processing
        # Use circuit breaker for external API calls
        result = circuit_breaker.call(self._call_line_api, user_id, message)

        return {
            "status": "success",
            "user_id": user_id,
            "message": message,
            "result": result,
        }
    except Exception as exc:
        logger.error(f"Error processing LINE message: {exc}")
        try:
            self.retry(exc=exc, retry_backoff=True)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for LINE message processing")
            return {"status": "failed", "error": str(exc)}


@app.task(bind=True, base=BaseTask, max_retries=3, default_retry_delay=180)
def process_scraping_job(self, job_id: int, url: str) -> Dict[str, Any]:
    """
    Process scraping job asynchronously.

    Args:
        job_id: Job ID (primitive int)
        url: URL to scrape (primitive str)

    Returns:
        Dict with scraping result
    """
    logger.info(f"Processing scraping job {job_id} for URL: {url}")

    try:
        # Simulate scraping - replace with actual Botsaurus scraping
        # Use circuit breaker for external API calls
        result = circuit_breaker.call(self._call_scraper, job_id, url)

        return {
            "status": "success",
            "job_id": job_id,
            "url": url,
            "result": result,
        }
    except Exception as exc:
        logger.error(f"Error processing scraping job: {exc}")
        try:
            self.retry(exc=exc, retry_backoff=True)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for scraping job {job_id}")
            return {"status": "failed", "error": str(exc)}


@app.task(bind=True, base=BaseTask, max_retries=3, default_retry_delay=30)
def process_ai_chat(self, user_id: int, message: str, conversation_id: int) -> Dict[str, Any]:
    """
    Process AI chat message asynchronously.

    Args:
        user_id: User ID (primitive int)
        message: Chat message (primitive str)
        conversation_id: Conversation ID (primitive int)

    Returns:
        Dict with AI response
    """
    logger.info(f"Processing AI chat for user {user_id}, conversation {conversation_id}")

    try:
        # Simulate AI processing - replace with actual LangGraph agent
        # Use circuit breaker for external API calls
        result = circuit_breaker.call(self._call_ai, user_id, message, conversation_id)

        return {
            "status": "success",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "response": result,
        }
    except Exception as exc:
        logger.error(f"Error processing AI chat: {exc}")
        try:
            self.retry(exc=exc, retry_backoff=True)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for AI chat")
            return {"status": "failed", "error": str(exc)}


# Helper methods (placeholders for actual implementation)
def _call_line_api(self, user_id: str, message: str) -> str:
    """Placeholder for LINE API call."""
    # Replace with actual line_service.process_message() call
    return f"Processed: {message}"


def _call_scraper(self, job_id: int, url: str) -> Dict[str, Any]:
    """Placeholder for scraper call."""
    # Replace with actual scraping logic using Botsaurus
    return {"job_id": job_id, "url": url, "data": []}


def _call_ai(self, user_id: int, message: str, conversation_id: int) -> str:
    """Placeholder for AI API call."""
    # Replace with actual LangGraph agent call
    return f"AI response to: {message}"