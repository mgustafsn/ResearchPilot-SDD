"""User-triggered OpenAlex retrieval with bounded, atomic result replacement."""

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

from researchpilot.paper_domain import (
    CurrentPapersOutput,
    DeduplicationResult,
    NoEnabledQueries,
    PaperOutput,
    SearchAttemptOutput,
    SearchOutput,
    allocate_query_budgets,
    deduplicate_papers,
)
from researchpilot.paper_provider import PaperProviderError, PaperSearchResult
from researchpilot.service import ProjectNotFound

logger = logging.getLogger("researchpilot.retrieval")
MAX_REQUESTS_PER_ATTEMPT = 20
MAX_CONCURRENT_REQUESTS = 2
ATTEMPT_TIMEOUT_SECONDS = 120
LEASE_SECONDS = 150
PROVIDER_ERRORS = {
    "rate_limited": "PROVIDER_UNAVAILABLE",
    "timeout": "PROVIDER_TIMEOUT",
    "unavailable": "PROVIDER_UNAVAILABLE",
    "invalid_response": "PROVIDER_INVALID_RESPONSE",
}


class RetrievalError(Exception):
    def __init__(self, code):
        self.code = code
        self.status, self.message = {
            "SEARCH_ACTIVE": (409, "A search is already active for this project."),
            "SEARCH_STALE": (409, "Search expired or was replaced; previous results were kept."),
            "NO_ENABLED_QUERIES": (422, "Enable at least one saved query before searching."),
            "PROVIDER_INVALID_RESPONSE": (502, "OpenAlex returned an invalid response."),
            "PROVIDER_UNAVAILABLE": (503, "OpenAlex is unavailable; previous results were kept."),
            "PROVIDER_TIMEOUT": (504, "OpenAlex timed out; previous results were kept."),
            "STORAGE_UNAVAILABLE": (503, "Storage is unavailable; previous results were kept."),
        }[code]
        super().__init__(self.message)


class ProviderBatchFailure(Exception):
    def __init__(self, cause, completed_results):
        self.cause = cause
        self.completed_results = completed_results
        super().__init__("Provider batch failed")


def _paper_output(paper_id, row):
    return PaperOutput(
        id=paper_id,
        provider=row["provider"],
        providerId=row["provider_id"],
        doi=row["doi"],
        title=row["title"],
        abstract=row["abstract"],
        authors=row["authors"],
        publicationYear=row["publication_year"],
        publicationDate=row["publication_date"],
        venue=row["venue"],
        citationCount=row["citation_count"],
        sourceUrl=row["source_url"],
        publicationUrl=row["publication_url"],
        fullTextUrl=row["full_text_url"],
        isOpenAccess=row["is_open_access"],
    )


def _attempt_output(row):
    return SearchAttemptOutput(
        searchRunId=row["id"],
        status=row["status"],
        provider="openalex",
        startedAt=row["started_at"],
        finishedAt=row["finished_at"],
        rawFetchedCount=row["raw_fetched_count"],
        skippedCount=row["skipped_count"],
        duplicateCount=row["duplicate_count"],
        queriesUsed=[
            {"text": item["text"], "allocatedLimit": item["allocatedLimit"]}
            for item in row["queries_used"]
        ],
        queriesUnused=[
            {"text": item["text"], "allocatedLimit": item["allocatedLimit"]}
            for item in row["queries_unused"]
        ],
        errorCode=row["error_code"],
    )


