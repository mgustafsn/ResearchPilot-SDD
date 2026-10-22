"""PostgreSQL-specific evidence for FR-PRJ-002–007 and SC-PRJ-003."""

import pytest
import researchpilot.persistence as persistence
from conftest import require_safe_test_database
from fastapi.testclient import TestClient
from researchpilot.api import create_app
from researchpilot.persistence import Database
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError


@pytest.mark.parametrize("url,app,opt_in", [
    ("postgresql+psycopg://localhost/researchpilot_sdd_test", "", "0"),
    ("postgresql+psycopg://localhost/researchpilot_sdd", "", "1"),
    ("sqlite:///researchpilot_sdd_test", "", "1"),
    ("bad-secret-url", "", "1"),
    ("postgresql+psycopg://localhost/researchpilot_sdd_test", "", "1"),
    ("postgresql+psycopg://remote.invalid/researchpilot_sdd_test",
     "postgresql://localhost/researchpilot_sdd", "1"),
    ("postgresql+psycopg://one:secret@localhost/researchpilot_sdd_test",
     "postgresql://two:other@127.0.0.1:5432/researchpilot_sdd_test", "1"),
])
def test_NFR_PRJ_001_safety_refuses_unsafe_targets(url, app, opt_in):
    with pytest.raises(RuntimeError, match="^Refusing unsafe test database configuration$"):
        require_safe_test_database(url, app, opt_in)


def test_NFR_PRJ_001_safety_allows_separate_database():
    url = "postgresql+psycopg://localhost/researchpilot_sdd_test"
    assert require_safe_test_database(url, "postgresql://localhost/researchpilot_sdd", "1") == url


@pytest.mark.parametrize("url", [
    "sqlite:///projects.sqlite", "postgresql+psycopg://localhost/original_project",
    "postgresql+psycopg://remote.invalid/researchpilot_sdd",
])
def test_NFR_PRJ_001_runtime_refuses_nonlocal_or_unrelated_database(url):
    with pytest.raises(RuntimeError, match="^Use the dedicated local ResearchPilot database$"):
        Database(url)


def test_FR_PRJ_006_migrations_are_versioned_and_repeatable(db_url):
    database = Database(db_url)
    try:
        database.migrate()
        database.migrate()
        with database.engine.connect() as connection:
            versions = connection.execute(text("SELECT version FROM schema_migrations")).scalars()
            assert sorted(versions) == ["001_projects.sql", "002_search_queries.sql",
                                        "003_paper_retrieval.sql", "004_local_ranking.sql"]
    finally:
        database.close()


def insert_project(connection, **overrides):
    values = dict(title="Persisted", question="A question", count=100, start=None, end=None)
    values.update(overrides)
    return connection.execute(text("""
        INSERT INTO projects
            (id, title, research_question, keywords, year_from, year_to,
             max_paper_count, created_at, updated_at)
        VALUES ('11111111-1111-4111-8111-111111111111', :title, :question, '[]',
                :start, :end, :count, now(), now()) RETURNING id
    """), values).scalar_one()


def test_FR_PRJ_006_reconnect_and_migrate_preserve_data(db, db_url):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
    db.close()
    restarted = Database(db_url)
    try:
        restarted.migrate()
        with restarted.engine.connect() as connection:
            assert connection.execute(text("SELECT id FROM projects")).scalar_one() == project_id
    finally:
        restarted.close()


@pytest.mark.parametrize("overrides", [
    {"title": ""}, {"title": "x" * 201}, {"question": ""}, {"question": "x" * 5001},
    {"count": 0}, {"count": 251}, {"start": 0}, {"end": 10000}, {"start": 2026, "end": 2020},
])
def test_FR_PRJ_002_004_005_database_constraints(db, overrides):
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            insert_project(connection, **overrides)
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM projects")).scalar_one() == 0


def test_FR_PRJ_007_transaction_rolls_back(db):
    with pytest.raises(RuntimeError, match="injected"):
        with db.engine.begin() as connection:
            insert_project(connection)
            raise RuntimeError("injected")
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM projects")).scalar_one() == 0


def test_FR_PRJ_006_SC_PRJ_003_api_app_restart_retains_project(db, db_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(db_url))
    values = {"title": "Restart project", "researchQuestion": "Restart question",
              "maxPaperCount": 100, "keywords": [" LLM ", "llm"], "yearFrom": 2020}
    with TestClient(create_app()) as first:
        response = first.post("/api/projects", json=values)
        assert response.status_code == 201
        project = response.json()
    with TestClient(create_app()) as second:
        assert second.get(f"/api/projects/{project['id']}").json() == project
        invalid = second.post("/api/projects", json=dict(values, maxPaperCount=0))
        assert invalid.status_code == 422
        assert second.get("/api/projects").json() == [project]


def test_FR_PRJ_006_008_update_delete_survive_app_restart(db, db_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(db_url))
    values = {"title": "Retained", "researchQuestion": "Question", "maxPaperCount": 100}
    with TestClient(create_app()) as first:
        project = first.post("/api/projects", json=values).json()
        other = first.post("/api/projects", json=dict(values, title="Other")).json()
        path = f"/api/projects/{project['id']}"
        changed = first.put(path, json=dict(values, title="Updated")).json()
    with TestClient(create_app()) as second:
        assert second.get(path).json() == changed
        assert second.delete(path).status_code == 204
    with TestClient(create_app()) as third:
        assert third.get(path).status_code == 404
        assert third.get("/api/projects").json() == [other]


def test_FR_PRJ_007_migration_failure_is_atomic(db, monkeypatch, tmp_path):
    with db.engine.connect() as connection:
        before = connection.execute(text("SELECT count(*) FROM schema_migrations")).scalar_one()
    migration = tmp_path / "002_intentionally_invalid.sql"
    migration.write_text("CREATE TABLE partial_migration (id integer); SELECT invalid_column;")
    monkeypatch.setattr(persistence, "MIGRATIONS", tmp_path)
    with pytest.raises(ProgrammingError):
        db.migrate()
    with db.engine.connect() as connection:
        partial = connection.execute(text("SELECT to_regclass('partial_migration')")).scalar_one()
        assert partial is None
        after = connection.execute(text("SELECT count(*) FROM schema_migrations")).scalar_one()
        assert after == before
