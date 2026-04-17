"""
Scraping management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

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

router = APIRouter()


@router.post("/", response_model=ScrapingJobResponse)
def create_scraping_job(
    job_in: ScrapingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create new scraping job.
    """
    job = scraping_service.create_job(db, job_in, current_user.id)
    # Start the scraping task asynchronously
    background_tasks.add_task(run_scraping_job, job.id)
    return job


@router.get("/", response_model=List[ScrapingJobResponse])
def read_scraping_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve scraping jobs.
    """
    jobs = scraping_service.get_jobs(db, skip=skip, limit=limit)
    return jobs


@router.get("/{job_id}", response_model=ScrapingJobResponse)
def read_scraping_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific scraping job by id.
    """
    job = scraping_service.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return job


@router.put("/{job_id}", response_model=ScrapingJobResponse)
def update_scraping_job(
    job_id: int,
    job_in: ScrapingJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a scraping job.
    """
    job = scraping_service.update_job(db, job_id=job_id, job_in=job_in)
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return job


@router.delete("/{job_id}", response_model=ScrapingJobResponse)
def delete_scraping_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a scraping job.
    """
    job = scraping_service.delete_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return job


@router.post("/{job_id}/cancel")
def cancel_scraping_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cancel a scraping job.
    """
    success = scraping_service.cancel_job(db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return {"message": "Scraping job cancelled"}


@router.get("/{job_id}/results", response_model=List[ScrapingResultResponse])
def get_scraping_results(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get results for a scraping job.
    """
    results = scraping_service.get_results(db, job_id=job_id, skip=skip, limit=limit)
    return results