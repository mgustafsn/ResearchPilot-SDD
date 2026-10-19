"""FR-RET-006–008 schema and migration tests using the guarded disposable DB."""

import asyncio
import json
import threading
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.paper_domain import Paper
from researchpilot.paper_provider import PaperProviderError, PaperSearchResult
from researchpilot.persistence import Database
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError, OperationalError


def insert_project(connection, project_id=None):
    project_id = project_id or uuid4()
    connection.execute(
        text("""
        INSERT INTO projects
            (id, title, research_question, keywords, year_from, year_to,
             max_paper_count, created_at, updated_at)
        VALUES (:id, 'Retrieval test', 'Research question', '[]', NULL, NULL,
                100, now(), now())
    """),
        {"id": project_id},
    )
    return project_id


def insert_paper(connection, paper_id=None, provider_id="W1", **overrides):
    paper_id = paper_id or uuid4()
    values = {
        "id": paper_id,
        "provider": "openalex",
        "provider_id": provider_id,
        "doi": None,
        "title": "A paper",
        "abstract": None,
        "authors": "[]",
        "publication_year": None,
        "publication_date": None,
        "venue": None,
        "citation_count": None,
        "source_url": "https://openalex.org/W1",
        "publication_url": None,
        "full_text_url": None,
        "is_open_access": None,
    }
    values.update(overrides)
    columns = ", ".join(values)
    parameters = ", ".join(f":{name}" for name in values)
    connection.execute(text(f"INSERT INTO papers ({columns}) VALUES ({parameters})"), values)
    return paper_id


def insert_search_run(connection, project_id, run_id=None, token=None):
    run_id, token = run_id or uuid4(), token or uuid4()
    connection.execute(
        text("""
        INSERT INTO search_runs
            (id, project_id, input_snapshot, status, ownership_token, lease_expires_at,
             started_at, raw_fetched_count, skipped_count, duplicate_count,
             queries_used, queries_unused)
        VALUES (:id, :project_id, CAST(:snapshot AS jsonb), 'pending', :token,
                now() + interval '150 seconds', now(), 0, 0, 0, '[]', '[]')
    """),
        {"id": run_id, "project_id": project_id, "snapshot": json.dumps({"x": 1}), "token": token},
    )
    return run_id


class FakePaperProvider:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    async def search(self, query, year_from, year_to, limit):
        self.calls.append((query, year_from, year_to, limit))
        papers = self.results.pop(0)
        return PaperSearchResult(papers=papers, raw_count=len(papers), request_count=1)


class BarrierPaperProvider:
    def __init__(self, papers=None, block_first=False):
        self.papers = list(papers or [paper("W1", "Paper")])
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        if not block_first:
            self.release.set()

    async def search(self, query, year_from, year_to, limit):
        self.calls += 1
        call = self.calls
        self.started.set()
        if call == 1 and not await asyncio.to_thread(self.release.wait, 5):
            raise PaperProviderError("timeout")
        selected = self.papers[min(call - 1, len(self.papers) - 1)]
        return PaperSearchResult(papers=[selected], raw_count=1, request_count=1)


def paper(provider_id, title):
    return Paper.model_validate(
        {
            "provider": "openalex",
            "provider_id": provider_id,
            "doi": None,
            "title": title,
            "source_url": f"https://openalex.org/{provider_id}",
            "authors": [],
        }
    )


def test_FR_RET_006_007_migration_003_is_versioned_repeatable_and_reflected(db_url):
    database = Database(db_url)
    try:
        database.migrate()
        database.migrate()
        with database.engine.connect() as connection:
            versions = set(
                connection.execute(text("SELECT version FROM schema_migrations")).scalars()
            )
            tables = {
                connection.execute(text("SELECT to_regclass(:name)"), {"name": name}).scalar_one()
                for name in ("papers", "project_papers", "search_runs")
            }
        assert versions == {"001_projects.sql", "002_search_queries.sql", "003_paper_retrieval.sql"}
        assert tables == {"papers", "project_papers", "search_runs"}
        assert database.papers.name == "papers"
        assert database.project_papers.name == "project_papers"
        assert database.search_runs.name == "search_runs"
    finally:
        database.close()


