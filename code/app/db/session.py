"""
Database session management (SQLAlchemy sync and async configuration).
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# Sync engine and session maker (commonly used for Alembic and simple sync tasks)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session maker (recommended for FastAPI asynchronous endpoints)
# Replace postgresql:// with postgresql+asyncpg:// for async pg driver compatibility
async_db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_db_url,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency provider for synchronous database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency provider for asynchronous database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
