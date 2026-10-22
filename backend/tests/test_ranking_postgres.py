"""FR-RNK-006 additive schema and legacy preservation in guarded PostgreSQL."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from conftest import FakeEmbeddingProvider, run_async
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.persistence import Database
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError, OperationalError
from test_ranking_api import project_with_query
from test_retrieval_api import FakePaperProvider, paper
from test_retrieval_postgres import insert_paper, insert_project, insert_search_run


def legacy_row(connection):
    project_id = insert_project(connection)
    paper_id = insert_paper(connection)
    run_id = insert_search_run(connection, project_id)
    connection.execute(
        text("""INSERT INTO project_papers
        (project_id,paper_id,search_run_id,ordinal) VALUES (:p,:w,:r,0)"""),
        {"p": project_id, "w": paper_id, "r": run_id},
    )
    return project_id


def test_FR_RNK_006_upgrade_preserves_legacy_without_backfill(db):
    # Disposable fixture target only: reconstruct just this additive migration's pre-state.
    with db.engine.begin() as c:
        legacy_row(c)
        c.execute(text("ALTER TABLE project_papers DROP COLUMN IF EXISTS embedding_score"))
        c.execute(text("ALTER TABLE project_papers DROP COLUMN IF EXISTS ranking_provenance"))
        c.execute(text("ALTER TABLE search_runs DROP COLUMN IF EXISTS ranking_provenance"))
        c.execute(text("DELETE FROM schema_migrations WHERE version='004_local_ranking.sql'"))
    db.migrate()
    db.migrate()
    with db.engine.connect() as c:
        row = c.execute(text("SELECT * FROM project_papers")).mappings().one()
        assert row["embedding_score"] is None
        assert row["ranking_provenance"] is None
        assert row["ordinal"] == 0
        assert c.execute(text("SELECT title FROM papers")).scalar_one() == "A paper"
        assert c.execute(text("SELECT count(*) FROM schema_migrations")).scalar_one() == 5
    reopened = Database(str(db.engine.url.render_as_string(hide_password=False)))
    try:
        reopened.migrate()
        assert "embedding_score" in reopened.project_papers.c
        assert "ranking_provenance" in reopened.search_runs.c
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "score,provenance", [(1.1, "{}"), (-0.1, "{}"), (0.5, None), (None, "{}"), (0.5, "[]")]
)
def test_FR_RNK_006_sql_score_provenance_constraints(db, score, provenance):
    with db.engine.begin() as c:
        legacy_row(c)
    with pytest.raises(IntegrityError):
        with db.engine.begin() as c:
            c.execute(
                text(
                    "UPDATE project_papers SET embedding_score=:s, "
                    "ranking_provenance=CAST(:p AS jsonb)"
                ),
                {"s": score, "p": provenance},
            )


def test_FR_RNK_006_additive_migration_rolls_back(db):
    migration = Path("migrations/004_local_ranking.sql")
    assert migration.exists()
    with db.engine.connect() as c:
        transaction = c.begin()
        c.execute(text("ALTER TABLE project_papers DROP COLUMN embedding_score"))
        transaction.rollback()
        assert c.execute(text("SELECT embedding_score FROM project_papers LIMIT 1")).all() == []


class BarrierEmbeddings(FakeEmbeddingProvider):
    def __init__(self):
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()
        self.block_next = False

    async def embed(self, inputs):
        if self.block_next:
            self.block_next = False
            self.started.set()
            while not self.release.is_set():
                await asyncio.sleep(0.01)
        return await super().embed(inputs)


def test_FR_RNK_007_no_db_lock_and_expired_ranking_cannot_commit(db):
    embeddings = BarrierEmbeddings()
    papers = FakePaperProvider()
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        assert client.post(path + "/search").status_code == 200
        embeddings.block_next = True
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(client.post, path + "/search")
            try:
                assert embeddings.started.wait(3)
                # These parent-lock operations would hang if ranking held a transaction.
                assert client.get(path + "/papers").status_code == 200
                assert (
                    client.put(
                        path,
                        json={
                            "title": "Blocked",
                            "researchQuestion": "Changed",
                            "maxPaperCount": 5,
                        },
                    ).status_code
                    == 409
                )
                assert client.post(path + "/search").status_code == 409
                with db.engine.begin() as c:
                    seconds = c.execute(
                        text(
                            "SELECT extract(epoch from (lease_expires_at-started_at)) "
                            "FROM search_runs WHERE status='pending'"
                        )
                    ).scalar_one()
                    assert seconds == 240
                    c.execute(
                        text(
                            "UPDATE search_runs SET lease_expires_at=now()-interval '1 second' "
                            "WHERE status='pending'"
                        )
                    )
                papers.results = {"Search text": [paper("W2", "New owner result")]}
                newer = client.post(path + "/search")
                assert newer.status_code == 200
                embeddings.release.set()
                assert pending.result(timeout=5).status_code == 409
                assert client.get(path + "/papers").json()["papers"] == newer.json()["papers"]
            finally:
                embeddings.release.set()


def test_FR_RNK_007_commit_failure_rolls_back_scores_and_provider_updates(db):
    embeddings, papers = FakeEmbeddingProvider(), FakePaperProvider()
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        assert client.post(path + "/search").status_code == 200
        before = client.get(path + "/papers").json()["papers"]
        papers.results = {"Search text": [paper("W1", "Should roll back")]}

        def fail_insert(connection, cursor, statement, parameters, context, many):
            if statement.startswith("INSERT INTO project_papers"):
                raise OperationalError("redacted-test-only", None, Exception("never log"))

        event.listen(db.engine, "before_cursor_execute", fail_insert)
        try:
            assert client.post(path + "/search").status_code == 503
        finally:
            event.remove(db.engine, "before_cursor_execute", fail_insert)
        assert client.get(path + "/papers").json()["papers"] == before


def test_FR_RNK_007_cancel_ranking_records_failure_keeps_results(db):
    embeddings, papers = BarrierEmbeddings(), FakePaperProvider()
    with TestClient(
        create_app(
            db, suggestion_provider=None, paper_provider=papers, embedding_provider=embeddings
        )
    ) as client:
        path = project_with_query(client)
        assert client.post(path + "/search").status_code == 200
        before = client.get(path + "/papers").json()["papers"]
        embeddings.block_next = True

        async def cancel():
            from uuid import UUID

            task = asyncio.create_task(client.app.state.retrieval.search(UUID(path.split("/")[-1])))
            try:
                async with asyncio.timeout(3):
                    while not embeddings.started.is_set():
                        await asyncio.sleep(0.01)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            finally:
                if not task.done():
                    task.cancel()

        run_async(cancel())
        output = client.get(path + "/papers").json()
        assert output["papers"] == before
        assert output["latestAttempt"]["errorCode"] == "SEARCH_CANCELLED"
