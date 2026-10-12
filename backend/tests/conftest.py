"""All destructive fixture operations require an explicitly disposable database."""

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from researchpilot.persistence import Database
from sqlalchemy import text
from sqlalchemy.engine import make_url


class SecretDatabaseURL(str):
    def __repr__(self):
        return "'<redacted database URL>'"


def require_safe_test_database(test_url=None, app_url=None, opt_in=None):
    test_url = test_url if test_url is not None else os.environ.get("TEST_DATABASE_URL", "")
    app_url = app_url if app_url is not None else os.environ.get("DATABASE_URL", "")
    opt_in = opt_in if opt_in is not None else os.environ.get("ALLOW_TEST_DATABASE_RESET", "")
    try:
        target = make_url(test_url)
        if (opt_in != "1" or target.database != "researchpilot_sdd_test"
                or target.get_backend_name() != "postgresql"):
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
        connection.execute(text("TRUNCATE projects"))
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
