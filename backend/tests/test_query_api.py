"""FR-QRY-002–010 manual API tests using real disposable PostgreSQL."""

from uuid import uuid4

import pytest

PROJECT = {"title": "Queries", "researchQuestion": "Question", "maxPaperCount": 100}


@pytest.fixture
def query_path(client):
    project = client.post("/api/projects", json=PROJECT).json()
    return f"/api/projects/{project['id']}/queries"


def test_FR_QRY_003_manual_crud_and_sticky_ownership(client, query_path):
    initial = client.get(query_path)
    assert initial.status_code == 200
    state = initial.json()
    assert state["revision"] == 0 and state["generationAvailable"] is False
    assert state["queries"] == [] and state["refreshRequired"] is False
    response = client.post(query_path, json={"text": " AI\n tutors ", "expectedRevision": 0})
    assert response.status_code == 201
    state = response.json()
    query = state["queries"][0]
    assert query["text"] == "AI tutors" and query["enabled"] and query["userOwned"]
    assert query["origin"] == "manual" and state["revision"] == 1
    path = f"{query_path}/{query['id']}"
    response = client.patch(path, json={"expectedRevision": 1, "enabled": False})
    assert response.status_code == 200 and response.json()["revision"] == 2
    assert response.json()["queries"][0]["enabled"] is False
    response = client.patch(path, json={"expectedRevision": 2, "enabled": False})
    assert response.json()["revision"] == 2  # No effective change.
    assert client.delete(path + "?expectedRevision=2").json()["queries"] == []


def test_FR_QRY_002_007_duplicates_stale_and_scoped_ids(client, query_path):
    created = client.post(query_path, json={"text": "Straße", "expectedRevision": 0}).json()
    duplicate = client.post(query_path, json={"text": "STRASSE", "expectedRevision": 1})
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "QUERY_DUPLICATE"
    stale = client.post(query_path, json={"text": "Another", "expectedRevision": 0})
    assert stale.status_code == 409
    assert client.get(query_path).json() == created
    assert client.patch(f"{query_path}/{uuid4()}", json={"expectedRevision": 1,
        "enabled": False}).status_code == 404


def test_FR_QRY_008_capacity_includes_disabled_and_releases_slot(client, query_path):
    for i in range(20):
        response = client.post(query_path, json={"text": f"Query {i}",
            "enabled": False, "expectedRevision": i})
        assert response.status_code == 201
    state = response.json()
    rejected = client.post(query_path, json={"text": "Too many", "expectedRevision": 20})
    assert rejected.status_code == 409
    query = state["queries"][0]
    assert client.delete(f"{query_path}/{query['id']}?expectedRevision=20").status_code == 200
    added = client.post(query_path, json={"text": "Replacement", "expectedRevision": 21})
    assert added.status_code == 201 and len(added.json()["queries"]) == 20


@pytest.mark.parametrize("values", [{"text": ""}, {"text": "CANARY", "expectedRevision": True},
    {"text": "CANARY", "expectedRevision": 0, "origin": "generated"}])
def test_FR_QRY_003_invalid_input_no_writes(client, query_path, values):
    response = client.post(query_path, json=values)
    assert response.status_code == 422
    assert "CANARY" not in response.text
    assert client.get(query_path).json()["queries"] == []


def test_FR_QRY_009_context_notice_preserves_queries_and_project_contract(client, query_path):
    original = client.get(query_path.removesuffix("/queries")).json()
    state = client.post(query_path, json={"text": "Manual", "expectedRevision": 0}).json()
    assert client.get(query_path.removesuffix("/queries")).json() == original
    client.put(query_path.removesuffix("/queries"), json=dict(PROJECT, researchQuestion="Changed"))
    changed = client.get(query_path).json()
    assert changed["refreshRequired"] is True and changed["queries"] == state["queries"]
    client.put(query_path.removesuffix("/queries"), json=PROJECT)
    assert client.get(query_path).json()["refreshRequired"] is True
