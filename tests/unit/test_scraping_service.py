"""Unit tests for scraping service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.scraping_service import (
    ScrapingJobService,
    ScrapingResultService,
    ScrapingService,
)
from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult


@pytest.fixture
def sample_job_data():
    """Sample scraping job data."""
    return {
        "url": "https://example.com",
        "source": "example",
        "status": "pending",
        "priority": 1,
    }


@pytest.fixture
def sample_result_data():
    """Sample scraping result data."""
    return {
        "url": "https://example.com/page1",
        "title": "Example Page",
        "content": "This is the content.",
        "metadata": {"author": "Test"},
    }


class TestScrapingJobService:
    """Test scraping job service."""

    @pytest.mark.asyncio
    async def test_create_job(self, db_session, sample_job_data):
        """Test creating a new scraping job."""
        service = ScrapingJobService()
        job = await service.create_job(db_session, sample_job_data, user_id=1)

        assert job.id is not None
        assert job.url == sample_job_data["url"]
        assert job.status == "pending"
        assert job.user_id == 1

    @pytest.mark.asyncio
    async def test_get_job(self, db_session, sample_job_data):
        """Test getting a job by ID."""
        service = ScrapingJobService()
        created_job = await service.create_job(
            db_session, sample_job_data, user_id=1
        )

        job = await service.get_job(db_session, created_job.id)
        assert job is not None
        assert job.id == created_job.id

    @pytest.mark.asyncio
    async def test_get_jobs(self, db_session, sample_job_data):
        """Test getting multiple jobs."""
        service = ScrapingJobService()

        # Create multiple jobs
        for i in range(3):
            await service.create_job(
                db_session,
                {**sample_job_data, "url": f"https://example{i}.com"},
                user_id=1,
            )

        jobs = await service.get_jobs(db_session)
        assert len(jobs) >= 3

    @pytest.mark.asyncio
    async def test_update_job(self, db_session, sample_job_data):
        """Test updating a job."""
        service = ScrapingJobService()
        job = await service.create_job(db_session, sample_job_data, user_id=1)

        updated = await service.update_job(
            db_session, job.id, {"status": "running"}
        )
        assert updated.status == "running"

    @pytest.mark.asyncio
    async def test_cancel_job(self, db_session, sample_job_data):
        """Test cancelling a job."""
        service = ScrapingJobService()
        job = await service.create_job(db_session, sample_job_data, user_id=1)

        result = await service.cancel_job(db_session, job.id)
        assert result is True

        # Verify cancelled
        cancelled_job = await service.get_job(db_session, job.id)
        assert cancelled_job.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_completed_job_fails(self, db_session, sample_job_data):
        """Test that cancelling a completed job fails."""
        service = ScrapingJobService()
        job = await service.create_job(db_session, sample_job_data, user_id=1)

        # Mark as completed first
        await service.update_job(db_session, job.id, {"status": "completed"})

        # Try to cancel
        result = await service.cancel_job(db_session, job.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_jobs_by_status(self, db_session, sample_job_data):
        """Test getting jobs filtered by status."""
        service = ScrapingJobService()

        # Create jobs with different statuses
        for i in range(3):
            await service.create_job(
                db_session,
                {**sample_job_data, "url": f"https://example{i}.com"},
                user_id=1,
            )

        pending_jobs = await service.get_jobs_by_status(db_session, "pending")
        assert all(j.status == "pending" for j in pending_jobs)

    @pytest.mark.asyncio
    async def test_count_jobs(self, db_session, sample_job_data):
        """Test counting jobs."""
        service = ScrapingJobService()

        await service.create_job(db_session, sample_job_data, user_id=1)
        await service.create_job(db_session, sample_job_data, user_id=1)

        count = await service.count_jobs(db_session)
        assert count >= 2

    @pytest.mark.asyncio
    async def test_get_user_jobs(self, db_session, sample_job_data):
        """Test getting jobs for a specific user."""
        service = ScrapingJobService()

        await service.create_job(db_session, sample_job_data, user_id=1)
        await service.create_job(db_session, sample_job_data, user_id=2)

        user1_jobs = await service.get_user_jobs(db_session, user_id=1)
        assert all(j.user_id == 1 for j in user1_jobs)


class TestScrapingResultService:
    """Test scraping result service."""

    @pytest.mark.asyncio
    async def test_create_result(self, db_session, sample_job_data, sample_result_data):
        """Test creating a scraping result."""
        job_service = ScrapingJobService()
        job = await job_service.create_job(db_session, sample_job_data, user_id=1)

        result_service = ScrapingResultService()
        result = await result_service.create_result(db_session, job.id, sample_result_data)

        assert result.id is not None
        assert result.job_id == job.id
        assert result.title == sample_result_data["title"]

    @pytest.mark.asyncio
    async def test_get_results(self, db_session, sample_job_data, sample_result_data):
        """Test getting results for a job."""
        job_service = ScrapingJobService()
        job = await job_service.create_job(db_session, sample_job_data, user_id=1)

        result_service = ScrapingResultService()
        await result_service.create_result(db_session, job.id, sample_result_data)

        results = await result_service.get_results(db_session, job.id)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_result_count(self, db_session, sample_job_data, sample_result_data):
        """Test getting result count for a job."""
        job_service = ScrapingJobService()
        job = await job_service.create_job(db_session, sample_job_data, user_id=1)

        result_service = ScrapingResultService()
        await result_service.create_result(db_session, job.id, sample_result_data)
        await result_service.create_result(db_session, job.id, sample_result_data)

        count = await result_service.get_result_count(db_session, job.id)
        assert count == 2


class TestScrapingService:
    """Test main scraping service."""

    @pytest.mark.asyncio
    async def test_scraping_service_delegates(self, db_session, sample_job_data):
        """Test that ScrapingService delegates to sub-services."""
        service = ScrapingService()

        # Should delegate to job_service
        job = await service.create_job(db_session, sample_job_data, user_id=1)
        assert job.id is not None

        # Should delegate to result_service
        fetched_job = await service.get_job(db_session, job.id)
        assert fetched_job.id == job.id