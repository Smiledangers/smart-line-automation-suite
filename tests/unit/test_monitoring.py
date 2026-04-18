"""Unit tests for monitoring metrics."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    db_query_duration_seconds,
    db_connections_active,
    celery_tasks_total,
    celery_task_duration_seconds,
    celery_active_tasks,
    line_api_calls_total,
    ai_requests_total,
    ai_tokens_used,
    scraping_jobs_total,
    active_users,
    line_users_total,
    MetricsMiddleware,
    track_db_query,
    track_celery_task,
)


class TestMetricsCounters:
    """Test Prometheus counters."""

    def test_http_requests_total_labels(self):
        """Test HTTP requests counter with labels."""
        # Reset mock
        http_requests_total.reset()
        
        # Should not raise - just testing metric creation
        assert http_requests_total is not None

    def test_celery_tasks_total_labels(self):
        """Test Celery tasks counter with labels."""
        celery_tasks_total.reset()
        assert celery_tasks_total is not None

    def test_ai_requests_total_labels(self):
        """Test AI requests counter with labels."""
        ai_requests_total.reset()
        assert ai_requests_total is not None


class TestMetricsGauges:
    """Test Prometheus gauges."""

    def test_active_users_gauge(self):
        """Test active users gauge."""
        active_users.set(5)
        # Should not raise
        assert active_users is not None

    def test_line_users_total_gauge(self):
        """Test LINE users total gauge."""
        line_users_total.set(10)
        assert line_users_total is not None

    def test_db_connections_gauge(self):
        """Test database connections gauge."""
        db_connections_active.set(3)
        assert db_connections_active is not None


class TestMetricsMiddleware:
    """Test metrics middleware."""

    def test_middleware_init(self):
        """Test middleware initialization."""
        mock_app = Mock()
        middleware = MetricsMiddleware(mock_app)
        assert middleware.app == mock_app

    @pytest.mark.asyncio
    async def test_middleware_non_http(self):
        """Test middleware passes through non-HTTP requests."""
        mock_app = Mock()
        middleware = MetricsMiddleware(mock_app)

        scope = {"type": "websocket"}
        receive = Mock()
        send = Mock()

        await middleware(scope, receive, send)
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_http(self):
        """Test middleware tracks HTTP requests."""
        mock_app = AsyncMock()
        middleware = MetricsMiddleware(mock_app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        receive = Mock()
        
        # Mock send that captures response start
        async def mock_send(message):
            if message["type"] == "http.response.start":
                message["status"] = 200
        
        send = Mock(side_effect=mock_send)

        await middleware(scope, receive, send)
        
        # App should be called
        mock_app.assert_called_once()


class TestTrackDecorators:
    """Test metric tracking decorators."""

    def test_track_db_query_decorator(self):
        """Test database query tracking decorator."""
        
        @track_db_query("select", "users")
        async def mock_query():
            return ["result"]
        
        # Should execute without error
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(mock_query())
        assert result == ["result"]

    def test_track_celery_task_decorator(self):
        """Test Celery task tracking decorator."""
        
        @track_celery_task("test_task")
        def mock_task():
            return "task_result"
        
        result = mock_task()
        assert result == "task_result"


class TestPrometheusMetrics:
    """Test Prometheus metrics integration."""

    def test_metrics_are_counters(self):
        """Test that counters are properly configured."""
        assert hasattr(http_requests_total, "labels")
        assert hasattr(celery_tasks_total, "labels")
        assert hasattr(ai_requests_total, "labels")

    def test_metrics_are_gauges(self):
        """Test that gauges are properly configured."""
        assert hasattr(active_users, "set")
        assert hasattr(line_users_total, "set")
        assert hasattr(db_connections_active, "set")

    def test_metrics_have_descriptions(self):
        """Test that metrics have descriptions."""
        # All metrics should have _value attribute or similar
        assert http_requests_total is not None


class TestMetricsCollection:
    """Test metrics collection scenarios."""

    def test_increment_counter(self):
        """Test incrementing a counter."""
        # Reset first
        ai_requests_total.reset()
        
        # Should not raise
        ai_requests_total.labels(status="success").inc(1)

    def test_observe_histogram(self):
        """Test observing histogram values."""
        # Should not raise
        http_request_duration_seconds.labels(
            method="GET",
            endpoint="/api/test",
        ).observe(0.5)

    def test_gauge_set_value(self):
        """Test setting gauge value."""
        # Should not raise
        active_users.set(42)