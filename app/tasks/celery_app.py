# app/tasks/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smart_line_automation_suite",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    timezone="Asia/Taipei",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={}
)

celery_app.autodiscover_tasks(["app.tasks"], force=True)