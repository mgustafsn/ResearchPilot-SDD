"""Query persistence with coherent parent-first locking and optimistic revisions."""

from uuid import uuid4

from sqlalchemy import delete, insert, select, update

from researchpilot.query_domain import (
    QueryListOutput,
    QueryOutput,
    becomes_owned,
    enabled_texts,
    refresh_required,
)
from researchpilot.service import ProjectNotFound


class QueryError(Exception):
    def __init__(self, code):
        self.code = code
        self.status, self.message = {
            "QUERY_REVISION_CHANGED": (409, "Queries changed. Reload and try again."),
            "QUERY_DUPLICATE": (409, "That query already exists in this project."),
            "QUERY_LIMIT_REACHED": (409, "A project can contain at most 20 saved queries."),
            "NOT_FOUND": (404, "Query not found."),
        }[code]
        super().__init__(self.message)


class QueryService:
    def __init__(self, database, provider=None):
        self.database = database
        self.provider = provider

    def list(self, project_id):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id)
            return self._output(connection, parent)

    def selected_texts(self, project_id):
        with self.database.engine.begin() as connection:
            self._parent(connection, project_id)
            return enabled_texts(self._rows(connection, project_id))

    def _parent(self, connection, project_id, revision=None):
        table = self.database.projects
        parent = connection.execute(
            select(table).where(table.c.id == project_id).with_for_update()
        ).mappings().first()
        if parent is None:
            raise ProjectNotFound
        if revision is not None and parent["mutation_revision"] != revision:
            raise QueryError("QUERY_REVISION_CHANGED")
        return dict(parent)

    def _rows(self, connection, project_id):
        table = self.database.queries
        return connection.execute(select(table).where(
            table.c.project_id == project_id).order_by(table.c.slot)).mappings().all()

    def _output(self, connection, parent):
        return QueryListOutput(
            projectId=parent["id"], revision=parent["mutation_revision"],
            refreshRequired=refresh_required(parent["query_context_revision"],
                                             parent["generated_context_revision"]),
            generationAvailable=self.provider is not None,
            queries=[QueryOutput(id=row["id"], projectId=row["project_id"], text=row["text"],
                enabled=row["enabled"], origin=row["origin"], userOwned=row["user_owned"])
                for row in self._rows(connection, parent["id"])],
        )

    def _bump(self, connection, parent):
        parent["mutation_revision"] += 1
        table = self.database.projects
        connection.execute(update(table).where(table.c.id == parent["id"]).values(
            mutation_revision=parent["mutation_revision"]))

    def add(self, project_id, data):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id, data.expectedRevision)
            rows = self._rows(connection, project_id)
            if any(row["normalized_key"] == data.text.casefold() for row in rows):
                raise QueryError("QUERY_DUPLICATE")
            occupied = {row["slot"] for row in rows}
            slot = next((slot for slot in range(1, 21) if slot not in occupied), None)
            if slot is None:
                raise QueryError("QUERY_LIMIT_REACHED")
            connection.execute(insert(self.database.queries).values(
                id=uuid4(), project_id=project_id, text=data.text,
                normalized_key=data.text.casefold(), enabled=data.enabled,
                origin="manual", user_owned=True, slot=slot))
            self._bump(connection, parent)
            return self._output(connection, parent)

    def patch(self, project_id, query_id, data):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id, data.expectedRevision)
            rows = self._rows(connection, project_id)
            previous = next((row for row in rows if row["id"] == query_id), None)
            if previous is None:
                raise QueryError("NOT_FOUND")
            text_value = data.text if data.text is not None else previous["text"]
            enabled = data.enabled if data.enabled is not None else previous["enabled"]
            if any(row["id"] != query_id and row["normalized_key"] == text_value.casefold()
                   for row in rows):
                raise QueryError("QUERY_DUPLICATE")
            if text_value != previous["text"] or enabled != previous["enabled"]:
                table = self.database.queries
                connection.execute(update(table).where(table.c.id == query_id).values(
                    text=text_value, normalized_key=text_value.casefold(), enabled=enabled,
                    user_owned=becomes_owned(previous, text_value, enabled)))
                self._bump(connection, parent)
            return self._output(connection, parent)

    def delete(self, project_id, query_id, revision):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id, revision)
            table = self.database.queries
            result = connection.execute(delete(table).where(
                table.c.id == query_id, table.c.project_id == project_id))
            if result.rowcount == 0:
                raise QueryError("NOT_FOUND")
            self._bump(connection, parent)
            return self._output(connection, parent)
