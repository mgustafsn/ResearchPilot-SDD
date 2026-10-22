"""Transactional, project-scoped saved-reference operations."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from researchpilot.paper_domain import Paper
from researchpilot.references_domain import (
    ReferenceError,
    ReferenceListOutput,
    paper_snapshot,
    reference_output,
    sort_references,
)
from researchpilot.service import ensure_search_inactive


class ReferenceService:
    def __init__(self, database):
        self.database = database

    def list(self, project_id) -> ReferenceListOutput:
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(self.database.projects.c.id)
                .where(self.database.projects.c.id == project_id)
                .with_for_update()
            ).first()
            if project is None:
                raise ReferenceError("PROJECT_NOT_FOUND")
            rows = (
                connection.execute(
                    select(self.database.saved_references).where(
                        self.database.saved_references.c.project_id == project_id
                    )
                )
                .mappings()
                .all()
            )
        try:
            references = sort_references([reference_output(row) for row in rows])
        except ValidationError:
            raise ReferenceError("STORAGE_ERROR") from None
        return ReferenceListOutput(projectId=project_id, references=references)

    def save(self, project_id, paper_id):
        projects = self.database.projects
        table = self.database.saved_references
        associations = self.database.project_papers
        papers = self.database.papers
        created = False
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(projects.c.id).where(projects.c.id == project_id).with_for_update()
            ).first()
            if project is None:
                raise ReferenceError("PROJECT_NOT_FOUND")
            ensure_search_inactive(connection, self.database, project_id)

            paper_row = (
                connection.execute(
                    select(papers)
                    .select_from(associations.join(papers, associations.c.paper_id == papers.c.id))
                    .where(associations.c.project_id == project_id, papers.c.id == paper_id)
                )
                .mappings()
                .first()
            )
            if paper_row is None:
                raise ReferenceError("PAPER_NOT_FOUND")

            try:
                provider_paper = Paper.model_validate(
                    {name: paper_row[name] for name in Paper.model_fields}
                )
            except ValidationError:
                raise ReferenceError("STORAGE_ERROR") from None

            values = {
                "id": uuid4(),
                "project_id": project_id,
                "provider": provider_paper.provider,
                "provider_id": provider_paper.provider_id,
                "paper_snapshot": paper_snapshot(provider_paper),
                "title_sort_key": provider_paper.title.casefold(),
                "saved_at": datetime.now(UTC),
            }
            inserted = (
                connection.execute(
                    pg_insert(table)
                    .values(**values)
                    .on_conflict_do_nothing(
                        index_elements=[table.c.project_id, table.c.provider, table.c.provider_id]
                    )
                    .returning(table)
                )
                .mappings()
                .first()
            )
            created = inserted is not None
            row = (
                inserted
                or connection.execute(
                    select(table).where(
                        table.c.project_id == project_id,
                        table.c.provider == provider_paper.provider,
                        table.c.provider_id == provider_paper.provider_id,
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise ReferenceError("STORAGE_ERROR")

        try:
            return reference_output(row), created
        except ValidationError:
            raise ReferenceError("STORAGE_ERROR") from None

    def remove(self, project_id, reference_id) -> None:
        table = self.database.saved_references
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(self.database.projects.c.id)
                .where(self.database.projects.c.id == project_id)
                .with_for_update()
            ).first()
            if project is None:
                raise ReferenceError("PROJECT_NOT_FOUND")
            result = connection.execute(
                delete(table).where(
                    table.c.project_id == project_id,
                    table.c.id == reference_id,
                )
            )
            if result.rowcount == 0:
                raise ReferenceError("REFERENCE_NOT_FOUND")
