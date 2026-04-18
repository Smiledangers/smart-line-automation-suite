"""Celery application configuration, tasks, and beat schedule."""
import logging
import time
from typing import Any, Dict, Optional
from celery import Celery, Task
from celery.exceptions import MaxRetriesExceededError
from celery.signals import task_success, task_failure, task_retry
from celery.schedules import crontab

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
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    beat_schedule={
        # Daily tasks
        "cleanup-old-data": {
            "task": "app.tasks.celery_app.cleanup_old_data",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "send-daily-digest": {
            "task": "app.tasks.celery_app.send_all_daily_digests",
            "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
        },
        "health-check": {
            "task": "app.tasks.celery_app.health_check_task",
            "schedule": 300,  # Every 5 minutes
        },
        # Weekly tasks
        "cleanup-old-logs": {
            "task": "app.tasks.celery_app.cleanup_old_logs",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
        },
        # Monthly tasks
        "generate-monthly-report": {
            "task": "app.tasks.celery_app.generate_monthly_report",
            "schedule": crontab(hour=1, minute=0, day_of_month=1),  # Monthly on 1st at 1 AM
        },
    },
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
        self.state = "closed"

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


# ==================== MAIN PROCESSING TASKS ====================

@app.task(bind=True, base=BaseTask, max_retries=3, default_retry_delay=60)
def process_line_message(self, user_id: str, message: str) -> Dict[str, Any]:
    """Process incoming LINE message asynchronously."""
    logger.info(f"Processing LINE message from user {user_id}: {message}")

    try:
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
    """Process scraping job asynchronously."""
    logger.info(f"Processing scraping job {job_id} for URL: {url}")

    try:
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
    """Process AI chat message asynchronously."""
    logger.info(f"Processing AI chat for user {user_id}, conversation {conversation_id}")

    try:
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


# ==================== SCHEDULED TASKS ====================

@app.task(bind=True, base=BaseTask)
def cleanup_old_data(self) -> Dict[str, Any]:
    """Clean up old data from database."""
    logger.info("Running cleanup old data task")
    
    try:
        from datetime import datetime, timedelta
        from app.core.database import SessionLocal
        from app.Models.ai_conversation import AIMessage
        
        db = SessionLocal()
        try:
            # Delete messages older than 90 days
            cutoff = datetime.utcnow() - timedelta(days=90)
            result = db.query(AIMessage).filter(AIMessage.created_at < cutoff).delete()
            db.commit()
            logger.info(f"Deleted {result} old AI messages")
            return {"status": "success", "deleted_count": result}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}")
        return {"status": "error", "error": str(e)}


@app.task(bind=True, base=BaseTask)
def send_all_daily_digests(self) -> Dict[str, Any]:
    """Send daily digest to all active users."""
    logger.info("Running send daily digest task")
    
    try:
        from app.core.database import SessionLocal
        from app.Models.user import User
        from app.tasks.notification_tasks import send_daily_digest
        
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_active == True).all()
            for user in users:
                send_daily_digest.delay(user.id)
            logger.info(f"Queued daily digests for {len(users)} users")
            return {"status": "success", "users_count": len(users)}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in send_all_daily_digests: {e}")
        return {"status": "error", "error": str(e)}


