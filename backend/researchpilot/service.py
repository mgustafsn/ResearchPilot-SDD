"""Project business operations, independent of scholarly/AI providers."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, insert, select, update

from researchpilot.domain import ProjectOutput


class ProjectNotFound(Exception):
    pass


class SearchInProgress(Exception):
    pass


def ensure_search_inactive(connection, database, project_id):
    """Caller holds the project row lock; expire stale owners or reject a writer."""
    table = database.search_runs
    pending = connection.execute(select(table).where(
        table.c.project_id == project_id, table.c.status == "pending"
    ).order_by(table.c.started_at.desc()).with_for_update()).mappings().first()
    if pending is None:
        return
    now = datetime.now(UTC)
    if pending["lease_expires_at"] > now:
        raise SearchInProgress
    connection.execute(update(table).where(table.c.id == pending["id"]).values(
        status="failed", finished_at=now, error_code="SEARCH_EXPIRED"))


def project_output(row):
    return ProjectOutput(
        id=row["id"], title=row["title"], researchQuestion=row["research_question"],
        keywords=row["keywords"], yearFrom=row["year_from"], yearTo=row["year_to"],
        maxPaperCount=row["max_paper_count"], createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


def input_values(data):
    return dict(title=data.title, research_question=data.researchQuestion, keywords=data.keywords,
                year_from=data.yearFrom, year_to=data.yearTo, max_paper_count=data.maxPaperCount)


class ProjectService:
    def __init__(self, database):
        self.database = database

    def create(self, data):
        table = self.database.projects
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            row = connection.execute(insert(table).values(
                **input_values(data), id=uuid4(), created_at=now, updated_at=now,
            ).returning(table)).mappings().one()
            result = project_output(row)
        return result  # Returned only after the transaction commits successfully.

    def list(self):
        table = self.database.projects
        with self.database.engine.connect() as connection:
            rows = connection.execute(select(table).order_by(
                table.c.updated_at.desc(), table.c.id.asc(),
            )).mappings().all()
        return [project_output(row) for row in rows]

    def read(self, project_id):
        table = self.database.projects
        with self.database.engine.connect() as connection:
            row = connection.execute(
                select(table).where(table.c.id == project_id)
            ).mappings().first()
        if row is None:
            raise ProjectNotFound
        return project_output(row)

    def update(self, project_id, data):
        table = self.database.projects
        with self.database.engine.begin() as connection:
            previous = connection.execute(
                select(table).where(table.c.id == project_id).with_for_update()
            ).mappings().first()
            if previous is None:
                raise ProjectNotFound
            ensure_search_inactive(connection, self.database, project_id)
            values = input_values(data)
            changed = any(previous[name] != value for name, value in values.items())
            context_changed = any(previous[name] != values[name]
                                  for name in ("research_question", "keywords"))
            row = connection.execute(update(table).where(table.c.id == project_id).values(
                **values, updated_at=datetime.now(UTC),
                mutation_revision=previous["mutation_revision"] + int(changed),
                query_context_revision=previous["query_context_revision"] + int(context_changed),
            ).returning(table)).mappings().first()
            if row is None:
                raise ProjectNotFound
            result = project_output(row)
        return result

    def delete(self, project_id):
        table = self.database.projects
        with self.database.engine.begin() as connection:
            parent = connection.execute(
                select(table.c.id).where(table.c.id == project_id).with_for_update()
            ).first()
            if parent is None:
                raise ProjectNotFound
            ensure_search_inactive(connection, self.database, project_id)
            result = connection.execute(delete(table).where(table.c.id == project_id))
            if result.rowcount == 0:
                raise ProjectNotFound
