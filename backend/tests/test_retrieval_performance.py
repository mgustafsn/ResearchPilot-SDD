"""FR-RET-002/006 proposed local retrieval pipeline reference-host benchmark."""

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
from researchpilot.paper_domain import Paper
from researchpilot.paper_provider import PaperSearchResult
from sqlalchemy import insert


class DeterministicPaperProvider:
    def __init__(self):
        self.calls = 0

    async def search(self, query, year_from, year_to, limit):
        self.calls += 1
        slot = int(query.rsplit(" ", 1)[1])
        papers = [
            Paper.model_validate(
                {
                    "provider": "openalex",
                    "provider_id": f"W{slot}-{index}",
                    "doi": None,
                    "title": f"Benchmark paper {slot}-{index}",
                    "authors": ["Fixture Author"],
                    "source_url": f"https://openalex.org/W{slot}-{index}",
                    "publication_year": 2024,
                }
            )
            for index in range(limit)
        ]
        return PaperSearchResult(papers=papers, raw_count=len(papers), request_count=1)


@pytest.mark.performance
def test_FR_RET_002_006_mock_provider_pipeline_reference_host(db, query_server, tmp_path):
    projects = []
    queries = []
    now = datetime.now(UTC)
    for project_index in range(100):
        project_id = uuid4()
        projects.append(
            {
                "id": project_id,
                "title": f"Retrieval benchmark project {project_index}",
                "research_question": "Fixture question",
                "keywords": [],
                "year_from": None,
                "year_to": None,
                "max_paper_count": 250,
                "created_at": now,
                "updated_at": now,
                "mutation_revision": 0,
                "query_context_revision": 0,
                "generated_context_revision": None,
            }
        )
        for slot in range(1, 21):
            query = f"Search {slot}"
            queries.append(
                {
                    "id": uuid4(),
                    "project_id": project_id,
                    "text": query,
                    "normalized_key": query.casefold(),
                    "enabled": True,
                    "origin": "manual",
                    "user_owned": True,
                    "slot": slot,
                }
            )
    with db.engine.begin() as connection:
        connection.execute(insert(db.projects), projects)
        connection.execute(insert(db.queries), queries)
    target_id = projects[-1]["id"]
    paper_provider = DeterministicPaperProvider()

    with query_server(paper_provider=paper_provider) as base:
        with httpx.Client(base_url=base, trust_env=False, timeout=30) as client:
            for _ in range(10):
                warmup = client.post(f"/api/projects/{target_id}/search")
                assert warmup.status_code == 200, warmup.text
                assert warmup.json()["rawFetchedCount"] == 250

            samples = []
            for iteration in range(20):
                start = perf_counter()
                response = client.post(f"/api/projects/{target_id}/search")
                duration_ms = (perf_counter() - start) * 1000
                samples.append(
                    {
                        "iteration": iteration + 1,
                        "duration_ms": duration_ms,
                        "status": response.status_code,
                        "raw_fetched_count": response.json().get("rawFetchedCount"),
                    }
                )
                assert response.status_code == 200, response.text
                assert response.json()["rawFetchedCount"] == 250
                assert len(response.json()["papers"]) == 250

    ordered = sorted(sample["duration_ms"] for sample in samples)
    p95 = ordered[18]  # nearest-rank p95 for 20 samples
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
        "requirement": "FR-RET-002/006 local mock-provider pipeline proposal",
        "threshold_ms": 2000,
        "p95_ms": p95,
        "request_count": len(samples),
        "seeded_projects": len(projects),
        "seeded_queries": len(queries),
        "records_per_attempt": 250,
        "provider_queries_per_attempt": 20,
        "warmup_requests": 10,
        "provider_call_count": paper_provider.calls,
        "percentile_method": "nearest-rank, 19th of 20 samples",
        "transport": "real loopback HTTP and PostgreSQL; deterministic fake PaperProvider",
        "python": platform.python_version(),
        "os": platform.platform(),
        "cpu": cpu,
        "load_average": os.getloadavg(),
        "postgresql": postgres,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("fastapi", "sqlalchemy", "psycopg", "httpx")
        },
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
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
        os.environ.get("PERFORMANCE_OUTPUT", str(tmp_path / "retrieval-performance.json"))
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    assert p95 < 2000, f"Proposed local mock-provider pipeline p95 was {p95:.2f} ms"
