"""FR-RNK-001–009 Search integration with fakes and real guarded storage."""

import pytest
from conftest import FakeEmbeddingProvider
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from sqlalchemy import text
from test_retrieval_api import PROJECT, FakePaperProvider, paper


def project_with_query(client):
    project = client.post("/api/projects", json=PROJECT).json()
    path = f"/api/projects/{project['id']}"
    assert (
        client.post(
            path + "/queries", json={"text": "Search text", "expectedRevision": 0}
        ).status_code
        == 201
    )
    return path


def test_FR_RNK_001_004_006_ranked_search_and_restart(db):
    embeddings = FakeEmbeddingProvider()
    papers = FakePaperProvider({"Search text": [paper("W1", "Title only")]})
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        output = client.post(path + "/search")
        assert output.status_code == 200, output.text
        result = output.json()["papers"][0]
        assert 0 <= result["embeddingScore"] <= 1
        assert result["rankingProvenance"]["dimension"] == 384
        assert result["rankingProvenance"]["searchRunId"] == output.json()["searchRunId"]
        assert len(result["rankingProvenance"]["inputHash"]) == 64
        assert embeddings.calls[0][0].text == "Private question not sent\nKeywords: private keyword"
        assert embeddings.calls[0][1].text == "Title only"
        assert output.json()["rankingProvenance"]["rankedPaperCount"] == 1
    with TestClient(
        create_app(db, suggestion_provider=None, paper_provider=None, embedding_provider=embeddings)
    ) as client:
        current = client.get(path + "/papers").json()
        assert current["papers"] == [result]
        assert len(embeddings.calls) == 1


@pytest.mark.parametrize(
    "category,status",
    [
        ("model_missing", 503),
        ("model_invalid", 503),
        ("busy", 503),
        ("timeout", 504),
        ("invalid_response", 502),
        ("unavailable", 503),
    ],
)
def test_FR_RNK_007_failed_ranking_keeps_old_results(db, category, status):
    embeddings = FakeEmbeddingProvider()
    papers = FakePaperProvider()
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        assert client.post(path + "/search").status_code == 200
        before = client.get(path + "/papers").json()["papers"]
        embeddings.failure = category
        failed = client.post(path + "/search")
        assert failed.status_code == status
        assert failed.json()["error"]["code"] == "EMBEDDING_" + category.upper()
        current = client.get(path + "/papers").json()
        assert current["papers"] == before
        assert current["latestAttempt"]["status"] == "failed"
        assert current["latestAttempt"]["rankingProvenance"] is None
        with db.engine.connect() as c:
            assert c.execute(text("SELECT title FROM papers")).scalar_one() == "Provider title"


def test_FR_RNK_007_successful_empty_without_model(db):
    embeddings = FakeEmbeddingProvider()
    embeddings.failure = "model_missing"
    papers = FakePaperProvider({"Search text": []})
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        output = client.post(path + "/search")
        assert output.status_code == 200, output.text
        assert output.json()["papers"] == []
        assert output.json()["rankingProvenance"] is None
        assert not embeddings.calls


def test_FR_RNK_006_legacy_nulls_and_reads_do_not_rank(db):
    from test_ranking_postgres import legacy_row

    with db.engine.begin() as c:
        project_id = legacy_row(c)
    embeddings = FakeEmbeddingProvider()
    with TestClient(
        create_app(db, suggestion_provider=None, paper_provider=None, embedding_provider=embeddings)
    ) as client:
        result = client.get(f"/api/projects/{project_id}/papers").json()["papers"][0]
        assert result["embeddingScore"] is None and result["rankingProvenance"] is None
        assert not embeddings.calls


def test_FR_RNK_007_overall_deadline_has_search_error(db, monkeypatch):
    import asyncio

    from researchpilot import retrieval_service

    class SlowEmbeddings(FakeEmbeddingProvider):
        async def embed(self, inputs):
            await asyncio.sleep(0.1)
            return await super().embed(inputs)

    embeddings = SlowEmbeddings()
    with TestClient(
        create_app(
            db,
            suggestion_provider=None,
            paper_provider=FakePaperProvider(),
            embedding_provider=embeddings,
        )
    ) as client:
        path = project_with_query(client)
        monkeypatch.setattr(retrieval_service, "PIPELINE_TIMEOUT_SECONDS", 0.03)
        response = client.post(path + "/search")
        assert response.status_code == 504
        assert response.json()["error"]["code"] == "SEARCH_TIMEOUT"


def test_FR_RNK_002_invalid_vectors_and_logs_preserve_old_scores(db, caplog):
    import logging

    class MalformedEmbeddings(FakeEmbeddingProvider):
        bad = False

        async def embed(self, inputs):
            batch = await super().embed(inputs)
            if self.bad:
                batch.items[0].vector[0] = float("nan")
            return batch

    embeddings = MalformedEmbeddings()
    with TestClient(
        create_app(
            db,
            suggestion_provider=None,
            paper_provider=FakePaperProvider(),
            embedding_provider=embeddings,
        )
    ) as client:
        path = project_with_query(client)
        assert client.post(path + "/search").status_code == 200
        before = client.get(path + "/papers").json()["papers"]
        embeddings.bad = True
        with caplog.at_level(logging.INFO, logger="researchpilot"):
            assert client.post(path + "/search").status_code == 502
        assert client.get(path + "/papers").json()["papers"] == before
        assert "Private question not sent" not in caplog.text
        assert "private keyword" not in caplog.text


def test_FR_RNK_004_005_sort_and_retain_zero_scores(db):
    class SelectedEmbeddings(FakeEmbeddingProvider):
        async def embed(self, inputs):
            result = await super().embed(inputs)
            for item, vector in zip(
                result.items, ([1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0]), strict=True
            ):
                item.vector = list(vector) + [0.0] * 382
            return result

    records = [
        paper("W3", "alpha").model_copy(update={"doi": "10.1234/3"}),
        paper("W2", "Zebra").model_copy(update={"doi": "10.1234/2"}),
        paper("W1", "Alpha").model_copy(update={"doi": "10.1234/1"}),
    ]
    with TestClient(
        create_app(
            db,
            suggestion_provider=None,
            paper_provider=FakePaperProvider({"Search text": records}),
            embedding_provider=SelectedEmbeddings(),
        )
    ) as client:
        path = project_with_query(client)
        output = client.post(path + "/search").json()
        assert [p["providerId"] for p in output["papers"]] == ["W2", "W1", "W3"]
        assert [p["embeddingScore"] for p in output["papers"]] == [1, 0, 0]
        assert client.get(path + "/papers").json()["papers"] == output["papers"]
