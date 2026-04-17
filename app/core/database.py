"""
Database connection module with async support.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Create async SQLAlchemy engine
engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create async SessionLocal class
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# Create Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session