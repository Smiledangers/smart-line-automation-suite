"""Scraping tasks - alias module."""
from app.tasks.celery_app import celery_app

# Re-export task functions
run_scraping_job = celery_app.process_scraping_job