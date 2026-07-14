import os
import sys
from collections.abc import Generator
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEMPLATE_ROOT))

database_url = os.environ.get("DATABASE_URL", "")
if not database_url.startswith("postgresql"):
    raise RuntimeError("Template Service tests require a PostgreSQL DATABASE_URL")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.dependencies import get_event_publisher, get_identity_gateway
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal
from app.main import app


class FakeIdentityGateway:
    async def authenticate(self, authorization: str, correlation_id: str) -> Principal:
        token = authorization.removeprefix("Bearer ")
        return Principal(
            id=f"{token}-user",
            name=token.title(),
            email=f"{token}@example.com",
            status="ACTIVE",
            roles=("ADMIN",),
            permissions=("templates:manage",),
            authorization=authorization,
        )


class FakeEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


fake_publisher = FakeEventPublisher()
app.dependency_overrides[get_identity_gateway] = lambda: FakeIdentityGateway()
app.dependency_overrides[get_event_publisher] = lambda: fake_publisher


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    fake_publisher.events.clear()
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE template.extraction_rules, template.template_annotations, "
                "template.identification_signals, template.template_fields, "
                "template.template_versions, template.templates, template.categories CASCADE"
            )
        )
        session.commit()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer admin"}


@pytest.fixture
def create_template(client: TestClient, auth_headers: dict[str, str]):
    def _create_template() -> dict:
        category = client.post(
            "/template-categories",
            headers=auth_headers,
            json={
                "name": "Balancete",
                "slug": "balancete",
                "description": "Documentos de balancete contabil",
            },
        ).json()
        return client.post(
            "/templates",
            headers=auth_headers,
            json={
                "name": "Balancete Dominio PDF",
                "description": "Template para balancete em PDF",
                "categoryId": category["id"],
                "fileFormat": "PDF",
                "structureType": "hierarchical",
            },
        ).json()

    return _create_template
