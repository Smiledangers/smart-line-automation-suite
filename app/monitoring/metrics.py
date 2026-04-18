"""Prometheus metrics for monitoring."""
from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Database metrics
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type", "table"],
)

db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
)

# Celery metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
)

celery_active_tasks = Gauge(
    "celery_active_tasks",
    "Number of active Celery tasks",
    ["task_name"],
)

# LINE API metrics
line_api_calls_total = Counter(
    "line_api_calls_total",
    "Total LINE API calls",
    ["method", "status"],
)

line_api_duration_seconds = Histogram(
    "line_api_duration_seconds",
    "LINE API call duration in seconds",
    ["method"],
)

# AI service metrics
ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI service requests",
    ["status"],
)

ai_tokens_used = Counter(
    "ai_tokens_used",
    "Total AI tokens used",
    ["model"],
)

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["model"],
)

# Scraping metrics
scraping_jobs_total = Counter(
    "scraping_jobs_total",
    "Total scraping jobs",
    ["status", "source"],
)

scraping_duration_seconds = Histogram(
    "scraping_duration_seconds",
    "Scraping job duration in seconds",
    ["source"],
)

# System metrics
active_users = Gauge(
    "active_users",
    "Number of active users",
)

line_users_total = Gauge(
    "line_users_total",
    "Total LINE users",
)

conversations_total = Gauge(
    "conversations_total",
    "Total AI conversations",
)

# Application info
app_info = Info("app", "Application information")


class MetricsMiddleware:
    """Middleware for collecting HTTP metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        start_time = time.time()

        # Custom send wrapper to capture status
        status_code = 200

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=path,
        ).observe(duration)


def track_db_query(query_type: str, table: str):
    """Decorator to track database query metrics."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    query_type=query_type,
                    table=table,
                ).observe(duration)
        return wrapper
    return decorator


def track_celery_task(task_name: str):
    """Decorator to track Celery task metrics."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            celery_active_tasks.labels(task_name=task_name).inc()
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(
                    task_name=task_name,
                    status="success",
                ).inc()
                return result
            except Exception as e:
                celery_tasks_total.labels(
                    task_name=task_name,
                    status="failure",
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration_seconds.labels(
                    task_name=task_name,
                ).observe(duration)
                celery_active_tasks.labels(task_name=task_name).dec()
        return wrapper
    return decorator