def test_FR_RET_006_paper_and_search_run_constraints(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        insert_paper(connection, provider_id="W1")
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO papers
                    (id, provider, provider_id, title, source_url, updated_at)
                VALUES (:id, 'openalex', 'W2', '', 'https://openalex.org/W2', now())
            """),
                {"id": uuid4()},
            )
    with db.engine.begin() as connection:
        run_id = insert_search_run(connection, project_id)
        assert (
            connection.execute(
                text("SELECT status FROM search_runs WHERE id=:id"), {"id": run_id}
            ).scalar_one()
            == "pending"
        )


def test_FR_RET_006_008_only_one_pending_run_per_project(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        insert_search_run(connection, project_id)
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            insert_search_run(connection, project_id)


def test_FR_RET_007_project_paper_relations_are_scoped_unique_and_cascade(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        run_id = insert_search_run(connection, project_id)
        paper_id = insert_paper(connection)
        connection.execute(
            text("""
            INSERT INTO project_papers (project_id, paper_id, search_run_id, ordinal)
            VALUES (:project, :paper, :run, 0)
        """),
            {"project": project_id, "paper": paper_id, "run": run_id},
        )
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO project_papers (project_id, paper_id, search_run_id, ordinal)
                VALUES (:project, :paper, :run, 1)
            """),
                {"project": project_id, "paper": paper_id, "run": run_id},
            )
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM projects WHERE id=:id"), {"id": project_id})
        assert connection.execute(text("SELECT count(*) FROM project_papers")).scalar_one() == 0


def test_FR_RET_006_007_success_persists_run_snapshot_and_replaces_results(db):
    provider = FakePaperProvider(
        [
            [paper("W1", "First"), paper("W2", "Second")],
            [paper("W3", "Replacement")],
        ]
    )
    values = {
        "title": "Persistence",
        "researchQuestion": "Not sent",
        "keywords": ["Private"],
        "yearFrom": 2020,
        "yearTo": 2024,
        "maxPaperCount": 2,
    }
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=provider)) as client:
        project = client.post("/api/projects", json=values).json()
        query_path = f"/api/projects/{project['id']}/queries"
        client.post(query_path, json={"text": "Search phrase", "expectedRevision": 0})
        path = f"/api/projects/{project['id']}"
        first = client.post(f"{path}/search")
        assert first.status_code == 200, first.text
        second = client.post(f"{path}/search")
        assert second.status_code == 200, second.text

    with db.engine.connect() as connection:
        papers = (
            connection.execute(text("SELECT provider_id FROM papers ORDER BY provider_id"))
            .scalars()
            .all()
        )
        current = (
            connection.execute(
                text("""
            SELECT p.provider_id FROM project_papers pp JOIN papers p ON p.id=pp.paper_id
            WHERE pp.project_id=:project ORDER BY pp.ordinal
        """),
                {"project": project["id"]},
            )
            .scalars()
            .all()
        )
        runs = connection.execute(
            text("""
            SELECT status, input_snapshot->>'researchQuestion' AS question,
                   input_snapshot->'enabledQueries' AS queries
            FROM search_runs WHERE project_id=:project ORDER BY started_at
        """),
            {"project": project["id"]},
        ).all()
    assert papers == ["W3"]
    assert current == ["W3"]
    assert [run.status for run in runs] == ["succeeded", "succeeded"]
    assert runs[0].question == "Not sent" and runs[0].queries[0]["text"] == "Search phrase"
    assert provider.calls == [("Search phrase", 2020, 2024, 2)] * 2


