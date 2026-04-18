"""Scraping Result model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.Models.base import Base


class ScrapingResult(Base):
    """Scraping result model."""

    __tablename__ = "scraping_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(2048), nullable=True)
    title = Column(String(512), nullable=True)
    content = Column(Text, nullable=True)
    result_result_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("ScrapingJob", back_populates="results")