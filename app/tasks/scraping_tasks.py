"""Scraping tasks - alias module."""
from app.tasks.celery_app import app as celery_app

# Re-export task functions
run_scraping_job = celery_app.process_scraping_job