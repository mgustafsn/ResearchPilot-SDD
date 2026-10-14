"""FR-QRY-002–010: actual PostgreSQL schema/revision compatibility."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

import pytest
from conftest import FakeSuggestionProvider, run_async
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.query_domain import GenerateInput, NoEnabledQueries
from researchpilot.query_service import QueryError, QueryService
from researchpilot.service import ProjectNotFound
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


# --- FR-QRY-004/005/007–010: generation snapshot/await/re-lock schedules ---


def run_generation(service, project_id, revision):
    return run_async(service.generate(project_id, GenerateInput(expectedRevision=revision)))


@pytest.fixture
def paused(client, db):
    provider = FakeSuggestionProvider(queries=("New A", "New B", "New C"), blocked=True)
    service = QueryService(db, provider)
    project = client.post("/api/projects", json=PROJECT).json()
    pool = ThreadPoolExecutor(max_workers=2)

    def start(revision=0):
        future = pool.submit(run_generation, service, project["id"], revision)
        assert provider.started.wait(5)
        return future
    try:
        yield SimpleNamespace(provider=provider, service=service, project=project, start=start,
                              path=f"/api/projects/{project['id']}", pool=pool)
    finally:
        provider.release.set()
        pool.shutdown(wait=True)


def stored(db):
    with db.engine.connect() as connection:
        return (connection.execute(select(db.projects)).mappings().all(),
                connection.execute(select(db.queries).order_by(db.queries.c.slot))
                .mappings().all())


@pytest.mark.parametrize("change", ["add", "edit", "toggle", "delete", "project"])
def test_FR_QRY_007_changes_during_generation_reject_stale_merge(client, db, paused, change):
    query = None
    if change in {"edit", "toggle", "delete"}:
        query = client.post(paused.path + "/queries", json={
            "text": "Existing", "expectedRevision": 0}).json()["queries"][0]
    revision = int(query is not None)
    future = paused.start(revision)
    queries = paused.path + "/queries"
    # The provider is awaiting, so no project lock may be held: these finish promptly.
    action = {
        "add": lambda: client.post(queries, json={"text": "During", "expectedRevision": 0}),
        "edit": lambda: client.patch(f"{queries}/{query['id']}", json={
            "expectedRevision": 1, "text": "Edited during"}),
        "toggle": lambda: client.patch(f"{queries}/{query['id']}", json={
            "expectedRevision": 1, "enabled": False}),
        "delete": lambda: client.delete(f"{queries}/{query['id']}?expectedRevision=1"),
        "project": lambda: client.put(paused.path, json=dict(PROJECT, title="Renamed")),
    }[change]
    assert paused.pool.submit(action).result(timeout=5).status_code in {200, 201}
    before = stored(db)
    paused.provider.release.set()
    with pytest.raises(QueryError) as raised:
        future.result(timeout=10)
    assert raised.value.code == "GENERATION_STALE" and raised.value.status == 409
    assert stored(db) == before and len(paused.provider.contexts) == 1


def test_FR_QRY_009_noop_project_put_during_generation_still_merges(client, db, paused):
    future = paused.start()
    assert client.put(paused.path, json=PROJECT).status_code == 200
    paused.provider.release.set()
    result = future.result(timeout=10)
    assert [q.text for q in result.queries] == ["New A", "New B", "New C"]
    assert result.revision == 1


def test_FR_QRY_010_project_deleted_during_generation_is_not_resurrected(client, db, paused):
    future = paused.start()
    assert paused.pool.submit(client.delete, paused.path).result(timeout=5).status_code == 204
    paused.provider.release.set()
    with pytest.raises(ProjectNotFound):
        future.result(timeout=10)
    assert stored(db) == ([], [])


def test_FR_QRY_007_two_same_revision_generations_have_one_winner(client, db, paused):
    first = paused.start()
    second = paused.pool.submit(run_generation, paused.service, paused.project["id"], 0)
    for _ in range(100):
        if len(paused.provider.contexts) == 2:
            break
        time.sleep(0.02)
    assert len(paused.provider.contexts) == 2
    paused.provider.release.set()
    outcomes = []
    for future in (first, second):
        try:
            outcomes.append(future.result(timeout=10).revision)
        except QueryError as error:
            outcomes.append(error.code)
    assert sorted(map(str, outcomes)) == ["1", "GENERATION_STALE"]
    projects, queries = stored(db)
    assert projects[0]["mutation_revision"] == 1 and len(queries) == 3


def test_FR_QRY_005_cancellation_before_merge_writes_nothing(client, db):
    provider = FakeSuggestionProvider(blocked=True)
    service = QueryService(db, provider)
    project = client.post("/api/projects", json=PROJECT).json()
    before = stored(db)

    async def cancel():
        task = asyncio.create_task(service.generate(project["id"],
                                                    GenerateInput(expectedRevision=0)))
        while not provider.started.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        provider.release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
    run_async(cancel())
    assert stored(db) == before


def test_FR_QRY_005_failed_merge_commit_rolls_back_everything(client, db, paused):
    client.put(paused.path, json=dict(PROJECT, researchQuestion="Changed"))
    future = paused.start(1)
    before = stored(db)

    def fail(connection):
        raise OperationalError("CANARY", {}, RuntimeError("CANARY"))
    event.listen(db.engine, "commit", fail, once=True)
    paused.provider.release.set()
    with pytest.raises(OperationalError):
        future.result(timeout=10)
    assert stored(db) == before
    assert before[0][0]["generated_context_revision"] is None


def test_FR_QRY_004_009_atomic_acknowledgement_and_no_owned_eviction(client, db):
    provider = FakeSuggestionProvider(queries=("Gen A", "Gen B", "Gen C"))
    service = QueryService(db, provider)
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}"
    first = run_generation(service, project["id"], 0)
    client.patch(f"{path}/queries/{first.queries[1].id}", json={
        "expectedRevision": 1, "enabled": False})
    client.put(path, json=dict(PROJECT, researchQuestion="Changed"))
    projects, queries = stored(db)
    assert projects[0]["query_context_revision"] == 1
    assert projects[0]["generated_context_revision"] == 0
    provider.queries = ("gen b", "Gen D", "Gen E")
    second = run_generation(service, project["id"], 3)
    projects, queries = stored(db)
    assert projects[0]["generated_context_revision"] == 1
    assert projects[0]["mutation_revision"] == second.revision == 4
    assert [(q["text"], q["slot"], q["user_owned"], q["enabled"]) for q in queries] == [
        ("Gen D", 1, False, True), ("Gen B", 2, True, False), ("Gen E", 3, False, True)]
    assert queries[1]["id"] == first.queries[1].id
    assert second.generationSummary.duplicateSkippedCount == 1


def test_FR_QRY_003_009_generated_state_survives_restart_into_manual_only(db, db_url,
                                                                          monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(db_url))
    provider = FakeSuggestionProvider(queries=("Gen A", "Gen B", "Gen C"))
    with TestClient(create_app(suggestion_provider=provider)) as first:
        project = first.post("/api/projects", json=PROJECT).json()
        path = f"/api/projects/{project['id']}/queries"
        generated = first.post(path + "/generate", json={"expectedRevision": 0}).json()
    with TestClient(create_app(suggestion_provider=None)) as restarted:
        state = restarted.get(path).json()
        assert state["queries"] == generated["queries"] and not state["refreshRequired"]
        assert state["generationAvailable"] is False
        unavailable = restarted.post(path + "/generate", json={"expectedRevision": 1})
        assert unavailable.status_code == 503
        assert restarted.post(path, json={"text": "Manual", "expectedRevision": 1}
                              ).status_code == 201


def test_FR_QRY_010_deleted_query_may_reappear_without_suppression_history(client, db):
    service = QueryService(db, FakeSuggestionProvider(queries=("Gen A", "Gen B", "Gen C")))
    project = client.post("/api/projects", json=PROJECT).json()
    first = run_generation(service, project["id"], 0)
    target = first.queries[0]
    client.delete(f"/api/projects/{project['id']}/queries/{target.id}?expectedRevision=1")
    again = run_generation(service, project["id"], 2)
    assert [q.text for q in again.queries] == ["Gen A", "Gen B", "Gen C"]
    assert target.id not in {q.id for q in again.queries}
