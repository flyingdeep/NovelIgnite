"""SQLAlchemy engine, session factory, and Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.infrastructure.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a session and closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
