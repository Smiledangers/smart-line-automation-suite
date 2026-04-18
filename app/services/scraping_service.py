"""Scraping service layer with async database support."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult
from app.schemas.scraping import ScrapingJobCreate, ScrapingJobUpdate

logger = logging.getLogger(__name__)


class ScrapingJobService:
    """Service for scraping job management."""

    async def create_job(
        self, db: AsyncSession, job_data: dict, user_id: int
    ) -> ScrapingJob:
        """Create a new scraping job."""
        job_data = job_data.copy()
        job_data["user_id"] = user_id
        job = ScrapingJob(**job_data)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Created scraping job {job.id}: {job.url}")
        return job

    async def get_job(
        self, db: AsyncSession, job_id: int
    ) -> Optional[ScrapingJob]:
        """Get scraping job by ID."""
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_jobs(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        """Get list of scraping jobs with pagination."""
        result = await db.execute(
            select(ScrapingJob)
            .order_by(ScrapingJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_jobs(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        """Get jobs for a specific user."""
        result = await db.execute(
            select(ScrapingJob)
            .where(ScrapingJob.user_id == user_id)
            .order_by(ScrapingJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_jobs_by_status(
        self, db: AsyncSession, status: str, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        """Get jobs by status."""
        result = await db.execute(
            select(ScrapingJob)
            .where(ScrapingJob.status == status)
            .order_by(ScrapingJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_job(
        self, db: AsyncSession, job_id: int, job_data: dict
    ) -> Optional[ScrapingJob]:
        """Update scraping job."""
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        for field, value in job_data.items():
            if hasattr(job, field):
                setattr(job, field, value)

        job.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(job)
        return job

    async def delete_job(
        self, db: AsyncSession, job_id: int
    ) -> bool:
        """Delete scraping job."""
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False

        await db.delete(job)
        await db.commit()
        return True

    async def cancel_job(
        self, db: AsyncSession, job_id: int
    ) -> bool:
        """Cancel scraping job."""
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False

        if job.status in ["completed", "failed", "cancelled"]:
            return False

        job.status = "cancelled"
        job.updated_at = datetime.utcnow()
        await db.commit()
        return True

    async def count_jobs(
        self, db: AsyncSession, status: Optional[str] = None
    ) -> int:
        """Count total jobs, optionally filtered by status."""
        query = select(func.count(ScrapingJob.id))
        if status:
            query = query.where(ScrapingJob.status == status)
        result = await db.execute(query)
        return result.scalar() or 0

    async def get_pending_jobs(
        self, db: AsyncSession, limit: int = 10
    ) -> List[ScrapingJob]:
        """Get pending jobs for processing."""
        result = await db.execute(
            select(ScrapingJob)
            .where(ScrapingJob.status == "pending")
            .order_by(ScrapingJob.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())


class ScrapingResultService:
    """Service for scraping result management."""

    async def get_results(
        self, db: AsyncSession, job_id: int, skip: int = 0, limit: int = 100
    ) -> List[ScrapingResult]:
        """Get scraping results for a job with pagination."""
        result = await db.execute(
            select(ScrapingResult)
            .where(ScrapingResult.job_id == job_id)
            .order_by(ScrapingResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_result(
        self, db: AsyncSession, result_id: int
    ) -> Optional[ScrapingResult]:
        """Get a specific result by ID."""
        result = await db.execute(
            select(ScrapingResult).where(ScrapingResult.id == result_id)
        )
        return result.scalar_one_or_none()

    async def create_result(
        self, db: AsyncSession, job_id: int, result_data: dict
    ) -> ScrapingResult:
        """Create a new scraping result."""
        result = ScrapingResult(
            job_id=job_id,
            url=result_data.get("url"),
            title=result_data.get("title"),
            content=result_data.get("content"),
            metadata=result_data.get("metadata", {}),
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)
        logger.info(f"Created result {result.id} for job {job_id}")
        return result

    async def get_result_count(
        self, db: AsyncSession, job_id: int
    ) -> int:
        """Get count of results for a job."""
        result = await db.execute(
            select(func.count(ScrapingResult.id)).where(
                ScrapingResult.job_id == job_id
            )
        )
        return result.scalar() or 0

    async def delete_result(
        self, db: AsyncSession, result_id: int
    ) -> bool:
        """Delete a result."""
        result = await db.execute(
            select(ScrapingResult).where(ScrapingResult.id == result_id)
        )
        scrap_result = result.scalar_one_or_none()
        if not scrap_result:
            return False

        await db.delete(scrap_result)
        await db.commit()
        return True


class ScrapingService:
    """Main scraping service that aggregates sub-services."""

    def __init__(self):
        self.job_service = ScrapingJobService()
        self.result_service = ScrapingResultService()

    # Delegate methods for backward compatibility
    async def create_job(
        self, db: AsyncSession, job_data: dict, user_id: int
    ) -> ScrapingJob:
        return await self.job_service.create_job(db, job_data, user_id)

    async def get_job(
        self, db: AsyncSession, job_id: int
    ) -> Optional[ScrapingJob]:
        return await self.job_service.get_job(db, job_id)

    async def get_jobs(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        return await self.job_service.get_jobs(db, skip, limit)

    async def get_user_jobs(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        return await self.job_service.get_user_jobs(db, user_id, skip, limit)

    async def get_jobs_by_status(
        self, db: AsyncSession, status: str, skip: int = 0, limit: int = 100
    ) -> List[ScrapingJob]:
        return await self.job_service.get_jobs_by_status(db, status, skip, limit)

    async def update_job(
        self, db: AsyncSession, job_id: int, job_data: dict
    ) -> Optional[ScrapingJob]:
        return await self.job_service.update_job(db, job_id, job_data)

    async def delete_job(
        self, db: AsyncSession, job_id: int
    ) -> bool:
        return await self.job_service.delete_job(db, job_id)

    async def cancel_job(
        self, db: AsyncSession, job_id: int
    ) -> bool:
        return await self.job_service.cancel_job(db, job_id)

    async def get_results(
        self, db: AsyncSession, job_id: int, skip: int = 0, limit: int = 100
    ) -> List[ScrapingResult]:
        return await self.result_service.get_results(db, job_id, skip, limit)

    async def create_result(
        self, db: AsyncSession, job_id: int, result_data: dict
    ) -> ScrapingResult:
        return await self.result_service.create_result(db, job_id, result_data)

    async def get_result_count(
        self, db: AsyncSession, job_id: int
    ) -> int:
        return await self.result_service.get_result_count(db, job_id)


scraping_service = ScrapingService()