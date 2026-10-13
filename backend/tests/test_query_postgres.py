"""FR-QRY-002–010: actual PostgreSQL schema/revision compatibility."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.query_domain import NoEnabledQueries
from researchpilot.query_service import QueryService
from sqlalchemy import event, insert, select
from sqlalchemy.exc import IntegrityError, OperationalError

PROJECT = {"title": "Queries", "researchQuestion": "Question", "maxPaperCount": 100}


def test_FR_QRY_007_009_initial_revisions_and_context_updates(client, db):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}"

    def state():
        with db.engine.connect() as connection:
            return connection.execute(select(db.projects)).mappings().one()

    assert state()["mutation_revision"] == state()["query_context_revision"] == 0
    assert state()["generated_context_revision"] is None
    client.put(path, json=PROJECT)
    assert state()["mutation_revision"] == 0
    client.put(path, json=dict(PROJECT, title="Title only"))
    assert state()["mutation_revision"] == 1 and state()["query_context_revision"] == 0
    client.put(path, json=dict(PROJECT, researchQuestion="Changed"))
    assert state()["mutation_revision"] == 2 and state()["query_context_revision"] == 1
    client.put(path, json=PROJECT)
    assert state()["query_context_revision"] == 2


@pytest.mark.parametrize("overrides", [{"slot": 0}, {"slot": 21}, {"text": ""},
    {"text": "x" * 161}, {"origin": "paper"}, {"origin": "manual", "user_owned": False}])
def test_FR_QRY_002_003_008_query_database_constraints(client, db, overrides):
    project = client.post("/api/projects", json=PROJECT).json()
    values = dict(id=uuid4(), project_id=project["id"], text="Query", normalized_key="query",
                  enabled=True, origin="manual", user_owned=True, slot=1)
    values.update(overrides)
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(insert(db.queries).values(**values))


def test_FR_QRY_002_010_unique_key_and_project_cascade(client, db):
    project = client.post("/api/projects", json=PROJECT).json()
    values = dict(id=uuid4(), project_id=project["id"], text="Straße", normalized_key="strasse",
                  enabled=False, origin="manual", user_owned=True, slot=1)
    with db.engine.begin() as connection:
        connection.execute(insert(db.queries).values(**values))
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(insert(db.queries).values(**dict(values, id=uuid4(), slot=2)))
    assert client.delete(f"/api/projects/{project['id']}").status_code == 204
    with db.engine.connect() as connection:
        assert connection.execute(select(db.queries)).all() == []


def test_FR_QRY_007_same_revision_has_one_winner(client):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}/queries"

    def add(index):
        return client.post(path, json={"text": f"Concurrent {index}", "expectedRevision": 0})

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(add, [1, 2]))
    assert sorted(response.status_code for response in responses) == [201, 409]
    assert len(client.get(path).json()["queries"]) == 1


def test_FR_QRY_005_007_failed_manual_commit_rolls_back(client, db):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}/queries"
    original = client.get(path).json()

    def fail(connection):
        raise OperationalError("CANARY", {}, RuntimeError("CANARY"))

    event.listen(db.engine, "commit", fail, once=True)
    response = client.post(path, json={"text": "Lost", "expectedRevision": 0})
    assert response.status_code == 503 and "CANARY" not in response.text
    assert client.get(path).json() == original


def test_FR_QRY_003_009_query_and_notice_survive_app_restart(db, db_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(db_url))
    with TestClient(create_app(suggestion_provider=None)) as first:
        project = first.post("/api/projects", json=PROJECT).json()
        parent_path = f"/api/projects/{project['id']}"
        path = parent_path + "/queries"
        first.post(path, json={"text": "Durable", "expectedRevision": 0, "enabled": False})
        first.put(parent_path, json=dict(PROJECT, researchQuestion="Changed"))
        snapshot = first.get(path).json()
    with TestClient(create_app(suggestion_provider=None)) as restarted:
        assert restarted.get(path).json() == snapshot
        assert snapshot["refreshRequired"] and snapshot["queries"][0]["enabled"] is False


def test_FR_QRY_004_generated_toggle_ownership_stays_after_restoration(client, db):
    project = client.post("/api/projects", json=PROJECT).json()
    query_id = uuid4()
    with db.engine.begin() as connection:
        connection.execute(insert(db.queries).values(
            id=query_id, project_id=project["id"], text="Generated", normalized_key="generated",
            slot=1, enabled=True, origin="generated", user_owned=False))
    path = f"/api/projects/{project['id']}/queries/{query_id}"
    unchanged = client.patch(path, json={"expectedRevision": 0, "enabled": True}).json()
    assert not unchanged["queries"][0]["userOwned"] and unchanged["revision"] == 0
    changed = client.patch(path, json={"expectedRevision": 0, "enabled": False}).json()
    assert changed["queries"][0]["userOwned"]
    restored = client.patch(path, json={"expectedRevision": 1, "enabled": True}).json()
    assert restored["queries"][0]["userOwned"] and restored["queries"][0]["origin"] == "generated"


def test_FR_QRY_006_service_selects_only_enabled_stored_texts(client, db):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}/queries"
    service = QueryService(db)
    with pytest.raises(NoEnabledQueries):
        service.selected_texts(project["id"])
    client.post(path, json={"text": "Disabled", "expectedRevision": 0, "enabled": False})
    client.post(path, json={"text": "Selected", "expectedRevision": 1})
    assert service.selected_texts(project["id"]) == ["Selected"]
