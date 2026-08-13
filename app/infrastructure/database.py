"""SQLAlchemy engine, session factory, and Base."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.infrastructure.config import settings

_is_sqlite = "sqlite" in settings.database_url
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30} if _is_sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        # 使用默认 journal（rollback journal）而非 WAL：避免 -wal/-shm 辅助文件
        # 被误删导致数据库损坏；busy_timeout 缓解并发写锁。
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a session and closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
