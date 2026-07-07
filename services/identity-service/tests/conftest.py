import os
import sys
from collections.abc import Generator
from pathlib import Path


IDENTITY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IDENTITY_ROOT))

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_ACCESS_SECRET"] = "test-secret-with-at-least-32-characters"
os.environ["JWT_ACCESS_EXPIRES_IN"] = "900"
os.environ["JWT_REFRESH_SECRET"] = "test-refresh-secret-with-at-least-32-characters"
os.environ["JWT_REFRESH_EXPIRES_IN"] = "604800"
os.environ["AUTH_MAX_FAILED_ATTEMPTS"] = "5"
os.environ["AUTH_LOCK_MINUTES"] = "15"
os.environ["AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS"] = "60"
os.environ["AUTH_LOGIN_RATE_LIMIT_MAX"] = "100"
os.environ["SEED_ADMIN_NAME"] = "Test Administrator"
os.environ["SEED_ADMIN_EMAIL"] = "admin@example.com"
os.environ["SEED_ADMIN_PASSWORD"] = "AdminPassword123!"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_db
from app.infrastructure.seed import seed_identity
from app.main import app


test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    execution_options={"schema_translate_map": {"auth": None}},
)
TestingSession = sessionmaker(
    bind=test_engine, autoflush=False, expire_on_commit=False
)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    with TestingSession() as session:
        seed_identity(session, get_settings())
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestingSession() as session:
        yield session
