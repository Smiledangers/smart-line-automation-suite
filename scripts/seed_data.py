"""Seed test data script."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import User
from app.models.line_user import LINEUser
from app.models.scraping_job import ScrapingJob
from app.models.scraping_job import ScrapingResult
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_users(count: int = 5):
    """Seed test users."""
    db = SessionLocal()
    try:
        for i in range(count):
            email = f"user{i+1}@example.com"
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                user = User(
                    email=email,
                    hashed_password=pwd_context.hash("password123"),
                    full_name=f"Test User {i+1}",
                    is_active=True,
                )
                db.add(user)
        db.commit()
        logger.info(f"Seeded {count} users")
    finally:
        db.close()


def seed_line_users(count: int = 10):
    """Seed test LINE users."""
    db = SessionLocal()
    try:
        users = db.query(User).limit(count).all()
        for i, user in enumerate(users):
            line_id = f"U{i:08x}"
            existing = db.query(LINEUser).filter(LINEUser.line_user_id == line_id).first()
            if not existing:
                line_user = LINEUser(
                    line_user_id=line_id,
                    user_id=user.id,
                    display_name=f"LINE User {i+1}",
                    picture_url=f"https://example.com/avatar{i}.jpg",
                    is_active=True,
                )
                db.add(line_user)
        db.commit()
        logger.info(f"Seeded {len(users)} LINE users")
    finally:
        db.close()


def seed_scraping_jobs(count: int = 10):
    """Seed test scraping jobs."""
    db = SessionLocal()
    try:
        statuses = ["pending", "running", "completed", "failed"]
        for i in range(count):
            job = ScrapingJob(
                user_id=1,
                url=f"https://example.com/page{i+1}",
                website_type="generic",
                status=statuses[i % len(statuses)],
                priority=(i % 5) + 1,
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            db.add(job)
        db.commit()
        logger.info(f"Seeded {count} scraping jobs")
    finally:
        db.close()


def seed_all():
    """Seed all test data."""
    logger.info("Seeding test data...")
    seed_users()
    seed_line_users()
    seed_scraping_jobs()
    logger.info("Seeding complete!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed test data")
    parser.add_argument("--users", type=int, default=5, help="Number of users")
    parser.add_argument("--line-users", type=int, default=10, help="Number of LINE users")
    parser.add_argument("--jobs", type=int, default=10, help="Number of scraping jobs")
    parser.add_argument("--all", action="store_true", help="Seed all data")

    args = parser.parse_args()

    if args.all:
        seed_all()
    else:
        seed_users(args.users)
        seed_line_users(args.line_users)
        seed_scraping_jobs(args.jobs)


if __name__ == "__main__":
    main()