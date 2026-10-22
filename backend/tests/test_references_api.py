"""FR-REF-001–008 reference API journeys using fake PaperProviders."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from conftest import FakeEmbeddingProvider
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from test_retrieval_api import PROJECT, FakePaperProvider, paper


def project_with_result(client, provider, title="Provider title"):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}"
    assert (
        client.post(
            path + "/queries",
            json={
                "text": "Search phrase",
                "expectedRevision": 0,
            },
        ).status_code
        == 201
    )
    provider.results["Search phrase"] = [paper("W1", title)]
    result = client.post(path + "/search")
    assert result.status_code == 200, result.text
    return path, result.json()["papers"][0]


def client_for(db, provider):
    return TestClient(
        create_app(
            db,
            suggestion_provider=None,
            paper_provider=provider,
            embedding_provider=FakeEmbeddingProvider(),
        )
    )


def test_FR_REF_001_002_003_first_save_and_duplicate_preserve_provider_snapshot(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "Original title")]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider, "Original title")
        first = client.post(path + "/references", json={"paperId": result["id"]})
        assert first.status_code == 201, first.text
        saved = first.json()
        assert saved["title"] == "Original title"
        assert saved["providerId"] == "W1"
        assert "embeddingScore" not in saved

        provider.results["Search phrase"] = [paper("W1", "Refreshed provider title")]
        assert client.post(path + "/search").status_code == 200
        duplicate = client.post(path + "/references", json={"paperId": result["id"]})
        assert duplicate.status_code == 200
        assert duplicate.json() == saved

        listing = client.get(path + "/references")
        assert listing.status_code == 200
        assert listing.json()["references"] == [saved]
        current = client.get(path + "/papers").json()["papers"]
        assert current[0]["title"] == "Refreshed provider title"


def test_FR_REF_001_007_save_only_accepts_current_project_result(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "One project")]})
    with client_for(db, provider) as client:
        first_path, first_paper = project_with_result(client, provider)
        other_project = client.post("/api/projects", json=PROJECT).json()
        other_path = f"/api/projects/{other_project['id']}"
        cross_project = client.post(
            other_path + "/references",
            json={
                "paperId": first_paper["id"],
            },
        )
        assert cross_project.status_code == 404
        assert cross_project.json()["error"]["code"] == "PAPER_NOT_FOUND"
        unknown = client.post(first_path + "/references", json={"paperId": str(uuid4())})
        assert unknown.status_code == 404


def test_FR_REF_006_remove_does_not_remove_search_result(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "Keep search paper")]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        saved = client.post(path + "/references", json={"paperId": result["id"]})
        assert saved.status_code == 201, saved.text
        removed = client.delete(path + f"/references/{saved.json()['id']}")
        assert removed.status_code == 204
        assert client.get(path + "/references").json()["references"] == []
        assert client.get(path + "/papers").json()["papers"][0]["id"] == result["id"]


def test_FR_REF_006_reference_is_available_after_application_restart(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "Survives restart")]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        saved = client.post(path + "/references", json={"paperId": result["id"]})
        assert saved.status_code == 201
        expected = saved.json()
    with client_for(db, provider) as reopened:
        assert reopened.get(path + "/references").json()["references"] == [expected]


def test_FR_REF_006_cross_project_reference_ids_are_not_disclosed_or_deleted(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "Scoped paper")]})
    with client_for(db, provider) as client:
        owner_path, result = project_with_result(client, provider)
        saved = client.post(owner_path + "/references", json={"paperId": result["id"]})
        other = client.post("/api/projects", json=PROJECT).json()
        other_path = f"/api/projects/{other['id']}"
        reference_id = saved.json()["id"]
        assert client.get(other_path + "/references").json()["references"] == []
        removed = client.delete(other_path + f"/references/{reference_id}")
        assert removed.status_code == 404
        assert removed.json()["error"]["code"] == "REFERENCE_NOT_FOUND"
        assert client.get(owner_path + "/references").json()["references"] == [saved.json()]


def test_FR_REF_007_saves_reject_during_search_but_list_and_remove_remain_available(db):
    provider = BlockingPaperProvider()
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        saved = client.post(path + "/references", json={"paperId": result["id"]})
        assert saved.status_code == 201
        provider.block_next = True
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(client.post, path + "/search")
            try:
                assert provider.started.wait(3)
                rejected = client.post(path + "/references", json={"paperId": result["id"]})
                assert rejected.status_code == 409
                assert rejected.json()["error"]["code"] == "SEARCH_ACTIVE"
                assert client.get(path + "/references").status_code == 200
                removed = client.delete(path + f"/references/{saved.json()['id']}")
                assert removed.status_code == 204
            finally:
                provider.release.set()
            assert pending.result(timeout=5).status_code == 200


def test_FR_REF_007_save_expires_stale_search_owner_then_succeeds(db):
    from sqlalchemy import text
    from test_retrieval_postgres import insert_search_run

    provider = FakePaperProvider({"Search phrase": [paper("W1", "Provider title")]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        project_id = path.rsplit("/", 1)[-1]
        with db.engine.begin() as connection:
            run_id = insert_search_run(connection, project_id)
            connection.execute(
                text("""
                UPDATE search_runs SET lease_expires_at=now()-interval '1 second'
                WHERE id=:id
            """),
                {"id": run_id},
            )
        saved = client.post(path + "/references", json={"paperId": result["id"]})
        assert saved.status_code == 201, saved.text
        with db.engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT status FROM search_runs WHERE id=:id"), {"id": run_id}
                ).scalar_one()
                == "failed"
            )


class BlockingPaperProvider(FakePaperProvider):
    def __init__(self):
        super().__init__({"Search phrase": [paper("W1", "Provider title")]})
        self.started = threading.Event()
        self.release = threading.Event()
        self.block_next = False

    async def search(self, query, year_from, year_to, limit):
        if self.block_next:
            self.block_next = False
            self.started.set()
            if not await asyncio.to_thread(self.release.wait, 5):
                raise RuntimeError("test provider timeout")
        return await super().search(query, year_from, year_to, limit)


def test_FR_REF_008_client_cannot_supply_metadata_or_reference_id(db):
    provider = FakePaperProvider({"Search phrase": [paper()]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        response = client.post(
            path + "/references",
            json={
                "paperId": result["id"],
                "title": "Client-created citation",
            },
        )
        assert response.status_code == 422
        assert client.get(path + "/references").json()["references"] == []
