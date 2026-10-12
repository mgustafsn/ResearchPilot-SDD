"""Project route contract tests with isolated real PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy import text
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
