"""Explicitly opted-in, offline real-model benchmark; never downloads weights."""

import asyncio
import hashlib
import json
import math
import os
import platform
import resource
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

import pytest
from researchpilot.embedding_provider import MODEL_ID, MODEL_REVISION, EmbeddingInput
from researchpilot.integrations.local_embeddings import LocalEmbeddingProvider


@pytest.mark.performance
def test_FR_RNK_009_offline_reference_model_performance():
    if os.environ.get("RUN_LOCAL_EMBEDDING_BENCHMARK") != "1":
        pytest.skip("Real-model benchmark requires explicit opt-in and installed pinned files")
    inputs = [
        EmbeddingInput(
            id=f"input-{i}",
            text=(f"Local semantic ranking benchmark input {i}. " + "synthetic timing text " * 300),
        )
        for i in range(251)
    ]

    async def benchmark():
        provider = LocalEmbeddingProvider()
        samples = []
        try:
            for index in range(23):
                started = time.perf_counter()
                result = await provider.embed(inputs)
                elapsed = (time.perf_counter() - started) * 1000
                assert result.dimension == 384 and len(result.items) == 251
                assert all(item.token_count == 256 and item.truncated for item in result.items)
                assert provider.active_process is None
                if index >= 3:
                    samples.append(elapsed)
            return samples, result.package_versions
        finally:
            await provider.aclose()

    samples, packages = asyncio.run(benchmark())
    p95 = sorted(samples)[math.ceil(0.95 * len(samples)) - 1]
    sources = [
        "pyproject.toml",
        "uv.lock",
        "backend/researchpilot/integrations/local_embeddings.py",
        "backend/researchpilot/ranking_domain.py",
        __file__,
    ]
    report = {
        "modelId": MODEL_ID,
        "modelRevision": MODEL_REVISION,
        "inferenceNetwork": "socket/DNS access denied inside inference child",
        "inputKind": "synthetic timing text, not scholarly records or quality evidence",
        "warmups": 3,
        "timedJobs": 20,
        "inputsPerJob": 251,
        "maxTokens": 256,
        "batchSize": 32,
        "threads": 4,
        "interopThreads": 1,
        "device": "cpu",
        "includes": ["child startup", "manifest hashes", "model loading", "inference", "cleanup"],
        "excludes": ["download", "HTTP", "PostgreSQL"],
        "samplesMs": samples,
        "nearestRankP95Ms": p95,
        "targetMs": 30000,
        "peakChildRssKiB": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostLoad": list(os.getloadavg()),
        "packageVersions": packages,
        "cpu": next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "",
        ),
        "memory": next(
            (
                line
                for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith("MemTotal:")
            ),
            "",
        ),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
        "sourceHashes": {
            str(Path(path).relative_to(Path.cwd()))
            if Path(path).is_absolute()
            else path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in sources
        },
        "pytest": version("pytest"),
    }
    target = Path(os.environ.get("PERFORMANCE_OUTPUT", "docs/evidence/ranking-performance.json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    assert p95 < 30000, f"Local ranking p95 {p95:.2f}ms exceeds 30000ms"
