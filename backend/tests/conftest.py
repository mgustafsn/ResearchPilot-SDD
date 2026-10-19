"""All destructive fixture operations require an explicitly disposable database."""

import asyncio
import os
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient
from researchpilot.persistence import Database
from researchpilot.query_domain import SuggestionBatch
from researchpilot.query_provider import SuggestionProviderError, SuggestionResult
from sqlalchemy import text
from sqlalchemy.engine import make_url


class SecretDatabaseURL(str):
    def __repr__(self):
        return "'<redacted database URL>'"


def run_async(coroutine):
    """Run on a fresh thread: Playwright may leave a loop running on the main thread."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


class FakeSuggestionProvider:
    """Test-only controlled provider; never performs HTTP or logs its context."""

    def __init__(self, queries=("AI tutoring", "Education", "Learning"), blocked=False):
        self.queries = queries
        self.contexts = []
        self.started = threading.Event()
        self.release = threading.Event()
        if not blocked:
            self.release.set()

    async def suggest(self, context):
        self.contexts.append(context)
        self.started.set()
        if not await asyncio.to_thread(self.release.wait, 5):
            raise SuggestionProviderError("timeout")
        return SuggestionResult(batch=SuggestionBatch(queries=list(self.queries)))


def require_safe_test_database(test_url=None, app_url=None, opt_in=None):
    test_url = test_url if test_url is not None else os.environ.get("TEST_DATABASE_URL", "")
    app_url = app_url if app_url is not None else os.environ.get("DATABASE_URL", "")
    opt_in = opt_in if opt_in is not None else os.environ.get("ALLOW_TEST_DATABASE_RESET", "")
    try:
        target = make_url(test_url)
        if (opt_in != "1" or not app_url or target.database != "researchpilot_sdd_test"
                or target.get_backend_name() != "postgresql"
                or target.host not in {"127.0.0.1", "localhost", "::1"}):
            raise ValueError
        if app_url:
            application = make_url(app_url)

            def identity(url):
                host = url.host or "localhost"
                addresses = frozenset(info[4][0] for info in socket.getaddrinfo(host, None))
                return addresses, url.port or 5432, url.database

            a, b = identity(target), identity(application)
            if a[1:] == b[1:] and a[0].intersection(b[0]):
                raise ValueError
    except Exception:
        raise RuntimeError("Refusing unsafe test database configuration") from None
    return SecretDatabaseURL(test_url)


@pytest.fixture
def db_url():
    return require_safe_test_database()


@pytest.fixture
def db(db_url):
    database = Database(db_url)
    database.migrate()
    with database.engine.begin() as connection:
        connection.execute(text(
            "TRUNCATE project_papers, search_runs, papers, search_queries, projects"
        ))
    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def live_server(db, db_url):
    @contextmanager
    def start():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        environment = dict(os.environ, DATABASE_URL=str(db_url),
                           PYTHONPATH=str(Path("backend").resolve()))
        # Never let a developer's real key enable live generation in tests.
        environment.pop("OPENAI_API_KEY", None)
        environment.pop("OPENALEX_API_KEY", None)
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "researchpilot.api:create_app", "--factory",
             "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
            env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            with httpx.Client(base_url=base) as client:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Local test server exited before readiness")
                    try:
                        if client.get("/api/projects").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                else:
                    raise RuntimeError("Local test server did not become ready")
            yield base
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return start


@pytest.fixture
def client(db):
    from researchpilot.api import create_app

    with TestClient(create_app(db, suggestion_provider=None)) as client:
        yield client


@pytest.fixture
def query_server(db):
    from researchpilot.api import create_app

    @contextmanager
    def start(provider=None, paper_provider=None):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        server = uvicorn.Server(uvicorn.Config(
            create_app(db, suggestion_provider=provider, paper_provider=paper_provider),
            host="127.0.0.1", port=port,
            log_level="warning", access_log=False,
        ))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            with httpx.Client(base_url=base, trust_env=False) as http:
                for _ in range(100):
                    try:
                        if http.get("/api/projects").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                else:
                    raise RuntimeError("Injected-provider server readiness failed")
            yield base
        finally:
            server.should_exit = True
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Injected-provider test server failed to shut down")
    return start
