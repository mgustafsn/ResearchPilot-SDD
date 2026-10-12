"""Project route contract tests with isolated real PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

VALID = {"title": "A project", "researchQuestion": "A question", "maxPaperCount": 100}


def test_FR_PRJ_001_create_list_read(client):
    assert client.get("/api/projects").json() == []
    response = client.post("/api/projects", json=dict(VALID, title="  A project  "))
    assert response.status_code == 201
    project = response.json()
    assert project["title"] == "A project"
    assert set(project) == {"id", "title", "researchQuestion", "keywords", "yearFrom", "yearTo",
                            "maxPaperCount", "createdAt", "updatedAt"}
    assert project["createdAt"].endswith("Z")
    assert client.get(f"/api/projects/{project['id']}").json() == project
    assert client.get("/api/projects").json() == [project]


def test_FR_PRJ_006_duplicate_names_and_tie_order(client, db):
    first = client.post("/api/projects", json=VALID)
    second = client.post("/api/projects", json=VALID)
    assert first.status_code == second.status_code == 201
    ids = [first.json()["id"], second.json()["id"]]
    assert client.get("/api/projects").json()[0]["id"] == ids[1]
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE projects SET updated_at = '2026-01-01T00:00:00Z'"))
    assert [p["id"] for p in client.get("/api/projects").json()] == sorted(ids)


@pytest.mark.parametrize("values", [
    dict(VALID, title=""), dict(VALID, yearFrom=2026, yearTo=2020),
    dict(VALID, maxPaperCount=True), dict(VALID, extra="CANARY-SECRET"),
    {"title": "A project"},
])
def test_FR_PRJ_007_validation_errors_preserve_data(client, values):
    response = client.post("/api/projects", json=values)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR" and error["fields"]
    assert "CANARY-SECRET" not in response.text
    assert client.get("/api/projects").json() == []


def test_FR_PRJ_007_malformed_json_and_ids(client):
    malformed = client.post("/api/projects", content='{"CANARY-SECRET":',
                            headers={"Content-Type": "application/json"})
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "CANARY-SECRET" not in malformed.text
    response = client.get("/api/projects/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(f"/api/projects/{uuid4()}").status_code == 404


def test_FR_PRJ_007_NFR_PRJ_001_storage_errors_are_sanitized(client, db, monkeypatch, caplog):
    def fail(*args, **kwargs):
        raise OperationalError("SQL CANARY-SECRET", {}, RuntimeError("CANARY-SECRET"))

    monkeypatch.setattr(db.engine, "connect", fail)
    response = client.get("/api/projects")
    assert response.status_code == 503
    assert response.json() == {"error": {"code": "STORAGE_UNAVAILABLE",
        "message": "Storage is temporarily unavailable. Please try again.", "fields": []}}
    assert "CANARY-SECRET" not in response.text + caplog.text


def test_FR_PRJ_001_006_full_update_preserves_identity(client):
    original = client.post("/api/projects", json=VALID).json()
    path = f"/api/projects/{original['id']}"
    response = client.put(path, json=dict(VALID, title=" Edited ", keywords=["AI", "ai"]))
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == original["id"] and updated["createdAt"] == original["createdAt"]
    assert updated["updatedAt"] > original["updatedAt"]
    assert updated["title"] == "Edited" and updated["keywords"] == ["AI"]
    assert client.get(path).json() == updated


@pytest.mark.parametrize("values", [dict(VALID, title=""), {"title": "Incomplete"},
                                   dict(VALID, id=str(uuid4()))])
def test_FR_PRJ_007_invalid_update_preserves_original(client, values):
    original = client.post("/api/projects", json=VALID).json()
    path = f"/api/projects/{original['id']}"
    assert client.put(path, json=values).status_code == 422
    assert client.get(path).json() == original


def test_FR_PRJ_008_delete_isolated_and_unknown_ids(client):
    first = client.post("/api/projects", json=VALID).json()
    second = client.post("/api/projects", json=dict(VALID, title="Other")).json()
    path = f"/api/projects/{first['id']}"
    response = client.delete(path)
    assert response.status_code == 204 and response.content == b""
    assert client.get(path).status_code == 404
    assert client.delete(path).status_code == 404
    assert client.put(path, json=VALID).status_code == 404
    assert client.get("/api/projects").json() == [second]
    assert client.delete("/api/projects/not-a-uuid").status_code == 422


@pytest.mark.parametrize("method", ["put", "delete"])
def test_FR_PRJ_007_failed_commit_preserves_original(client, db, method, caplog):
    original = client.post("/api/projects", json=VALID).json()
    path = f"/api/projects/{original['id']}"

    def fail(connection):
        raise OperationalError("CANARY-SECRET", {}, RuntimeError("CANARY-SECRET"))

    event.listen(db.engine, "commit", fail, once=True)
    options = {"json": dict(VALID, title="Changed")} if method == "put" else {}
    response = getattr(client, method)(path, **options)
    assert response.status_code == 503
    assert "CANARY-SECRET" not in response.text + caplog.text
    assert client.get(path).json() == original
