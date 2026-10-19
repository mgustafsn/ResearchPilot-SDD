"""FR-RET-001/002/006/009 API behavior with an injected fake provider."""

import asyncio
import logging
import threading
from datetime import date

from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.paper_domain import Paper
from researchpilot.paper_provider import PaperProviderError, PaperSearchResult

PROJECT = {
    "title": "Retrieval project",
    "researchQuestion": "Private question not sent",
    "keywords": ["private keyword"],
    "yearFrom": 2020,
    "yearTo": 2024,
    "maxPaperCount": 5,
}


def paper(provider_id="W1", title="Provider title"):
    return Paper.model_validate(
        {
            "provider": "openalex",
            "provider_id": provider_id,
            "doi": "10.1234/work",
            "title": title,
            "source_url": f"https://openalex.org/{provider_id}",
            "authors": ["Provider Author"],
            "citation_count": 2,
            "publication_year": 2022,
            "publication_date": date(2022, 3, 4),
            "venue": "Provider Journal",
            "is_open_access": None,
        }
    )


class FakePaperProvider:
    def __init__(self, results=None):
        self.calls = []
        self.results = results or {}
        self.fail_category = None

    async def search(self, query, year_from, year_to, limit):
        self.calls.append((query, year_from, year_to, limit))
        if self.fail_category:
            raise PaperProviderError(self.fail_category)
        papers = self.results.get(query, [paper()])
        return PaperSearchResult(papers=papers, raw_count=len(papers), request_count=1)


class BlockingProvider:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()

    async def search(self, query, year_from, year_to, limit):
        self.started.set()
        if not await asyncio.to_thread(self.release.wait, 5):
            raise PaperProviderError("timeout")
        return PaperSearchResult(papers=[paper()], raw_count=1, request_count=1)


def app_client(db, provider):
    return TestClient(create_app(db, suggestion_provider=None, paper_provider=provider))


def test_FR_RET_001_002_search_uses_exact_enabled_queries_and_inclusive_bounds(db):
    provider = FakePaperProvider()
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=PROJECT).json()
        path = f"/api/projects/{project['id']}"
        queries = f"{path}/queries"
        client.post(queries, json={"text": "AI tutors", "expectedRevision": 0})
        second = client.post(queries, json={"text": "Excluded query", "expectedRevision": 1}).json()
        q2 = second["queries"][1]
        disabled = client.patch(
            f"{queries}/{q2['id']}", json={"expectedRevision": 2, "enabled": False}
        )
        assert disabled.status_code == 200

        response = client.post(f"{path}/search")
        assert response.status_code == 200, response.text
        output = response.json()
        assert provider.calls == [("AI tutors", 2020, 2024, 5)]
        assert output["queriesUsed"] == [{"text": "AI tutors", "allocatedLimit": 5}]
        assert output["queriesUnused"] == []
        assert output["papers"][0]["providerId"] == "W1"
        assert output["papers"][0]["sourceUrl"] == "https://openalex.org/W1"
        assert "Private question not sent" not in response.text
        assert "private keyword" not in response.text
        assert output["status"] == "succeeded"


def test_FR_RET_006_get_current_papers_never_triggers_search(db):
    provider = FakePaperProvider()
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=PROJECT).json()
        response = client.get(f"/api/projects/{project['id']}/papers")
        assert response.status_code == 200
        assert provider.calls == []


def test_FR_RET_002_no_enabled_query_rejects_without_provider_call(db):
    provider = FakePaperProvider()
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=PROJECT).json()
        path = f"/api/projects/{project['id']}/queries"
        created = client.post(path, json={"text": "Disabled", "expectedRevision": 0}).json()
        query_id = created["queries"][0]["id"]
        client.patch(f"{path}/{query_id}", json={"expectedRevision": 1, "enabled": False})
        response = client.post(f"/api/projects/{project['id']}/search")
        assert response.status_code == 422
        assert provider.calls == []


def test_FR_RET_002_allocations_match_paper_limit_and_stored_query_order(db):
    provider = FakePaperProvider()
    values = dict(PROJECT, maxPaperCount=2)
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}/queries"
        client.post(path, json={"text": "Query first", "expectedRevision": 0})
        client.post(path, json={"text": "Query second", "expectedRevision": 1})
        response = client.post(f"/api/projects/{project['id']}/search")
        assert response.status_code == 200, response.text
        assert provider.calls == [("Query first", 2020, 2024, 1), ("Query second", 2020, 2024, 1)]
        assert response.json()["rawFetchedCount"] == 2


def test_FR_RET_007_provider_failure_preserves_old_results_and_records_safe_failure(db):
    provider = FakePaperProvider({"AI tutors": [paper("W1", "Existing result")]})
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=PROJECT).json()
        path = f"/api/projects/{project['id']}"
        query_path = f"{path}/queries"
        client.post(query_path, json={"text": "AI tutors", "expectedRevision": 0})
        initial = client.post(f"{path}/search")
        assert initial.status_code == 200
        before = client.get(f"{path}/papers").json()["papers"]
        provider.fail_category = "rate_limited"
        failure = client.post(f"{path}/search")
        after = client.get(f"{path}/papers").json()
        assert failure.status_code == 503
        assert failure.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
        assert "AI tutors" not in failure.text
        assert after["papers"] == before
        assert after["latestAttempt"]["status"] == "failed"
        assert after["latestAttempt"]["errorCode"] == "PROVIDER_UNAVAILABLE"


def test_FR_RET_001_006_search_query_and_project_context_never_enter_logs(db, caplog):
    caplog.set_level(logging.DEBUG)
    provider = FakePaperProvider()
    values = dict(
        PROJECT, researchQuestion="PRIVATE project question", keywords=["PRIVATE project keyword"]
    )
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        client.post(
            f"{path}/queries", json={"text": "PRIVATE stored search phrase", "expectedRevision": 0}
        )
        result = client.post(f"{path}/search")
        assert result.status_code == 200
        assert "PRIVATE" not in caplog.text


def test_FR_RET_008_second_search_conflicts_but_reads_remain_available(db):
    provider = BlockingProvider()
    with app_client(db, provider) as client:
        project = client.post("/api/projects", json=PROJECT).json()
        path = f"/api/projects/{project['id']}"
        client.post(f"{path}/queries", json={"text": "AI tutors", "expectedRevision": 0})
        responses = []
        worker = threading.Thread(target=lambda: responses.append(client.post(f"{path}/search")))
        worker.start()
        assert provider.started.wait(5)
        current = client.get(f"{path}/papers")
        conflict = client.post(f"{path}/search")
        assert current.status_code == 200
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "SEARCH_ACTIVE"
        provider.release.set()
        worker.join(10)
        assert responses[0].status_code == 200


def test_FR_RET_006_failed_multi_query_attempt_persists_completed_query_counts(db):
    class PartialFailureProvider:
        async def search(self, query, year_from, year_to, limit):
            if query == "Query first":
                return PaperSearchResult(papers=[paper()], raw_count=1, request_count=1)
            await asyncio.sleep(0.02)
            raise PaperProviderError("rate_limited")

    values = dict(PROJECT, maxPaperCount=2)
    with app_client(db, PartialFailureProvider()) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        query_path = f"{path}/queries"
        client.post(query_path, json={"text": "Query first", "expectedRevision": 0})
        client.post(query_path, json={"text": "Query second", "expectedRevision": 1})
        response = client.post(f"{path}/search")
        assert response.status_code == 503
        current = client.get(f"{path}/papers").json()
        assert current["latestAttempt"]["status"] == "failed"
        assert current["latestAttempt"]["rawFetchedCount"] == 1
        assert current["papers"] == []
