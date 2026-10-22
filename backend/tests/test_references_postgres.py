"""FR-REF-002/003/006 saved-reference migration and persistence constraints."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from researchpilot.persistence import Database
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from test_references_api import client_for, project_with_result
from test_retrieval_api import FakePaperProvider, paper
from test_retrieval_postgres import insert_paper, insert_project


def snapshot(provider_id="W1", title="Saved provider title"):
    return json.dumps(
        {
            "provider": "openalex",
            "provider_id": provider_id,
            "doi": None,
            "title": title,
            "abstract": None,
            "authors": ["Provider Author"],
            "publication_year": 2022,
            "publication_date": None,
            "venue": "Journal",
            "citation_count": 4,
            "source_url": f"https://openalex.org/{provider_id}",
            "publication_url": None,
            "full_text_url": None,
            "is_open_access": None,
        }
    )


def insert_reference(connection, project_id, provider_id="W1", paper_snapshot=None):
    connection.execute(
        text("""
        INSERT INTO saved_references
            (id, project_id, provider, provider_id, paper_snapshot, title_sort_key, saved_at)
        VALUES (:id, :project_id, 'openalex', :provider_id, CAST(:snapshot AS jsonb),
                lower(:title), now())
    """),
        {
            "id": uuid4(),
            "project_id": project_id,
            "provider_id": provider_id,
            "snapshot": paper_snapshot or snapshot(provider_id),
            "title": "Saved provider title",
        },
    )


def test_FR_REF_002_003_006_migration_005_is_versioned_repeatable_and_reflected(db_url):
    database = Database(db_url)
    try:
        database.migrate()
        database.migrate()
        with database.engine.connect() as connection:
            versions = set(
                connection.execute(text("SELECT version FROM schema_migrations")).scalars()
            )
            table = connection.execute(text("SELECT to_regclass('saved_references')")).scalar_one()
        assert versions == {
            "001_projects.sql",
            "002_search_queries.sql",
            "003_paper_retrieval.sql",
            "004_local_ranking.sql",
            "005_saved_references.sql",
        }
        assert table == "saved_references"
        assert database.saved_references.name == "saved_references"
    finally:
        database.close()


def test_FR_REF_003_unique_source_identity_and_FR_REF_006_project_cascade(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        insert_reference(connection, project_id)
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            insert_reference(connection, project_id)
    with db.engine.begin() as connection:
        second_project = insert_project(connection)
        insert_reference(connection, second_project)
        connection.execute(text("DELETE FROM projects WHERE id=:id"), {"id": project_id})
        assert (
            connection.execute(
                text("SELECT count(*) FROM saved_references WHERE project_id=:id"),
                {"id": project_id},
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text("SELECT count(*) FROM saved_references WHERE project_id=:id"),
                {"id": second_project},
            ).scalar_one()
            == 1
        )


@pytest.mark.parametrize(
    "provider,provider_id,snapshot_value",
    [
        ("openalex", "W1", "[]"),
        (
            "openalex",
            "W1",
            '{"provider":"openalex","provider_id":"W2","title":"X","source_url":"https://openalex.org/W2"}',
        ),
        ("other", "W1", None),
    ],
)
def test_FR_REF_002_snapshot_object_and_identity_constraints(
    db, provider, provider_id, snapshot_value
):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO saved_references
                    (id, project_id, provider, provider_id, paper_snapshot, title_sort_key)
                VALUES (:id, :project, :provider, :provider_id,
                        CAST(:snapshot AS jsonb), 'x')
            """),
                {
                    "id": uuid4(),
                    "project": project_id,
                    "provider": provider,
                    "provider_id": provider_id,
                    "snapshot": snapshot_value or snapshot(provider_id),
                },
            )


def test_FR_REF_002_saved_snapshot_is_independent_of_paper_refresh_and_result_links(db):
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        paper_id = insert_paper(connection, provider_id="W1", title="Current provider title")
        insert_reference(
            connection, project_id, paper_snapshot=snapshot("W1", "Original saved title")
        )
        connection.execute(
            text("UPDATE papers SET title='Refreshed title' WHERE id=:id"), {"id": paper_id}
        )
        connection.execute(text("DELETE FROM papers WHERE id=:id"), {"id": paper_id})
        row = connection.execute(
            text("""
            SELECT paper_snapshot->>'title' FROM saved_references WHERE project_id=:project
        """),
            {"project": project_id},
        ).scalar_one()
    assert row == "Original saved title"


def test_FR_REF_002_005_snapshot_survives_migration_reopen(db):
    migration = Path("migrations/005_saved_references.sql")
    assert migration.exists()
    with db.engine.begin() as connection:
        project_id = insert_project(connection)
        insert_reference(connection, project_id)
    reopened = Database(str(db.engine.url.render_as_string(hide_password=False)))
    try:
        reopened.migrate()
        with reopened.engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT paper_snapshot->>'title' FROM saved_references")
                ).scalar_one()
                == "Saved provider title"
            )
    finally:
        reopened.close()


def test_FR_REF_003_concurrent_duplicate_saves_return_one_reference(db):
    provider = FakePaperProvider({"Search phrase": [paper("W1", "Provider title")]})
    with client_for(db, provider) as client:
        path, result = project_with_result(client, provider)
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(
                pool.map(
                    lambda _: client.post(path + "/references", json={"paperId": result["id"]}),
                    range(2),
                )
            )
        assert sorted(response.status_code for response in responses) == [200, 201]
        assert responses[0].json()["id"] == responses[1].json()["id"]
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM saved_references")).scalar_one() == 1
