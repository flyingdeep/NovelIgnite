"""Pytest session fixtures.

Redirects observability logs to a temp dir so tests never pollute logs/app.jsonl.
Must run before app modules import observability.
"""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("NOVEL_LOG_DIR", os.path.join(tempfile.gettempdir(), "novel_ignite_test_logs"))


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()
