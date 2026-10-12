"""NFR-PRJ-003: approved real HTTP/PostgreSQL reference-host protocol."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx
import pytest
from researchpilot.domain import ProjectInput
from researchpilot.service import ProjectService
from sqlalchemy import text


@pytest.mark.performance
def test_NFR_PRJ_003_reference_host_latency(db, live_server, tmp_path):
    values = {"title": "Performance project", "researchQuestion": "A research question",
              "maxPaperCount": 100}
    service = ProjectService(db)
    for _ in range(100):
        service.create(ProjectInput(**values))
    with db.engine.connect() as connection:
        postgres = connection.execute(text("SELECT version()")).scalar_one()
    samples = []
    with live_server() as base:
        with httpx.Client(base_url=base) as client:
            for _ in range(10):
                assert client.get("/api/projects").status_code == 200
            for cycle in range(20):
                project_id = None
                for operation in ["create", "list", "detail", "update", "delete"]:
                    path = "/api/projects" if operation in {"create", "list"} else (
                        f"/api/projects/{project_id}"
                    )
                    method = {"create": "POST", "list": "GET", "detail": "GET",
                              "update": "PUT", "delete": "DELETE"}[operation]
                    options = {"json": values} if operation in {"create", "update"} else {}
                    start = perf_counter()
                    response = client.request(method, path, **options)
                    duration_ms = (perf_counter() - start) * 1000
                    samples.append({"cycle": cycle + 1, "operation": operation,
                                    "duration_ms": duration_ms, "status": response.status_code})
                    expected_status = {"create": 201, "delete": 204}.get(operation, 200)
                    assert response.status_code == expected_status
                    if operation == "create":
                        project_id = response.json()["id"]
            assert len(client.get("/api/projects").json()) == 100
    ordered = sorted(sample["duration_ms"] for sample in samples)
    cpu = next((line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")), "unknown")
    report = {
        "run_timestamp": datetime.now(UTC).isoformat(),
        "requirement": "NFR-PRJ-003", "threshold_ms": 500, "p95_ms": ordered[94],
        "request_count": 100, "seeded_projects": 100, "warmup_read_requests": 10,
        "percentile_method": "nearest-rank, 95th of 100 sorted durations",
        "transport": "real loopback HTTP, persistent HTTPX client, PostgreSQL",
        "python": platform.python_version(), "os": platform.platform(), "cpu": cpu,
        "load_average": os.getloadavg(), "postgresql": postgres,
        "versions": {name: importlib.metadata.version(name)
                     for name in ["fastapi", "sqlalchemy", "psycopg", "httpx", "playwright"]},
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "dirty_working_tree": bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True).strip()),
        "source_hashes": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted([*Path("backend").rglob("*.py"),
                                *Path("frontend").glob("*"),
                                *Path("migrations").glob("*.sql")])
        },
        "samples": samples,
    }
    destination = Path(os.environ.get("PERFORMANCE_OUTPUT", str(tmp_path / "performance.json")))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Reference-host p95: {ordered[94]:.2f} ms; samples: {destination}")
    assert ordered[94] < 500
