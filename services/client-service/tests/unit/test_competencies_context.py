from fastapi.testclient import TestClient

from tests.conftest import auth


def test_competency_lifecycle_and_ensure_current(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created_client = create_client()
    base = f"/clients/{created_client['id']}/competencies"
    created = client.post(
        base, headers=admin_headers, json={"year": 2026, "month": 7}
    )
    duplicate = client.post(
        base, headers=admin_headers, json={"year": 2026, "month": 7}
    )
    ensured = client.post(
        f"{base}/ensure-current",
        headers=admin_headers,
        json={"year": 2026, "month": 7},
    )
    status_changed = client.patch(
        f"{base}/{created.json()['id']}/status",
        headers=admin_headers,
        json={"status": "READY_FOR_CONFERENCE"},
    )
    closed = client.patch(
        f"{base}/{created.json()['id']}/close", headers=admin_headers
    )
    locked = client.patch(
        f"{base}/{created.json()['id']}",
        headers=admin_headers,
        json={"folderPath": "manual"},
    )
    archived = client.patch(
        f"{base}/{created.json()['id']}/archive", headers=admin_headers
    )

    assert created.status_code == 201
    assert created.json()["period"] == "2026-07"
    assert created.json()["folderPath"].endswith("\\2026\\07")
    assert duplicate.status_code == 409
    assert ensured.json()["created"] is False
    assert status_changed.json()["status"] == "READY_FOR_CONFERENCE"
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["closedByUserId"] == "admin-user"
    assert locked.status_code == 422
    assert archived.json()["status"] == "ARCHIVED"


def test_context_and_preferences_use_real_clients(
    client: TestClient, create_client, admin_headers: dict[str, str]
) -> None:
    created = create_client()
    competency = client.post(
        f"/clients/{created['id']}/competencies",
        headers=admin_headers,
        json={"year": 2026, "month": 7},
    ).json()
    context = client.get("/client-context", headers=admin_headers)
    preference = client.patch(
        "/client-context/preferences",
        headers=admin_headers,
        json={
            "defaultClientId": created["id"],
            "defaultCompetencePeriod": competency["period"],
        },
    )
    context_after = client.get("/client-context", headers=admin_headers)
    empty = client.get("/client-context", headers=auth("unlinked"))

    assert context.status_code == 200
    assert context.json()["clients"][0]["id"] == created["id"]
    assert preference.status_code == 200
    assert context_after.json()["defaultClientId"] == created["id"]
    assert context_after.json()["currentCompetence"]["period"] == "2026-07"
    assert empty.json()["clients"] == []


def test_preference_rejects_inaccessible_client(
    client: TestClient, create_client
) -> None:
    created = create_client()
    response = client.patch(
        "/client-context/preferences",
        headers=auth("unlinked"),
        json={"defaultClientId": created["id"]},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CLIENT_ACCESS_DENIED"
