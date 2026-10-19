"""Query persistence with coherent parent-first locking and optimistic revisions."""

import asyncio
import logging
import time
from uuid import uuid4

from sqlalchemy import delete, insert, select, update

from researchpilot.query_domain import (
    GenerationOutput,
    GenerationSummary,
    QueryListOutput,
    QueryOutput,
    SuggestionBatch,
    becomes_owned,
    enabled_texts,
    merge_plan,
    refresh_required,
)
from researchpilot.query_provider import SuggestionContext, SuggestionProviderError
from researchpilot.service import ProjectNotFound, ensure_search_inactive

logger = logging.getLogger("researchpilot.suggestions")
PROVIDER_ERRORS = {"timeout": "SUGGESTIONS_TIMEOUT", "invalid_output": "SUGGESTIONS_INVALID_OUTPUT"}


class QueryError(Exception):
    def __init__(self, code):
        self.code = code
        self.status, self.message = {
            "QUERY_REVISION_CHANGED": (409, "Queries changed. Reload and try again."),
            "QUERY_DUPLICATE": (409, "That query already exists in this project."),
            "QUERY_LIMIT_REACHED": (409, "A project can contain at most 20 saved queries."),
            "NOT_FOUND": (404, "Query not found."),
            "GENERATION_STALE": (409, "The project or its queries changed while suggestions "
                                 "were generated. Reload and try again."),
            "SUGGESTIONS_UNAVAILABLE": (503, "Query suggestions are unavailable right now. "
                                        "You can still manage queries manually."),
            "SUGGESTIONS_TIMEOUT": (504, "Query suggestions took too long. Your saved "
                                    "queries are unchanged."),
            "SUGGESTIONS_INVALID_OUTPUT": (502, "Query suggestions could not be used. Your "
                                           "saved queries are unchanged."),
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

    def _parent(self, connection, project_id, revision=None, mutation=False):
        table = self.database.projects
        parent = connection.execute(
            select(table).where(table.c.id == project_id).with_for_update()
        ).mappings().first()
        if parent is None:
            raise ProjectNotFound
        if revision is not None and parent["mutation_revision"] != revision:
            raise QueryError("QUERY_REVISION_CHANGED")
        if mutation:
            ensure_search_inactive(connection, self.database, project_id)
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
            parent = self._parent(connection, project_id, data.expectedRevision, mutation=True)
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
            parent = self._parent(connection, project_id, data.expectedRevision, mutation=True)
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
            parent = self._parent(connection, project_id, revision, mutation=True)
            table = self.database.queries
            result = connection.execute(delete(table).where(
                table.c.id == query_id, table.c.project_id == project_id))
            if result.rowcount == 0:
                raise QueryError("NOT_FOUND")
            self._bump(connection, parent)
            return self._output(connection, parent)

    async def generate(self, project_id, data):
        """One explicit attempt: short snapshot, unlocked provider await, re-lock and merge."""
        context, revision = await asyncio.to_thread(
            self._snapshot, project_id, data.expectedRevision)
        started = time.monotonic()
        result = output = None
        status = "failed"  # Cancellation or storage failure.
        try:
            try:
                result = await self.provider.suggest(context)
            except SuggestionProviderError as error:
                raise QueryError(PROVIDER_ERRORS.get(error.category, "SUGGESTIONS_UNAVAILABLE")
                                 ) from None
            except Exception:
                raise QueryError("SUGGESTIONS_UNAVAILABLE") from None
            try:
                # Re-validate the complete batch; never trust a provider-built object.
                batch = SuggestionBatch.model_validate({"queries": list(result.batch.queries)})
            except Exception:
                raise QueryError("SUGGESTIONS_INVALID_OUTPUT") from None
            output = await asyncio.to_thread(self._merge, project_id, revision, batch)
            status = "success"
        except QueryError as error:
            status = error.code
            raise
        except ProjectNotFound:
            status = "NOT_FOUND"
            raise
        finally:
            self._log(project_id, status, started, result, output)
        return output

    def _log(self, project_id, status, started, result, output):
        metadata = getattr(result, "metadata", None)
        summary = getattr(output, "generationSummary", None)
        logger.info(
            "Query generation project=%s status=%s duration=%.3fs model=%s prompt=%s "
            "input_tokens=%s output_tokens=%s total_tokens=%s added=%s replaced=%s "
            "duplicates=%s capacity=%s", project_id, status, time.monotonic() - started,
            getattr(metadata, "model", None), getattr(metadata, "promptVersion", None),
            getattr(metadata, "inputTokens", None), getattr(metadata, "outputTokens", None),
            getattr(metadata, "totalTokens", None), getattr(summary, "addedCount", None),
            getattr(summary, "replacedCount", None),
            getattr(summary, "duplicateSkippedCount", None),
            getattr(summary, "capacitySkippedCount", None))

    def _snapshot(self, project_id, revision):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id, revision)
        if self.provider is None:
            raise QueryError("SUGGESTIONS_UNAVAILABLE")
        context = SuggestionContext(question=parent["research_question"],
                                    keywords=tuple(parent["keywords"]))
        return context, parent["mutation_revision"]

    def _merge(self, project_id, revision, batch):
        with self.database.engine.begin() as connection:
            parent = self._parent(connection, project_id)
            if parent["mutation_revision"] != revision:
                raise QueryError("GENERATION_STALE")
            plan = merge_plan(self._rows(connection, project_id), batch)
            table = self.database.queries
            connection.execute(delete(table).where(
                table.c.project_id == project_id, table.c.user_owned.is_(False)))
            if plan["additions"]:
                connection.execute(insert(table), [dict(
                    id=uuid4(), project_id=project_id, text=item["text"],
                    normalized_key=item["text"].casefold(), enabled=True, origin="generated",
                    user_owned=False, slot=item["slot"]) for item in plan["additions"]])
            parent["generated_context_revision"] = parent["query_context_revision"]
            projects = self.database.projects
            connection.execute(update(projects).where(projects.c.id == project_id).values(
                generated_context_revision=parent["generated_context_revision"]))
            self._bump(connection, parent)
            output = self._output(connection, parent)
        summary = GenerationSummary(
            validatedCount=len(batch.queries), addedCount=len(plan["additions"]),
            replacedCount=plan["replacedCount"],
            duplicateSkippedCount=plan["duplicateSkippedCount"],
            capacitySkippedCount=plan["capacitySkippedCount"])
        return GenerationOutput(**dict(output), generationSummary=summary)
