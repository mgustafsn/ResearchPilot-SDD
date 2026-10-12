"""Same-origin local API. Configuration and raw database errors never reach the UI."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from researchpilot.domain import ProjectInput, ProjectOutput
from researchpilot.persistence import Database
from researchpilot.service import ProjectNotFound, ProjectService

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
logger = logging.getLogger("researchpilot")


def error_response(status, code, message, fields=None):
    return JSONResponse({"error": {"code": code, "message": message,
                                   "fields": fields or []}}, status_code=status)


def create_app(database=None):
    @asynccontextmanager
    async def lifespan(app):
        owned = database is None
        storage = None
        try:
            try:
                storage = database or Database(os.environ["DATABASE_URL"])
                storage.migrate()
            except Exception:
                raise RuntimeError("Database startup failed; check local configuration") from None
            app.state.database = storage
            app.state.projects = ProjectService(storage)
            yield
        finally:
            if owned and storage is not None:
                storage.close()

    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exception):
        fields = []
        allowed = set(ProjectInput.model_fields) | {"project_id"}
        for error in exception.errors():
            name = next((part for part in error["loc"] if part in allowed), "request")
            fields.append({"field": name, "message": "Invalid or missing value."})
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

    @app.get("/", include_in_schema=False)
    def homepage():
        return FileResponse(FRONTEND / "index.html")

    app.mount("/static", StaticFiles(directory=FRONTEND, check_dir=False), name="static")

    return app
