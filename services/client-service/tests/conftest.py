import os
import sys
from collections.abc import Generator
from pathlib import Path


CLIENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLIENT_ROOT))

database_url = os.environ.get("DATABASE_URL", "")
if not database_url.startswith("postgresql"):
    raise RuntimeError("Client Service tests require a PostgreSQL DATABASE_URL")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.dependencies import get_identity_gateway
from app.domain.enums import Permission
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.identity_gateway import Principal
from app.main import app


ALL_CLIENT_PERMISSIONS = tuple(
    value
    for name, value in vars(Permission).items()
    if name.isupper() and isinstance(value, str)
)

ROLE_PERMISSIONS = {
    "admin": ALL_CLIENT_PERMISSIONS,
    "manager": (
        Permission.CLIENTS_READ,
        Permission.CLIENTS_UPDATE,
        Permission.CLIENT_USERS_READ,
        Permission.COMPETENCIES_READ,
        Permission.COMPETENCIES_CREATE,
        Permission.COMPETENCIES_UPDATE,
        Permission.COMPETENCIES_CLOSE,
        Permission.FOLDERS_READ,
        Permission.FOLDERS_UPDATE,
        Permission.FOLDERS_PREVIEW,
        Permission.CONTEXT_READ,
    ),
    "operator": (
        Permission.CLIENTS_READ,
        Permission.COMPETENCIES_READ,
        Permission.COMPETENCIES_CREATE,
        Permission.COMPETENCIES_UPDATE,
        Permission.FOLDERS_READ,
        Permission.FOLDERS_PREVIEW,
        Permission.CONTEXT_READ,
    ),
    "viewer": (
        Permission.CLIENTS_READ,
        Permission.COMPETENCIES_READ,
        Permission.FOLDERS_READ,
        Permission.FOLDERS_PREVIEW,
        Permission.CONTEXT_READ,
    ),
    "unlinked": (
        Permission.CLIENTS_READ,
        Permission.COMPETENCIES_READ,
        Permission.FOLDERS_READ,
        Permission.FOLDERS_PREVIEW,
        Permission.CONTEXT_READ,
    ),
}


class FakeIdentityGateway:
    async def authenticate(self, authorization: str, correlation_id: str) -> Principal:
        token = authorization.removeprefix("Bearer ")
        if token not in ROLE_PERMISSIONS:
            from app.errors import InvalidTokenError

            raise InvalidTokenError()
        return Principal(
            id=f"{token}-user",
            name=token.title(),
            email=f"{token}@example.com",
            status="ACTIVE",
            roles=("ADMIN",) if token == "admin" else (token.upper(),),
            permissions=ROLE_PERMISSIONS[token],
            authorization=authorization,
        )

    async def get_user(self, user_id: str, principal: Principal, correlation_id: str):
        return {
            "id": user_id,
            "name": "Linked User",
            "email": "linked@example.com",
            "status": "INACTIVE" if user_id == "inactive-user" else "ACTIVE",
            "roles": ["OPERATOR"],
            "permissions": [],
        }


fake_identity = FakeIdentityGateway()
app.dependency_overrides[get_identity_gateway] = lambda: fake_identity


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE core.client_audit_events, core.user_client_preferences, "
                "core.client_users, core.client_competencies, core.clients CASCADE"
            )
        )
        session.commit()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def auth(token: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return auth("admin")


@pytest.fixture
def create_client(client: TestClient, admin_headers: dict[str, str]):
    def create(**overrides):
        payload = {
            "code": "0001",
            "name": "Empresa Exemplo LTDA",
            "tradeName": "Empresa Exemplo",
            "cnpj": "12.345.678/0001-95",
            "taxRegime": "SIMPLES_NACIONAL",
            "city": "Gravataí",
            "state": "RS",
            "defaultFolderPath": "R:\\Clientes\\Empresa Exemplo",
            "competenceFolderPattern": "{{YYYY}}/{{MM}}",
        }
        payload.update(overrides)
        response = client.post("/clients", headers=admin_headers, json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return create

