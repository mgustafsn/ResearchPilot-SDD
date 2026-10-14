"""FR-QRY-001–010 manual and fake-provider API tests using real disposable PostgreSQL."""

import logging
import threading
from uuid import uuid4

import pytest
from conftest import FakeSuggestionProvider
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.query_domain import SuggestionBatch
from researchpilot.query_provider import (
    SuggestionMetadata,
    SuggestionProviderError,
    SuggestionResult,
)
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

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


# --- FR-QRY-001/002/004/005/007–010: explicit generation through injected fakes ---

class FailingProvider:
    def __init__(self, category):
        self.category, self.calls = category, 0

    async def suggest(self, context):
        self.calls += 1
        raise SuggestionProviderError(self.category)


class CrashingProvider:
    async def suggest(self, context):
        raise RuntimeError("CANARY internal")


class UnvalidatedProvider:
    """Bypasses model validation to prove the service re-validates the whole batch."""

    async def suggest(self, context):
        return SuggestionResult.model_construct(
            batch=SuggestionBatch.model_construct(queries=["Valid", "valid", "x" * 200]))


@pytest.fixture
def generation(db):
    clients = []

    def start(provider):
        client = TestClient(create_app(db, suggestion_provider=provider))
        clients.append(client.__enter__())
        project = clients[-1].post("/api/projects", json=dict(
            PROJECT, keywords=["tutors", "feedback"])).json()
        return clients[-1], f"/api/projects/{project['id']}/queries"
    yield start
    for client in clients:
        client.__exit__(None, None, None)


def test_FR_QRY_001_generate_merges_validated_batch_with_summary(generation):
    provider = FakeSuggestionProvider(queries=(" AI\n tutoring ", "Feedback", "Learning"))
    client, path = generation(provider)
    assert client.get(path).json()["generationAvailable"] is True
    response = client.post(path + "/generate", json={"expectedRevision": 0})
    assert response.status_code == 200
    state = response.json()
    assert [q["text"] for q in state["queries"]] == ["AI tutoring", "Feedback", "Learning"]
    assert all(q["origin"] == "generated" and q["enabled"] and not q["userOwned"]
               for q in state["queries"])
    assert state["revision"] == 1 and state["refreshRequired"] is False
    assert state["generationSummary"] == {"validatedCount": 3, "addedCount": 3,
        "replacedCount": 0, "duplicateSkippedCount": 0, "capacitySkippedCount": 0}
    assert set(state) == {"projectId", "revision", "refreshRequired", "generationAvailable",
                          "queries", "generationSummary"}
    assert provider.contexts[0].question == "Question"
    assert provider.contexts[0].keywords == ("tutors", "feedback")
    assert client.get(path).json() == {k: v for k, v in state.items()
                                       if k != "generationSummary"}


@pytest.mark.parametrize("body", [{}, {"expectedRevision": "0"}, {"expectedRevision": -1},
    {"expectedRevision": True}, {"expectedRevision": 0, "researchQuestion": "CANARY"},
    {"expectedRevision": 0, "queries": ["CANARY"]}])
def test_FR_QRY_001_generate_rejects_caller_context_and_bad_revision(generation, body):
    provider = FakeSuggestionProvider()
    client, path = generation(provider)
    response = client.post(path + "/generate", json=body)
    assert response.status_code == 422 and "CANARY" not in response.text
    assert provider.contexts == [] and client.get(path).json()["queries"] == []


def test_FR_QRY_004_regeneration_preserves_owned_and_replaces_untouched(generation):
    provider = FakeSuggestionProvider(queries=("First", "Second", "Third"))
    client, path = generation(provider)
    state = client.post(path + "/generate", json={"expectedRevision": 0}).json()
    first, second, third = state["queries"]
    client.patch(f"{path}/{first['id']}", json={"expectedRevision": 1, "text": "Edited"})
    client.patch(f"{path}/{second['id']}", json={"expectedRevision": 2, "enabled": False})
    manual = client.post(path, json={"text": "Manual", "expectedRevision": 3}).json()
    provider.queries = ("edited", "New A", "New B", "New C")
    response = client.post(path + "/generate", json={"expectedRevision": 4})
    assert response.status_code == 200
    result = response.json()
    by_text = {q["text"]: q for q in result["queries"]}
    assert by_text["Edited"]["id"] == first["id"] and by_text["Edited"]["userOwned"]
    assert by_text["Second"]["enabled"] is False and by_text["Second"]["userOwned"]
    assert by_text["Manual"] == manual["queries"][-1]
    assert third["id"] not in {q["id"] for q in result["queries"]}
    assert [q["text"] for q in result["queries"]] == [
        "Edited", "Second", "New A", "Manual", "New B", "New C"]
    assert result["generationSummary"] == {"validatedCount": 4, "addedCount": 3,
        "replacedCount": 1, "duplicateSkippedCount": 1, "capacitySkippedCount": 0}


def test_FR_QRY_008_zero_slot_success_clears_notice_and_advances_revision(generation):
    client, path = generation(FakeSuggestionProvider(queries=("A new", "B new", "Query 0")))
    for i in range(20):
        client.post(path, json={"text": f"Query {i}", "enabled": i % 2 == 0,
                                "expectedRevision": i})
    parent = path.removesuffix("/queries")
    client.put(parent, json=dict(PROJECT, keywords=["tutors", "changed"]))
    before = client.get(path).json()
    assert before["refreshRequired"] is True and before["revision"] == 21
    result = client.post(path + "/generate", json={"expectedRevision": 21}).json()
    assert result["queries"] == before["queries"] and result["revision"] == 22
    assert result["refreshRequired"] is False
    assert result["generationSummary"] == {"validatedCount": 3, "addedCount": 0,
        "replacedCount": 0, "duplicateSkippedCount": 1, "capacitySkippedCount": 2}


