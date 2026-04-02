"""Database engine and session factory. Provides the get_db dependency for FastAPI routes."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a database session per request and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()