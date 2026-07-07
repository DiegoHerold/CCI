from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal
from tests.conftest import auth


def test_client_lifecycle_and_cnpj_validation(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created = create_client()
    assert created["cnpjNormalized"] == "12345678000195"
    assert created["cnpj"] == "12.345.678/0001-95"

    duplicate = client.post(
        "/clients",
        headers=admin_headers,
        json={"name": "Duplicada", "cnpj": "12345678000195"},
    )
    invalid = client.post(
        "/clients",
        headers=admin_headers,
        json={"name": "Inválida", "cnpj": "12.345.678/0001-00"},
    )
    updated = client.patch(
        f"/clients/{created['id']}",
        headers=admin_headers,
        json={"tradeName": "Novo Nome"},
    )
    disabled = client.patch(
        f"/clients/{created['id']}/disable", headers=admin_headers
    )
    restored = client.patch(
        f"/clients/{created['id']}/restore", headers=admin_headers
    )
    archived = client.patch(
        f"/clients/{created['id']}/archive", headers=admin_headers
    )
    listed = client.get("/clients", headers=admin_headers)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CLIENT_CNPJ_ALREADY_EXISTS"
    assert invalid.status_code == 422
    assert updated.json()["tradeName"] == "Novo Nome"
    assert disabled.json()["status"] == "INACTIVE"
    assert restored.json()["status"] == "ACTIVE"
    assert archived.json()["status"] == "ARCHIVED"
    assert listed.json()["total"] == 0


def test_folder_preview_and_update(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created = create_client()
    preview = client.post(
        f"/clients/{created['id']}/folder-preview",
        headers=admin_headers,
        json={"year": 2026, "month": 7},
    )
    updated = client.patch(
        f"/clients/{created['id']}/folder",
        headers=admin_headers,
        json={"competenceFolderPattern": "{{MM}}-{{YYYY}}"},
    )
    unsafe = client.patch(
        f"/clients/{created['id']}/folder",
        headers=admin_headers,
        json={"competenceFolderPattern": "../{{MM}}"},
    )

    assert preview.status_code == 200
    assert preview.json()["resolvedCompetencePath"].endswith("\\2026\\07")
    assert updated.json()["competenceFolderPattern"] == "{{MM}}-{{YYYY}}"
    assert unsafe.status_code == 422


def test_permission_and_client_link_access(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created = create_client()
    denied_create = client.post(
        "/clients",
        headers=auth("viewer"),
        json={"name": "Sem permissão", "cnpj": "45.723.174/0001-10"},
    )
    denied_access = client.get(
        f"/clients/{created['id']}", headers=auth("unlinked")
    )
    linked = client.post(
        f"/clients/{created['id']}/users",
        headers=admin_headers,
        json={
            "userId": "operator-user",
            "clientRole": "CLIENT_OPERATOR",
            "responsibilityArea": "ACCOUNTING",
            "isPrimaryResponsible": True,
        },
    )
    allowed = client.get(f"/clients/{created['id']}", headers=auth("operator"))
    deactivated = client.delete(
        f"/clients/{created['id']}/users/operator-user", headers=admin_headers
    )
    denied_after = client.get(
        f"/clients/{created['id']}", headers=auth("operator")
    )

    assert denied_create.status_code == 403
    assert denied_access.status_code == 403
    assert denied_access.json()["error"]["code"] == "CLIENT_ACCESS_DENIED"
    assert linked.status_code == 201
    assert allowed.status_code == 200
    assert deactivated.json()["status"] == "INACTIVE"
    assert denied_after.status_code == 403


def test_inactive_client_rejects_competency_and_link(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created = create_client()
    client.patch(f"/clients/{created['id']}/disable", headers=admin_headers)

    competency = client.post(
        f"/clients/{created['id']}/competencies",
        headers=admin_headers,
        json={"year": 2026, "month": 7},
    )
    link = client.post(
        f"/clients/{created['id']}/users",
        headers=admin_headers,
        json={"userId": "operator-user", "clientRole": "CLIENT_OPERATOR"},
    )

    assert competency.status_code == 422
    assert link.status_code == 422


def test_postgresql_migration_tables_exist(client: TestClient) -> None:
    with SessionLocal() as session:
        tables = set(
            session.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'core'"
                )
            ).all()
        )
    assert {
        "clients",
        "client_competencies",
        "client_users",
        "user_client_preferences",
        "client_audit_events",
    }.issubset(tables)