@pytest.mark.parametrize("provider,status,code", [
    (None, 503, "SUGGESTIONS_UNAVAILABLE"),
    (FailingProvider("not_configured"), 503, "SUGGESTIONS_UNAVAILABLE"),
    (FailingProvider("unavailable"), 503, "SUGGESTIONS_UNAVAILABLE"),
    (FailingProvider("busy"), 503, "SUGGESTIONS_UNAVAILABLE"),
    (FailingProvider("timeout"), 504, "SUGGESTIONS_TIMEOUT"),
    (FailingProvider("invalid_output"), 502, "SUGGESTIONS_INVALID_OUTPUT"),
    (CrashingProvider(), 503, "SUGGESTIONS_UNAVAILABLE"),
    (UnvalidatedProvider(), 502, "SUGGESTIONS_INVALID_OUTPUT"),
])
def test_FR_QRY_005_failures_leave_complete_state_unchanged(generation, provider, status,
                                                            code, caplog):
    caplog.set_level(logging.DEBUG)
    client, path = generation(provider)
    client.post(path, json={"text": "Manual", "expectedRevision": 0})
    client.put(path.removesuffix("/queries"), json=dict(PROJECT, researchQuestion="New"))
    before = client.get(path).json()
    response = client.post(path + "/generate", json={"expectedRevision": before["revision"]})
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code and error["fields"] == []
    assert "CANARY" not in response.text and "CANARY" not in caplog.text
    assert client.get(path).json() == before and before["refreshRequired"] is True
    if isinstance(provider, FailingProvider):
        assert provider.calls == 1
    added = client.post(path, json={"text": "Still manual", "expectedRevision": 2})
    assert added.status_code == 201


def test_FR_QRY_007_generate_precedence_missing_parent_and_stale_revision(generation):
    provider = FakeSuggestionProvider()
    client, path = generation(provider)
    missing = client.post(f"/api/projects/{uuid4()}/queries/generate",
                          json={"expectedRevision": 0})
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
    client.post(path, json={"text": "Manual", "expectedRevision": 0})
    stale = client.post(path + "/generate", json={"expectedRevision": 0})
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "QUERY_REVISION_CHANGED"
    assert provider.contexts == []


def test_FR_QRY_005_unavailable_checked_after_parent_and_revision(generation):
    client, path = generation(None)
    assert client.post(f"/api/projects/{uuid4()}/queries/generate",
                       json={"expectedRevision": 0}).status_code == 404
    assert client.post(path + "/generate", json={"expectedRevision": 5}).status_code == 409


def test_FR_QRY_005_storage_failure_during_merge_is_sanitized(generation, db):
    provider = FakeSuggestionProvider(blocked=True)
    client, path = generation(provider)
    before = client.get(path).json()

    def fail(connection):
        raise OperationalError("CANARY", {}, RuntimeError("CANARY"))

    responses = []
    worker = threading.Thread(target=lambda: responses.append(
        client.post(path + "/generate", json={"expectedRevision": 0})))
    worker.start()
    assert provider.started.wait(5)
    event.listen(db.engine, "commit", fail, once=True)
    provider.release.set()
    worker.join(10)
    response = responses[0]
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
    assert "CANARY" not in response.text
    assert client.get(path).json() == before


def test_FR_QRY_001_generation_logs_typed_metadata_only(generation, caplog):
    class MetadataProvider(FakeSuggestionProvider):
        async def suggest(self, context):
            result = await super().suggest(context)
            return SuggestionResult(batch=result.batch, metadata=SuggestionMetadata(
                model="fake-model", promptVersion="fake_v1", durationSeconds=0.5,
                inputTokens=10, outputTokens=5, totalTokens=15))
    caplog.set_level(logging.DEBUG)
    client, path = generation(MetadataProvider(queries=("CANARY A", "CANARY B", "CANARY C")))
    project_id = path.split("/")[3]
    response = client.post(path + "/generate", json={"expectedRevision": 0})
    assert response.status_code == 200 and "fake-model" not in response.text
    assert "totalTokens" not in response.text
    assert project_id in caplog.text and "fake_v1" in caplog.text and "15" in caplog.text
    assert "CANARY" not in caplog.text and "Question" not in caplog.text


def test_FR_QRY_004_restored_queries_stay_owned_through_regeneration(generation):
    provider = FakeSuggestionProvider(queries=("First", "Second", "Third"))
    client, path = generation(provider)
    first, second, _ = client.post(path + "/generate",
                                   json={"expectedRevision": 0}).json()["queries"]
    client.patch(f"{path}/{first['id']}", json={"expectedRevision": 1, "text": "Edited"})
    client.patch(f"{path}/{first['id']}", json={"expectedRevision": 2, "text": "First"})
    client.patch(f"{path}/{second['id']}", json={"expectedRevision": 3, "enabled": False})
    client.patch(f"{path}/{second['id']}", json={"expectedRevision": 4, "enabled": True})
    provider.queries = ("Fourth", "Fifth", "Sixth")
    result = client.post(path + "/generate", json={"expectedRevision": 5}).json()
    kept = {q["id"]: q for q in result["queries"]}
    assert kept[first["id"]]["text"] == "First" and kept[first["id"]]["userOwned"]
    assert kept[second["id"]]["enabled"] and kept[second["id"]]["userOwned"]
    assert result["generationSummary"]["replacedCount"] == 1
