import pytest
from fastapi.testclient import TestClient
import mongomock

from app.database.connection import get_db
from app.main import app


@pytest.fixture
def client():
    """Provides a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def override_database_dependency():
    """Uses one isolated in-memory database for each test."""
    mongo_client = mongomock.MongoClient(tz_aware=True)
    test_database = mongo_client["test_framework"]

    def override_get_db():
        yield test_database

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    mongo_client.close()
