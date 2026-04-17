"""Scraping job schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl


class ScrapingJobBase(BaseModel):
    url: HttpUrl
    website_type: Optional[str] = "generic"
    priority: Optional[int] = 1
    max_retries: Optional[int] = 3


class ScrapingJobCreate(ScrapingJobBase):
    pass


class ScrapingJobUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    error_message: Optional[str] = None


class ScrapingJobInDB(ScrapingJobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    status: str
    retry_count: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScrapingJobResponse(ScrapingJobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    status: str
    retry_count: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScrapingJobList(BaseModel):
    jobs: list[ScrapingJobResponse]
    total: int


class ScrapingResultBase(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None


class ScrapingResultCreate(ScrapingResultBase):
    pass


class ScrapingResultResponse(ScrapingResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class ScrapingResultList(BaseModel):
    results: list[ScrapingResultResponse]
    total: int