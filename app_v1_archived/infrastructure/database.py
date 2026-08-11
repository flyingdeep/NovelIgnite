from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.infrastructure.config import get_settings


class Base(DeclarativeBase):
    pass


def build_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    return sessionmaker(bind=engine, expire_on_commit=False)


SessionLocal = build_session_factory()


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
