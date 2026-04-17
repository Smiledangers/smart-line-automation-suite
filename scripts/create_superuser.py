"""Create superuser script."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from passlib.context import CryptContext

from app.core.database import SessionLocal
from app.models.user import User
from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_superuser(email: str, password: str, full_name: str = None):
    """Create a superuser account."""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            logger.error(f"User {email} already exists")
            return False

        # Create superuser
        hashed_password = pwd_context.hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name or "Admin",
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Superuser created: {email} (ID: {user.id})")
        return True
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create superuser")
    parser.add_argument("--email", default=settings.FIRST_SUPERUSER, help="Admin email")
    parser.add_argument(
        "--password",
        default=settings.FIRST_SUPERUSER_PASSWORD,
        help="Admin password",
    )
    parser.add_argument("--name", help="Admin full name")

    args = parser.parse_args()

    success = create_superuser(args.email, args.password, args.name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()