class RetrievalService:
    def __init__(self, database, provider=None):
        self.database = database
        self.provider = provider

    async def search(self, project_id):
        snapshot = await asyncio.to_thread(self._begin, project_id)
        started = time.monotonic()
        raw_count = skipped_count = duplicate_count = request_count = 0
        provider_cost_usd = None
        try:
            results = await self._retrieve(snapshot)
            deduplicated = deduplicate_papers(
                [paper for result in results for paper in result.papers]
            )
            raw_count = sum(result.raw_count for result in results)
            skipped_count = sum(result.skipped_count for result in results)
            request_count = sum(result.request_count for result in results)
            duplicate_count = deduplicated.duplicate_count
            costs = [
                result.provider_cost_usd
                for result in results
                if result.provider_cost_usd is not None
            ]
            provider_cost_usd = sum(costs) if costs else None
            if raw_count > snapshot["paper_limit"] or request_count > MAX_REQUESTS_PER_ATTEMPT:
                raise RetrievalError("PROVIDER_INVALID_RESPONSE")
            try:
                output = await asyncio.to_thread(
                    self._commit_success,
                    snapshot,
                    deduplicated,
                    raw_count,
                    skipped_count,
                    request_count,
                )
            except SQLAlchemyError:
                try:
                    await asyncio.to_thread(
                        self._finish_failure,
                        snapshot,
                        "STORAGE_UNAVAILABLE",
                        raw_count,
                        skipped_count,
                        duplicate_count,
                    )
                except SQLAlchemyError:
                    pass
                raise RetrievalError("STORAGE_UNAVAILABLE") from None
            self._log(
                snapshot,
                "succeeded",
                started,
                raw_count,
                skipped_count,
                deduplicated.duplicate_count,
                request_count,
                provider_cost_usd,
            )
            return output
        except asyncio.CancelledError:
            await asyncio.to_thread(
                self._finish_failure,
                snapshot,
                "SEARCH_CANCELLED",
                raw_count,
                skipped_count,
                duplicate_count,
            )
            raise
        except ProviderBatchFailure as failure:
            results = failure.completed_results
            raw_count = sum(result.raw_count for result in results)
            skipped_count = sum(result.skipped_count for result in results)
            request_count = sum(result.request_count for result in results)
            cause = failure.cause
            if isinstance(cause, PaperProviderError):
                raw_count += cause.raw_count
                skipped_count += cause.skipped_count
                request_count += cause.request_count
                costs = [
                    result.provider_cost_usd
                    for result in results
                    if result.provider_cost_usd is not None
                ]
                if cause.provider_cost_usd is not None:
                    costs.append(cause.provider_cost_usd)
                provider_cost_usd = sum(costs) if costs else None
                code = PROVIDER_ERRORS.get(cause.category, "PROVIDER_UNAVAILABLE")
            elif isinstance(cause, (ValidationError, ValueError, TypeError)):
                code = "PROVIDER_INVALID_RESPONSE"
            elif isinstance(cause, TimeoutError):
                code = "PROVIDER_TIMEOUT"
            else:
                code = "PROVIDER_UNAVAILABLE"
            if results:
                duplicate_count = deduplicate_papers(
                    [paper for result in results for paper in result.papers]
                ).duplicate_count
            if provider_cost_usd is None:
                costs = [
                    result.provider_cost_usd
                    for result in results
                    if result.provider_cost_usd is not None
                ]
                provider_cost_usd = sum(costs) if costs else None
            await asyncio.to_thread(
                self._finish_failure, snapshot, code, raw_count, skipped_count, duplicate_count
            )
            self._log(
                snapshot,
                code,
                started,
                raw_count,
                skipped_count,
                duplicate_count,
                request_count,
                provider_cost_usd,
            )
            raise RetrievalError(code) from None
        except TimeoutError:
            await asyncio.to_thread(
                self._finish_failure,
                snapshot,
                "PROVIDER_TIMEOUT",
                raw_count,
                skipped_count,
                duplicate_count,
            )
            self._log(
                snapshot,
                "PROVIDER_TIMEOUT",
                started,
                raw_count,
                skipped_count,
                duplicate_count,
                request_count,
                provider_cost_usd,
            )
            raise RetrievalError("PROVIDER_TIMEOUT") from None
        except RetrievalError as error:
            await asyncio.to_thread(
                self._finish_failure,
                snapshot,
                error.code,
                raw_count,
                skipped_count,
                duplicate_count,
            )
            self._log(
                snapshot,
                error.code,
                started,
                raw_count,
                skipped_count,
                duplicate_count,
                request_count,
                provider_cost_usd,
            )
            raise
        except PaperProviderError as error:
            code = PROVIDER_ERRORS.get(error.category, "PROVIDER_UNAVAILABLE")
            raw_count += error.raw_count
            skipped_count += error.skipped_count
            request_count += error.request_count
            provider_cost_usd = error.provider_cost_usd
            await asyncio.to_thread(
                self._finish_failure, snapshot, code, raw_count, skipped_count, duplicate_count
            )
            self._log(
                snapshot,
                code,
                started,
                raw_count,
                skipped_count,
                duplicate_count,
                request_count,
                provider_cost_usd,
            )
            raise RetrievalError(code) from None
        except ProjectNotFound:
            await asyncio.to_thread(self._finish_failure, snapshot, "PROJECT_DELETED")
            raise
        except Exception:
            # Provider implementations are untrusted at the service boundary.
            await asyncio.to_thread(self._finish_failure, snapshot, "PROVIDER_UNAVAILABLE")
            self._log(snapshot, "PROVIDER_UNAVAILABLE", started, 0, 0, 0, 0)
            raise RetrievalError("PROVIDER_UNAVAILABLE") from None

    async def _retrieve(self, snapshot):
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def one(index, allocation):
            async with semaphore:
                result = await self.provider.search(
                    allocation.text, snapshot["year_from"], snapshot["year_to"], allocation.limit
                )
            try:
                result = PaperSearchResult.model_validate(result)
            except (ValidationError, ValueError, TypeError):
                raise PaperProviderError("invalid_response") from None
            if result.raw_count > allocation.limit:
                raise PaperProviderError("invalid_response") from None
            return index, result

        tasks = [
            asyncio.create_task(one(index, item))
            for index, item in enumerate(snapshot["used_allocations"])
        ]
        completed = {}
        try:
            async with asyncio.timeout(ATTEMPT_TIMEOUT_SECONDS):
                for finished in asyncio.as_completed(tasks):
                    index, result = await finished
                    completed[index] = result
        except BaseException as error:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if isinstance(error, asyncio.CancelledError):
                raise
            raise ProviderBatchFailure(
                error, [completed[index] for index in sorted(completed)]
            ) from None
        return [completed[index] for index in sorted(completed)]

    def _begin(self, project_id):
        projects = self.database.projects
        runs = self.database.search_runs
        attempt = None
        with self.database.engine.begin() as connection:
            project = (
                connection.execute(
                    select(projects).where(projects.c.id == project_id).with_for_update()
                )
                .mappings()
                .first()
            )
            if project is None:
                raise ProjectNotFound
            now = datetime.now(UTC)
            pending = (
                connection.execute(
                    select(runs)
                    .where(runs.c.project_id == project_id, runs.c.status == "pending")
                    .order_by(runs.c.started_at.desc())
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if pending is not None:
                if pending["lease_expires_at"] > now:
                    raise RetrievalError("SEARCH_ACTIVE")
                connection.execute(
                    update(runs)
                    .where(runs.c.id == pending["id"])
                    .values(status="failed", finished_at=now, error_code="SEARCH_EXPIRED")
                )
            rows = (
                connection.execute(
                    select(self.database.queries)
                    .where(self.database.queries.c.project_id == project_id)
                    .order_by(self.database.queries.c.slot)
                )
                .mappings()
                .all()
            )
            try:
                used, unused = allocate_query_budgets(rows, project["max_paper_count"])
            except NoEnabledQueries:
                raise RetrievalError("NO_ENABLED_QUERIES") from None
            used_json = [self._query_snapshot(item) for item in used]
            unused_json = [self._query_snapshot(item) for item in unused]
            if self.provider is not None:
                run_id, token = uuid4(), uuid4()
                started_at = now
                run_values = {
                    "project_id": project_id,
                    "run_id": run_id,
                    "token": token,
                    "started_at": started_at,
                    "year_from": project["year_from"],
                    "year_to": project["year_to"],
                    "paper_limit": project["max_paper_count"],
                    "used_allocations": used,
                    "queries_used": used_json,
                    "queries_unused": unused_json,
                }
                run_snapshot = {
                    "researchQuestion": project["research_question"],
                    "keywords": project["keywords"],
                    "enabledQueries": used_json + unused_json,
                    "yearFrom": project["year_from"],
                    "yearTo": project["year_to"],
                    "paperLimit": project["max_paper_count"],
                    "providersQueried": ["openalex"],
                    "startedAt": started_at.isoformat(),
                }
                connection.execute(
                    insert(runs).values(
                        id=run_id,
                        project_id=project_id,
                        input_snapshot=run_snapshot,
                        status="pending",
                        ownership_token=token,
                        lease_expires_at=now + timedelta(seconds=LEASE_SECONDS),
                        started_at=started_at,
                        raw_fetched_count=0,
                        skipped_count=0,
                        duplicate_count=0,
                        queries_used=used_json,
                        queries_unused=unused_json,
                        error_code=None,
                    )
                )
                attempt = run_values
        if attempt is None:
            raise RetrievalError("PROVIDER_UNAVAILABLE")
        return attempt

    @staticmethod
    def _query_snapshot(allocation):
        return {
            "queryId": allocation.id,
            "text": allocation.text,
            "slot": allocation.slot,
            "allocatedLimit": allocation.limit,
        }

    def _commit_success(
        self, snapshot, deduplicated: DeduplicationResult, raw_count, skipped_count, request_count
    ):
        projects = self.database.projects
        runs = self.database.search_runs
        papers_table = self.database.papers
        associations = self.database.project_papers
        now = datetime.now(UTC)
        inserted_papers = []
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(projects.c.id)
                .where(projects.c.id == snapshot["project_id"])
                .with_for_update()
            ).first()
            if project is None:
                raise ProjectNotFound
            run = (
                connection.execute(
                    select(runs).where(runs.c.id == snapshot["run_id"]).with_for_update()
                )
                .mappings()
                .first()
            )
            if (
                run is None
                or run["status"] != "pending"
                or run["ownership_token"] != snapshot["token"]
                or run["lease_expires_at"] <= now
            ):
                raise RetrievalError("SEARCH_STALE")

            paper_ids = []
            for paper in deduplicated.papers:
                values = {
                    "id": uuid4(),
                    "provider": paper.provider,
                    "provider_id": paper.provider_id,
                    "doi": paper.doi,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "publication_year": paper.publication_year,
                    "publication_date": paper.publication_date,
                    "venue": paper.venue,
                    "citation_count": paper.citation_count,
                    "source_url": paper.source_url,
                    "publication_url": paper.publication_url,
                    "full_text_url": paper.full_text_url,
                    "is_open_access": paper.is_open_access,
                    "updated_at": now,
                }
                statement = pg_insert(papers_table).values(**values)
                update_values = {
                    name: getattr(statement.excluded, name)
                    for name in values
                    if name not in {"id", "provider", "provider_id"}
                }
                statement = statement.on_conflict_do_update(
                    index_elements=[papers_table.c.provider, papers_table.c.provider_id],
                    set_=update_values,
                ).returning(papers_table.c.id)
                paper_id = connection.execute(statement).scalar_one()
                paper_ids.append(paper_id)
                inserted_papers.append(_paper_output(paper_id, values))

            # A slow database phase may outlive the lease even after HTTP completed.
            latest_run = (
                connection.execute(
                    select(runs).where(runs.c.id == snapshot["run_id"]).with_for_update()
                )
                .mappings()
                .first()
            )
            if (
                latest_run is None
                or latest_run["status"] != "pending"
                or latest_run["ownership_token"] != snapshot["token"]
                or latest_run["lease_expires_at"] <= datetime.now(UTC)
            ):
                raise RetrievalError("SEARCH_STALE")

            connection.execute(
                delete(associations).where(associations.c.project_id == snapshot["project_id"])
            )
            if paper_ids:
                connection.execute(
                    insert(associations),
                    [
                        {
                            "project_id": snapshot["project_id"],
                            "paper_id": paper_id,
                            "search_run_id": snapshot["run_id"],
                            "ordinal": index,
                        }
                        for index, paper_id in enumerate(paper_ids)
                    ],
                )
            finished = datetime.now(UTC)
            connection.execute(
                update(runs)
                .where(
                    runs.c.id == snapshot["run_id"],
                    runs.c.status == "pending",
                    runs.c.ownership_token == snapshot["token"],
                )
                .values(
                    status="succeeded",
                    finished_at=finished,
                    raw_fetched_count=raw_count,
                    skipped_count=skipped_count,
                    duplicate_count=deduplicated.duplicate_count,
                    error_code=None,
                )
            )
            # Preserve provider rows still associated with any project's current results.
            connection.execute(
                delete(papers_table).where(
                    ~select(associations.c.paper_id)
                    .where(associations.c.paper_id == papers_table.c.id)
                    .exists()
                )
            )
            run_row = dict(run)
            run_row.update(
                status="succeeded",
                finished_at=finished,
                raw_fetched_count=raw_count,
                skipped_count=skipped_count,
                duplicate_count=deduplicated.duplicate_count,
                error_code=None,
            )
        attempt = _attempt_output(run_row)
        return SearchOutput(
            **dict(attempt), projectId=snapshot["project_id"], papers=inserted_papers
        )

    def _finish_failure(self, snapshot, code, raw_count=0, skipped_count=0, duplicate_count=0):
        projects = self.database.projects
        runs = self.database.search_runs
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(projects.c.id)
                .where(projects.c.id == snapshot["project_id"])
                .with_for_update()
            ).first()
            if project is None:
                return
            connection.execute(
                update(runs)
                .where(
                    runs.c.id == snapshot["run_id"],
                    runs.c.project_id == snapshot["project_id"],
                    runs.c.status == "pending",
                    runs.c.ownership_token == snapshot["token"],
                )
                .values(
                    status="failed",
                    finished_at=now,
                    error_code=code,
                    raw_fetched_count=raw_count,
                    skipped_count=skipped_count,
                    duplicate_count=duplicate_count,
                )
            )

    def current(self, project_id):
        projects = self.database.projects
        runs = self.database.search_runs
        associations = self.database.project_papers
        papers = self.database.papers
        now = datetime.now(UTC)
        with self.database.engine.begin() as connection:
            project = connection.execute(
                select(projects.c.id).where(projects.c.id == project_id).with_for_update()
            ).first()
            if project is None:
                raise ProjectNotFound
            pending = (
                connection.execute(
                    select(runs)
                    .where(runs.c.project_id == project_id, runs.c.status == "pending")
                    .order_by(runs.c.started_at.desc())
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if pending is not None and pending["lease_expires_at"] <= now:
                connection.execute(
                    update(runs)
                    .where(runs.c.id == pending["id"])
                    .values(status="failed", finished_at=now, error_code="SEARCH_EXPIRED")
                )
            latest = (
                connection.execute(
                    select(runs)
                    .where(runs.c.project_id == project_id)
                    .order_by(runs.c.started_at.desc(), runs.c.id.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
            rows = (
                connection.execute(
                    select(papers, associations.c.ordinal)
                    .select_from(associations.join(papers, associations.c.paper_id == papers.c.id))
                    .where(associations.c.project_id == project_id)
                    .order_by(associations.c.ordinal)
                )
                .mappings()
                .all()
            )
            outputs = [_paper_output(row["id"], row) for row in rows]
        attempt = _attempt_output(latest) if latest else None
        return CurrentPapersOutput(projectId=project_id, latestAttempt=attempt, papers=outputs)

    @staticmethod
    def _log(
        snapshot,
        status,
        started,
        raw_count,
        skipped_count,
        duplicate_count,
        request_count,
        provider_cost_usd=None,
    ):
        logger.info(
            "Retrieval run=%s project=%s provider=openalex status=%s duration=%.3fs "
            "requests=%s raw=%s skipped=%s duplicates=%s cost_usd=%s",
            snapshot["run_id"],
            snapshot["project_id"],
            status,
            time.monotonic() - started,
            request_count,
            raw_count,
            skipped_count,
            duplicate_count,
            provider_cost_usd,
        )
