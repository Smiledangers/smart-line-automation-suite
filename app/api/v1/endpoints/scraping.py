"""
Scraping management endpoints with async support.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.schemas.scraping import (
    ScrapingJobCreate, 
    ScrapingJobResponse, 
    ScrapingJobUpdate,
    ScrapingResultResponse
)
from app.services.scraping_service import scraping_service
from app.tasks.scraping_tasks import run_scraping_job
from app.core.security import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


# Additional response models
class JobListResponse(BaseModel):
    """Response for job list endpoint."""
    jobs: list[ScrapingJobResponse]
    total: int


class ResultListResponse(BaseModel):
    """Response for results list endpoint."""
    results: list[ScrapingResultResponse]
    total: int


@router.post("/", response_model=ScrapingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_job(
    job_in: ScrapingJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScrapingJobResponse:
    """
    Create new scraping job.
    """
    try:
        job_data = job_in.model_dump()
        job = await scraping_service.create_job(db, job_data, current_user.id)
        
        # Start the scraping task asynchronously
        background_tasks.add_task(run_scraping_job, job.id)
        
        logger.info(f"Created scraping job {job.id} for user {current_user.id}")
        
        return ScrapingJobResponse(
            id=job.id,
            user_id=job.user_id,
            url=job.url,
            source=job.source,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=JobListResponse)
async def read_scraping_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobListResponse:
    """
    Retrieve scraping jobs.
    """
    try:
        if status_filter:
            jobs = await scraping_service.get_jobs_by_status(
                db, status_filter, skip=skip, limit=limit
            )
        else:
            jobs = await scraping_service.get_jobs(db, skip=skip, limit=limit)
        
        total = await scraping_service.job_service.count_jobs(db)
        
        return JobListResponse(
            jobs=[
                ScrapingJobResponse(
                    id=j.id,
                    user_id=j.user_id,
                    url=j.url,
                    source=j.source,
                    status=j.status,
                    priority=j.priority,
                    created_at=j.created_at.isoformat() if j.created_at else None,
                    started_at=j.started_at.isoformat() if j.started_at else None,
                    completed_at=j.completed_at.isoformat() if j.completed_at else None,
                )
                for j in jobs
            ],
            total=total,
        )
    except Exception as e:
        logger.error(f"Error reading scraping jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-jobs")
async def read_my_scraping_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobListResponse:
    """
    Get current user's scraping jobs.
    """
    try:
        jobs = await scraping_service.get_user_jobs(
            db, current_user.id, skip=skip, limit=limit
        )
        
        total = await scraping_service.job_service.count_jobs(db)
        
        return JobListResponse(
            jobs=[
                ScrapingJobResponse(
                    id=j.id,
                    user_id=j.user_id,
                    url=j.url,
                    source=j.source,
                    status=j.status,
                    priority=j.priority,
                    created_at=j.created_at.isoformat() if j.created_at else None,
                    started_at=j.started_at.isoformat() if j.started_at else None,
                    completed_at=j.completed_at.isoformat() if j.completed_at else None,
                )
                for j in jobs
            ],
            total=total,
        )
    except Exception as e:
        logger.error(f"Error reading user scraping jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=ScrapingJobResponse)
async def read_scraping_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScrapingJobResponse:
    """
    Get a specific scraping job by id.
    """
    try:
        job = await scraping_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=404, detail="Scraping job not found"
            )
        
        # Check ownership (or admin)
        if job.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this job"
            )
        
        return ScrapingJobResponse(
            id=job.id,
            user_id=job.user_id,
            url=job.url,
            source=job.source,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{job_id}", response_model=ScrapingJobResponse)
async def update_scraping_job(
    job_id: int,
    job_in: ScrapingJobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScrapingJobResponse:
    """
    Update a scraping job.
    """
    try:
        job_data = {k: v for k, v in job_in.model_dump().items() if v is not None}
        
        job = await scraping_service.update_job(db, job_id=job_id, job_data=job_data)
        if not job:
            raise HTTPException(
                status_code=404, detail="Scraping job not found"
            )
        
        return ScrapingJobResponse(
            id=job.id,
            user_id=job.user_id,
            url=job.url,
            source=job.source,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scraping_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a scraping job.
    """
    try:
        job = await scraping_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=404, detail="Scraping job not found"
            )
        
        # Check ownership (or admin)
        if job.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this job"
            )
        
        await scraping_service.delete_job(db, job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_scraping_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Cancel a scraping job.
    """
    try:
        job = await scraping_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=404, detail="Scraping job not found"
            )
        
        # Check ownership (or admin)
        if job.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Not authorized to cancel this job"
            )
        
        success = await scraping_service.cancel_job(db, job_id=job_id)
        if not success:
            raise HTTPException(
                status_code=400, detail="Job cannot be cancelled (already completed or cancelled)"
            )
        
        return {"message": "Scraping job cancelled", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/results", response_model=ResultListResponse)
async def get_scraping_results(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResultListResponse:
    """
    Get results for a scraping job.
    """
    try:
        job = await scraping_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=404, detail="Scraping job not found"
            )
        
        # Check ownership (or admin)
        if job.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this job"
            )
        
        results = await scraping_service.get_results(db, job_id=job_id, skip=skip, limit=limit)
        total = await scraping_service.result_service.get_result_count(db, job_id)
        
        return ResultListResponse(
            results=[
                ScrapingResultResponse(
                    id=r.id,
                    job_id=r.job_id,
                    url=r.url,
                    title=r.title,
                    content=r.content,
                    created_at=r.created_at.isoformat() if r.created_at else None,
                )
                for r in results
            ],
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scraping results: {e}")
        raise HTTPException(status_code=500, detail=str(e))