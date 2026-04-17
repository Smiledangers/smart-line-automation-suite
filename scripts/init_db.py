"""Initialize database script."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import text

from app.core.database import engine, Base
from app.core.config import get_settings
from app.models.user import User
from app.models.line_user import LINEUser
from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize database tables."""
    logger.info("Creating database tables...")

    # Import all models to ensure they're registered
    try:
        from app.models import user, line_user, scraping_job, scraping_result
    except ImportError as e:
        logger.warning(f"Some models not found: {e}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        logger.info(f"Tables created: {tables}")

    return True


def reset_db():
    """Reset database (drop all tables)."""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")
    return init_db()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument("--reset", action="store_true", help="Reset database")

    args = parser.parse_args()

    if args.reset:
        success = reset_db()
    else:
        success = init_db()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()