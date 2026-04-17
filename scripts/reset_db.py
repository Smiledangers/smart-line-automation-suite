"""Reset database script."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import text

from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_db():
    """Drop all tables and recreate them."""
    logger.warning("⚠️  This will delete ALL data! ⚠️")

    confirm = input("Are you sure? Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        logger.info("Cancelled")
        return False

    try:
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")

        # Recreate tables
        logger.info("Recreating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables recreated successfully")

        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Reset database")
    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if args.force:
        logger.info("Force mode: resetting database...")
        # Force reset without confirmation
        try:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Database reset complete")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    success = reset_db()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()