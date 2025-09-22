import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.main import app
from app.conf.config import get_db
from app.services import cache as cache_module

@pytest.fixture(scope="session")
def engine_and_session():
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine, TestingSessionLocal
    os.unlink(db_path)

@pytest.fixture()
def db_session(engine_and_session):
    _, TestingSessionLocal = engine_and_session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_dependencies(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db

    class DummyCache:
        def __init__(self):
            self.reset_tokens: dict[str, str] = {}
        async def set_user_for_token(self, token, user):
            return None
        async def get_user_by_token(self, token):
            return None
        async def set_password_reset_token(self, token: str, email: str):
            self.reset_tokens[token] = email
        async def pop_email_by_reset_token(self, token: str):
            return self.reset_tokens.pop(token, None)

    cache_module.cache_service = DummyCache()
    yield
    app.dependency_overrides.clear()

@pytest.fixture()
def client():
    return TestClient(app) 