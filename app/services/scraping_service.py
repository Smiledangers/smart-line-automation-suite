"""Scraping service layer for scraping pipeline management."""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult
from app.schemas.scraping import ScrapingJobCreate, ScrapingJobUpdate

logger = logging.getLogger(__name__)

class ScrapingJobService:
    """Service for scraping job management."""
    
    def create_job(self, db: Session, job_in: dict, user_id: int) -> ScrapingJob:
        """Create a new scraping job."""
        job_data = job_in.copy()
        job_data["user_id"] = user_id
        job = ScrapingJob(**job_data)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    def get_job(self, db: Session, job_id: int) -> Optional[ScrapingJob]:
        """Get scraping job by ID."""
        return db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    
    def get_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        """Get list of scraping jobs with pagination."""
        return db.query(ScrapingJob).offset(skip).limit(limit).all()
    
    def update_job(self, db: Session, job_id: int, job_in: dict) -> Optional[ScrapingJob]:
        """Update scraping job."""
        job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if not job:
            return None
        
        for field, value in job_in.items():
            if hasattr(job, field):
                setattr(job, field, value)
        
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
    
    def delete_job(self, db: Session, job_id: int) -> bool:
        """Delete scraping job."""
        job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if not job:
            return False
        
        db.delete(job)
        db.commit()
        return True
    
    def cancel_job(self, db: Session, job_id: int) -> bool:
        """Cancel scraping job."""
        job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if not job:
            return False
        
        if job.status in ["completed", "failed", "cancelled"]:
            return False
        
        job.status = "cancelled"
        job.updated_at = datetime.utcnow()
        db.commit()
        return True

class ScrapingResultService:
    """Service for scraping result management."""
    
    def get_results(self, db: Session, job_id: int, skip: int = 0, limit: int = 100) -> List[ScrapingResult]:
        """Get scraping results for a job with pagination."""
        return db.query(ScrapingResult)\
                .filter(ScrapingResult.job_id == job_id)\
                .offset(skip)\
                .limit(limit)\
                .all()
    
    def create_result(self, db: Session, job_id: int, result_data: dict) -> ScrapingResult:
        """Create a new scraping result."""
        result = ScrapingResult(
            job_id=job_id,
            url=result_data.get("url"),
            title=result_data.get("title"),
            content=result_data.get("content"),
            metadata=result_data.get("metadata", {})
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    
    def get_result_count(self, db: Session, job_id: int) -> int:
        """Get count of results for a job."""
        return db.query(ScrapingResult).filter(ScrapingResult.job_id == job_id).count()

class ScrapingService:
    """Main scraping service that aggregates sub-services."""
    
    def __init__(self):
        self.job_service = ScrapingJobService()
        self.result_service = ScrapingResultService()
    
    # Delegate methods for backward compatibility
    def create_job(self, db: Session, job_in: dict, user_id: int) -> ScrapingJob:
        return self.job_service.create_job(db, job_in, user_id)
    
    def get_job(self, db: Session, job_id: int) -> Optional[ScrapingJob]:
        return self.job_service.get_job(db, job_id)
    
    def get_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        return self.job_service.get_jobs(db, skip, limit)
    
    def update_job(self, db: Session, job_id: int, job_in: dict) -> Optional[ScrapingJob]:
        return self.job_service.update_job(db, job_id, job_in)
    
    def delete_job(self, db: Session, job_id: int) -> bool:
        return self.job_service.delete_job(db, job_id)
    
    def cancel_job(self, db: Session, job_id: int) -> bool:
        return self.job_service.cancel_job(db, job_id)
    
    def get_results(self, db: Session, job_id: int, skip: int = 0, limit: int = 100) -> List[ScrapingResult]:
        return self.result_service.get_results(db, job_id, skip, limit)
    
    def create_result(self, db: Session, job_id: int, result_data: dict) -> ScrapingResult:
        return self.result_service.create_result(db, job_id, result_data)
    
    def get_result_count(self, db: Session, job_id: int) -> int:
        return self.result_service.get_result_count(db, job_id)

scraping_service = ScrapingService()