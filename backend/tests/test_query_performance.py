"""FR-QRY-008: approved real HTTP/PostgreSQL reference-host latency protocol."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
import pytest
from researchpilot.domain import ProjectInput
from researchpilot.service import ProjectService
from sqlalchemy import insert


@pytest.mark.performance
def test_FR_QRY_008_reference_host_latency(db, live_server, tmp_path):
    project_service = ProjectService(db)
    project_ids = [
        project_service.create(
            ProjectInput(
                title=f"Query performance {index}", researchQuestion="Question", maxPaperCount=100
            )
        ).id
        for index in range(100)
    ]
    target_id = project_ids[-1]
    rows = []
    for project_id in project_ids[:-1]:
        rows.extend(_query_row(project_id, slot) for slot in range(1, 21))
    rows.extend(_query_row(target_id, slot) for slot in range(1, 20))
    with db.engine.begin() as connection:
        connection.execute(insert(db.queries), rows)

    with live_server() as base, httpx.Client(base_url=base) as client:
        for _ in range(10):
            assert client.get(f"/api/projects/{target_id}/queries").status_code == 200

        samples = []
        revision = 0
        for cycle in range(20):
            query_id = None
            operations = ["add", "list", "edit", "toggle", "delete"]
            for operation in operations:
                path = f"/api/projects/{target_id}/queries"
                if operation in {"edit", "toggle", "delete"}:
                    assert query_id is not None
                    path += f"/{query_id}"
                start = perf_counter()
                if operation == "add":
                    response = client.post(
                        path, json={"text": f"Cycle {cycle}", "expectedRevision": revision}
                    )
                elif operation == "list":
                    response = client.get(path)
                elif operation == "edit":
                    response = client.patch(
                        path, json={"expectedRevision": revision, "text": f"Edited {cycle}"}
                    )
                elif operation == "toggle":
                    response = client.patch(
                        path, json={"expectedRevision": revision, "enabled": False}
                    )
                else:
                    response = client.delete(path, params={"expectedRevision": revision})
                duration_ms = (perf_counter() - start) * 1000
                expected_status = 201 if operation == "add" else 200
                samples.append(
                    {
                        "cycle": cycle + 1,
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "status": response.status_code,
                    }
                )
                if response.status_code != expected_status:
                    break
                if operation == "add":
                    state = response.json()
                    revision = state["revision"]
                    query_id = state["queries"][-1]["id"]
                elif operation in {"edit", "toggle", "delete"}:
                    state = response.json()
                    revision = state["revision"]

        ordered = sorted(sample["duration_ms"] for sample in samples)
        p95 = ordered[94] if len(ordered) >= 95 else None
        with db.engine.connect() as connection:
            postgres = connection.exec_driver_sql("SELECT version()").scalar_one()
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "unknown",
        )
        report = {
            "run_timestamp": datetime.now(UTC).isoformat(),
            "requirement": "FR-QRY-008 / approved query CRUD benchmark",
            "threshold_ms": 500,
            "p95_ms": p95,
            "request_count": len(samples),
            "seeded_projects": 100,
            "seeded_queries": len(rows),
            "target_initial_queries": 19,
            "warmup_read_requests": 10,
            "percentile_method": "nearest-rank, 95th of 100 sorted durations",
            "transport": "real loopback HTTP, persistent HTTPX client, PostgreSQL",
            "python": platform.python_version(),
            "os": platform.platform(),
            "cpu": cpu,
            "load_average": os.getloadavg(),
            "postgresql": postgres,
            "versions": {
                name: importlib.metadata.version(name)
                for name in ["fastapi", "sqlalchemy", "psycopg", "httpx"]
            },
            "baseline_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "dirty_working_tree": bool(
                subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
            ),
            "source_hashes": {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(
                    [
                        *Path("backend").rglob("*.py"),
                        *Path("frontend").glob("*"),
                        *Path("migrations").glob("*.sql"),
                    ]
                )
            },
            "samples": samples,
        }
        destination = Path(
            os.environ.get("PERFORMANCE_OUTPUT", str(tmp_path / "query-performance.json"))
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n")

    assert len(samples) == 100, f"Expected 100 requests, observed {len(samples)}"
    assert all(sample["status"] in {200, 201} for sample in samples), samples
    assert p95 is not None and p95 < 500, f"Reference-host p95 was {p95} ms"


def _query_row(project_id, slot):
    text = f"Seed query {slot} for {project_id}"
    return {
        "id": uuid4(),
        "project_id": project_id,
        "text": text,
        "normalized_key": text.casefold(),
        "enabled": True,
        "origin": "manual",
        "user_owned": True,
        "slot": slot,
    }
