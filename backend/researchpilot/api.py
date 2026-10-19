"""Same-origin local API. Configuration and raw database errors never reach the UI."""

import logging
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from researchpilot.domain import ProjectInput, ProjectOutput
from researchpilot.integrations import openai_queries
from researchpilot.integrations.openalex_papers import OpenAlexPaperProvider
from researchpilot.paper_domain import CurrentPapersOutput, SearchOutput
from researchpilot.persistence import Database
from researchpilot.query_domain import (
    GenerateInput,
    GenerationOutput,
    QueryAddInput,
    QueryListOutput,
    QueryPatchInput,
)
from researchpilot.query_service import QueryError, QueryService
from researchpilot.retrieval_service import RetrievalError, RetrievalService
from researchpilot.service import ProjectNotFound, ProjectService, SearchInProgress

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
logger = logging.getLogger("researchpilot")
FROM_ENVIRONMENT = object()  # Production composition; tests inject a fake or None.
OPENALEX_PROVIDER = object()  # Production composition; tests inject a fake or None.


def error_response(status, code, message, fields=None):
    return JSONResponse({"error": {"code": code, "message": message,
                                   "fields": fields or []}}, status_code=status)


def create_app(database=None, suggestion_provider=FROM_ENVIRONMENT,
               paper_provider=OPENALEX_PROVIDER):
    @asynccontextmanager
    async def lifespan(app):
        owned = database is None
        storage = provider = retrieval_provider = None
        try:
            try:
                storage = database or Database(os.environ["DATABASE_URL"])
                storage.migrate()
            except Exception:
                raise RuntimeError("Database startup failed; check local configuration") from None
            app.state.database = storage
            app.state.projects = ProjectService(storage)
            provider = (openai_queries.from_environment(os.environ)
                        if suggestion_provider is FROM_ENVIRONMENT else suggestion_provider)
            app.state.queries = QueryService(storage, provider)
            if paper_provider is OPENALEX_PROVIDER:
                retrieval_provider = OpenAlexPaperProvider()
            else:
                retrieval_provider = paper_provider
            app.state.retrieval = RetrievalService(storage, retrieval_provider)
            yield
        finally:
            if suggestion_provider is FROM_ENVIRONMENT and provider is not None:
                await provider.aclose()
            if paper_provider is OPENALEX_PROVIDER and retrieval_provider is not None:
                await retrieval_provider.aclose()
            if owned and storage is not None:
                storage.close()

    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exception):
        fields = []
        allowed = set(ProjectInput.model_fields) | set(QueryAddInput.model_fields) | {
            "project_id", "query_id"}
        for error in exception.errors():
            name = next((part for part in error["loc"] if part in allowed), "request")
            kind, context = error["type"], error.get("ctx", {})
            messages = {
                "missing": "This field is required.", "int_type": "Use a whole number.",
                "string_type": "Use text.", "list_type": "Use a list of keywords.",
                "extra_forbidden": "Unknown fields are not allowed.",
                "json_invalid": "The request must contain valid JSON.",
                "uuid_parsing": "Use a valid project ID.",
                "uuid_type": "Use a valid project ID.",
            }
            message = messages.get(kind, "Invalid or missing value.")
            if kind in {"string_too_short", "string_too_long", "too_long"}:
                minimum, maximum = context.get("min_length"), context.get("max_length")
                if minimum is not None:
                    message = f"Use at least {minimum} characters."
                elif maximum is not None:
                    unit = "keywords" if name == "keywords" and kind == "too_long" else "characters"
                    message = f"Use at most {maximum} {unit}."
            elif kind in {"greater_than_equal", "less_than_equal"}:
                key = "ge" if kind == "greater_than_equal" else "le"
                direction = "at least" if key == "ge" else "at most"
                message = f"Use a value {direction} {context[key]}."
            elif kind == "value_error" and name == "yearTo":
                message = "End year must not precede start year."
            elif kind == "value_error" and name == "text":
                message = "Use 1–160 characters of query text."
            fields.append({"field": name, "message": message})
        return error_response(
            422, "VALIDATION_ERROR", "Please check the highlighted fields.", fields
        )

    @app.exception_handler(ProjectNotFound)
    async def not_found(request, exception):
        return error_response(404, "NOT_FOUND", "Project not found.")

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request, exception):
        # Never log exception text, SQL, parameters, credentials, or database URLs.
        logger.warning("Project storage operation failed")
        return error_response(503, "STORAGE_UNAVAILABLE",
                              "Storage is temporarily unavailable. Please try again.")

    @app.exception_handler(QueryError)
    async def query_error(request, exception):
        return error_response(exception.status, exception.code, exception.message)

    @app.exception_handler(RetrievalError)
    async def retrieval_error(request, exception):
        return error_response(exception.status, exception.code, exception.message)

    @app.exception_handler(SearchInProgress)
    async def search_in_progress(request, exception):
        return error_response(409, "SEARCH_ACTIVE",
                              "A search is active for this project. Please wait before editing.")

    @app.get("/api/projects", response_model=list[ProjectOutput])
    def list_projects(request: Request):
        return request.app.state.projects.list()

    @app.post("/api/projects", response_model=ProjectOutput, status_code=201)
    def create_project(data: ProjectInput, request: Request):
        return request.app.state.projects.create(data)

    @app.get("/api/projects/{project_id}", response_model=ProjectOutput)
    def read_project(project_id: UUID, request: Request):
        return request.app.state.projects.read(project_id)

    @app.put("/api/projects/{project_id}", response_model=ProjectOutput)
    def update_project(project_id: UUID, data: ProjectInput, request: Request):
        return request.app.state.projects.update(project_id, data)

    @app.delete("/api/projects/{project_id}", status_code=204)
    def delete_project(project_id: UUID, request: Request):
        request.app.state.projects.delete(project_id)
        return Response(status_code=204)

    @app.get("/api/projects/{project_id}/queries", response_model=QueryListOutput)
    def list_queries(project_id: UUID, request: Request):
        return request.app.state.queries.list(project_id)

    @app.post("/api/projects/{project_id}/queries", response_model=QueryListOutput, status_code=201)
    def add_query(project_id: UUID, data: QueryAddInput, request: Request):
        return request.app.state.queries.add(project_id, data)

    @app.patch("/api/projects/{project_id}/queries/{query_id}", response_model=QueryListOutput)
    def patch_query(project_id: UUID, query_id: UUID, data: QueryPatchInput, request: Request):
        return request.app.state.queries.patch(project_id, query_id, data)

    @app.delete("/api/projects/{project_id}/queries/{query_id}", response_model=QueryListOutput)
    def delete_query(project_id: UUID, query_id: UUID, expectedRevision: str, request: Request):
        if not re.fullmatch(r"[0-9]+", expectedRevision) or len(expectedRevision) > 20:
            return error_response(422, "VALIDATION_ERROR", "Use a nonnegative integer revision.",
                                  [{"field": "expectedRevision", "message": "Invalid revision."}])
        return request.app.state.queries.delete(project_id, query_id, int(expectedRevision))

    @app.post("/api/projects/{project_id}/queries/generate", response_model=GenerationOutput)
    async def generate_queries(project_id: UUID, data: GenerateInput, request: Request):
        return await request.app.state.queries.generate(project_id, data)

    @app.post("/api/projects/{project_id}/search", response_model=SearchOutput)
    async def search_project(project_id: UUID, request: Request):
        return await request.app.state.retrieval.search(project_id)

    @app.get("/api/projects/{project_id}/papers", response_model=CurrentPapersOutput)
    def current_papers(project_id: UUID, request: Request):
        return request.app.state.retrieval.current(project_id)

    @app.get("/", include_in_schema=False)
    def homepage():
        return FileResponse(FRONTEND / "index.html")

    app.mount("/static", StaticFiles(directory=FRONTEND, check_dir=False), name="static")

    return app