@app.task(bind=True, base=BaseTask)
def health_check_task(self) -> Dict[str, Any]:
    """Periodic health check task."""
    logger.info("Running health check task")
    
    try:
        # Check database
        from app.core.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Check redis
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        
        logger.info("Health check passed")
        return {"status": "success", "database": "ok", "redis": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


@app.task(bind=True, base=BaseTask)
def cleanup_old_logs(self) -> Dict[str, Any]:
    """Clean up old log files."""
    logger.info("Running cleanup old logs task")
    
    try:
        import os
        from datetime import datetime, timedelta
        
        log_dir = "logs"
        if os.path.exists(log_dir):
            cutoff = datetime.now() - timedelta(days=30)
            count = 0
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    if datetime.fromtimestamp(os.path.getmtime(filepath)) < cutoff:
                        os.remove(filepath)
                        count += 1
            logger.info(f"Deleted {count} old log files")
            return {"status": "success", "deleted_count": count}
        return {"status": "success", "deleted_count": 0}
    except Exception as e:
        logger.error(f"Error in cleanup_old_logs: {e}")
        return {"status": "error", "error": str(e)}


@app.task(bind=True, base=BaseTask)
def generate_monthly_report(self) -> Dict[str, Any]:
    """Generate monthly system report."""
    logger.info("Running generate monthly report task")
    
    try:
        from datetime import datetime, timedelta
        from app.core.database import SessionLocal
        from app.Models.user import User
        from app.Models.scraping_job import ScrapingJob
        from app.Models.ai_conversation import AIConversation
        
        db = SessionLocal()
        try:
            # Get stats for last month
            start_date = datetime.utcnow() - timedelta(days=30)
            
            user_count = db.query(User).count()
            scraping_jobs = db.query(ScrapingJob).filter(
                ScrapingJob.created_at >= start_date
            ).all()
            completed_jobs = len([j for j in scraping_jobs if j.status == "completed"])
            failed_jobs = len([j for j in scraping_jobs if j.status == "failed"])
            
            ai_conversations = db.query(AIConversation).filter(
                AIConversation.created_at >= start_date
            ).count()
            
            report = {
                "period": f"{start_date.date()} to {datetime.utcnow().date()}",
                "total_users": user_count,
                "new_scraping_jobs": len(scraping_jobs),
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": round(completed_jobs / len(scraping_jobs) * 100, 2) if scraping_jobs else 0,
                "ai_conversations": ai_conversations,
            }
            
            logger.info(f"Monthly report generated: {report}")
            return {"status": "success", "report": report}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in generate_monthly_report: {e}")
        return {"status": "error", "error": str(e)}


# ==================== HELPER METHODS ====================

def _call_line_api(self, user_id: str, message: str) -> str:
    """Call LINE API to process message."""
    from app.services.line_service import line_service
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get or create LINE user
        line_user = line_service.user_service.get_or_create_line_user(db, user_id)
        
        # Process message through AI service
        from app.services.ai_service import ai_service
        import asyncio
        result = asyncio.run(ai_service.chat(
            db, 
            user_id=line_user.user_id or 0, 
            message=message
        ))
        
        return result.get("message", "Message processed")
    except Exception as e:
        logger.error(f"Error calling LINE API: {e}")
        raise
    finally:
        db.close()


def _call_scraper(self, job_id: int, url: str) -> Dict[str, Any]:
    """Call scraper to process URL."""
    from app.services.scraping_service import scraping_service
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get job
        job = scraping_service.job_service.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # TODO: Actually scrape the URL using Botsaurus
        # For now, return mock data
        result_data = {
            "job_id": job_id,
            "url": url,
            "data": [{"title": "Sample", "content": "Sample content"}],
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        # Save result
        scraping_service.result_service.create_result(
            db, job_id, {"url": url, "title": "Scraped page", "content": "Data extracted"}
        )
        
        # Update job as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        return result_data
    except Exception as e:
        logger.error(f"Error calling scraper: {e}")
        # Update job as failed
        try:
            job = scraping_service.job_service.get_job(db, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass
        raise
    finally:
        db.close()


def _call_ai(self, user_id: int, message: str, conversation_id: int) -> str:
    """Call AI service to process message."""
    from app.services.ai_service import ai_service
    from app.core.database import SessionLocal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        result = await ai_service.chat(
            db,
            user_id=user_id,
            message=message,
            conversation_id=conversation_id if conversation_id > 0 else None
        )
        return result.get("message", "AI response generated")
    except Exception as e:
        logger.error(f"Error calling AI service: {e}")
        raise
    finally:
        db.close()