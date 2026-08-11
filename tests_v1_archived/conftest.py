import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database import Base, build_session_factory, get_session
from app.main import app


@pytest.fixture()
def client(tmp_path):
    session_factory = build_session_factory(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(session_factory.kw["bind"])

    def override_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