def test_FR_RET_007_successful_empty_search_removes_associations(db):
    provider = FakePaperProvider([[paper("W1", "Old")], []])
    values = {"title": "Empty", "researchQuestion": "Question", "maxPaperCount": 1}
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=provider)) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        query_path = f"{path}/queries"
        client.post(query_path, json={"text": "Query", "expectedRevision": 0})
        assert client.post(f"{path}/search").json()["papers"]
        empty = client.post(f"{path}/search")
        assert empty.status_code == 200 and empty.json()["papers"] == []
    with db.engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM project_papers WHERE project_id=:id"),
                {"id": project["id"]},
            ).scalar_one()
            == 0
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "project_update",
        "project_delete",
        "query_add",
        "query_patch",
        "query_delete",
    ],
)
def test_FR_RET_008_project_and_query_mutations_conflict_during_active_search(db, mutation):
    provider = BarrierPaperProvider(block_first=True)
    values = {"title": "Locked", "researchQuestion": "Question", "maxPaperCount": 10}
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=provider)) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        query_path = f"{path}/queries"
        query = client.post(query_path, json={"text": "Original", "expectedRevision": 0}).json()[
            "queries"
        ][0]
        replies = []
        worker = threading.Thread(target=lambda: replies.append(client.post(f"{path}/search")))
        worker.start()
        assert provider.started.wait(5)
        assert client.get(query_path).status_code == 200  # No transaction spans provider wait.
        if mutation == "project_update":
            response = client.put(path, json=dict(values, title="Changed"))
        elif mutation == "project_delete":
            response = client.delete(path)
        elif mutation == "query_add":
            response = client.post(query_path, json={"text": "Another", "expectedRevision": 1})
        elif mutation == "query_patch":
            response = client.patch(
                f"{query_path}/{query['id']}", json={"expectedRevision": 1, "text": "Changed"}
            )
        else:
            response = client.delete(f"{query_path}/{query['id']}?expectedRevision=1")
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "SEARCH_ACTIVE"
        provider.release.set()
        worker.join(10)
        assert replies[0].status_code == 200


def test_FR_RET_008_expired_owner_cannot_replace_newer_attempt(db):
    provider = BarrierPaperProvider(
        papers=[paper("W1", "Late result"), paper("W2", "Current result")],
        block_first=True,
    )
    values = {"title": "Lease", "researchQuestion": "Question", "maxPaperCount": 1}
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=provider)) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        client.post(f"{path}/queries", json={"text": "Query", "expectedRevision": 0})
        old_responses = []
        old_worker = threading.Thread(
            target=lambda: old_responses.append(client.post(f"{path}/search"))
        )
        old_worker.start()
        assert provider.started.wait(5)
        with db.engine.begin() as connection:
            connection.execute(
                text("""
                UPDATE search_runs SET lease_expires_at=now() - interval '1 second'
                WHERE project_id=:project AND status='pending'
            """),
                {"project": project["id"]},
            )
        newer = client.post(f"{path}/search")
        assert newer.status_code == 200, newer.text
        assert [paper["providerId"] for paper in newer.json()["papers"]] == ["W2"]
        provider.release.set()
        old_worker.join(10)
        assert old_responses[0].status_code == 409
        assert old_responses[0].json()["error"]["code"] == "SEARCH_STALE"
        current = client.get(f"{path}/papers").json()
        assert [paper["providerId"] for paper in current["papers"]] == ["W2"]


def test_FR_RET_006_expired_pending_attempt_is_recovered_on_current_results_read(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        run_id = insert_search_run(connection, project_id)
        connection.execute(
            text("""
            UPDATE search_runs SET lease_expires_at=now() - interval '1 second' WHERE id=:id
        """),
            {"id": run_id},
        )
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=None)) as client:
        output = client.get(f"/api/projects/{project_id}/papers")
        assert output.status_code == 200
        assert output.json()["latestAttempt"]["status"] == "failed"
        assert output.json()["latestAttempt"]["errorCode"] == "SEARCH_EXPIRED"


def test_FR_RET_007_failed_result_commit_preserves_previous_associations(db):
    provider = FakePaperProvider(
        [
            [paper("W1", "Old result")],
            [paper("W2", "Uncommitted replacement")],
        ]
    )
    values = {"title": "Rollback", "researchQuestion": "Question", "maxPaperCount": 1}
    with TestClient(create_app(db, suggestion_provider=None, paper_provider=provider)) as client:
        project = client.post("/api/projects", json=values).json()
        path = f"/api/projects/{project['id']}"
        client.post(f"{path}/queries", json={"text": "Query", "expectedRevision": 0})
        first = client.post(f"{path}/search")
        assert first.status_code == 200
        before = client.get(f"{path}/papers").json()["papers"]

        def fail_association_insert(connection, cursor, statement, parameters, context, many):
            if "insert into project_papers" in statement.casefold():
                raise OperationalError("injected", {}, RuntimeError("CANARY"))

        event.listen(db.engine, "before_cursor_execute", fail_association_insert)
        try:
            failed = client.post(f"{path}/search")
        finally:
            event.remove(db.engine, "before_cursor_execute", fail_association_insert)

        assert failed.status_code == 503
        assert failed.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
        assert "CANARY" not in failed.text
        after = client.get(f"{path}/papers").json()
        assert after["papers"] == before
        assert after["latestAttempt"]["status"] == "failed"
