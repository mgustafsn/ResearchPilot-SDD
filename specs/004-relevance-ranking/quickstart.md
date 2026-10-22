# Local ranking validation guide

**Status**: Guide approved with the plan on 2026-10-21; tasks/implementation subsequently
authorized (reply: “Start”). Commands below are implemented. Actual evidence is in
`docs/evidence-log.md`; this guide alone is not verification or human acceptance.

## Prerequisites

- Reviewed plan/contracts, separately approved tasks and implementation permission.
- Existing isolated PostgreSQL and ignored `.env`; disposable test DB safeguards
  from README retained. No OpenAI/embedding API key or paid account.
- CPU-only locked ML dependencies and pinned model revision from [plan](plan.md).
- Model installation directory ignored by Git; never commit weights or local secrets.

## Setup and start

1. Resolve/install approved locked packages with `uv sync`. Verify CPU-only torch;
   do not silently add CUDA or use another provider/model if resolution fails.
2. Explicitly invoke the setup module once (downloads public model files only):
   `PYTHONPATH=backend uv run python -m researchpilot.integrations.setup_embeddings`.
   This is the only embedding-related network setup step; use no HF token.
3. `docker compose up -d --wait db`, then `./scripts/start-local.sh`.
4. Open `http://127.0.0.1:8000/`. Existing 003 results should remain unranked and
   unchanged until a successful new explicit Search; startup/GET must not infer.

## Repeatable suite (no external calls/downloads)

After implementation, execute with guarded test environment:

```bash
uv run --env-file .env pytest backend/tests/test_ranking.py backend/tests/test_local_embeddings.py backend/tests/test_ranking_api.py backend/tests/test_ranking_postgres.py backend/tests/test_ranking_browser.py -q
uv run --env-file .env pytest -q -m 'not performance'
uv run ruff check backend
node --check frontend/app.js
git diff --check
```

Inject fake embeddings and PaperProvider; mock setup/loader. Include missing/corrupt
model, malformed vectors, busy job, timeout, cancellation, stale-owner, migration,
restart, hostile text and commit rollback. Prove child cleanup and no outbound
embedding traffic. No synthetic fixture paper is presented as real scholarly output.

## Separate offline real-model checks

After explicit setup, run local adapter integration/benchmark with outbound network
blocked in its child. Use non-scholarly synthetic text for inference timing; it is
not metadata or ranking-quality evidence. Benchmark 251 inputs (250 papers +
context), 256-token limit, CPU threads/batch as plan, 3 warm-ups +20 timed jobs.
Save raw timings, p95 nearest rank, peak RSS, host/load/package versions, revision,
source hashes and actual failure counts under `docs/evidence/`. Proposed target:
p95 <30 seconds including per-job startup/model loading. No download/network/
PostgreSQL in that timing. No result is claimed until actually run.

Keep existing fake retrieval/project/query performance protocols; if approved
reference OS/hardware has changed, report it before claiming budget acceptance.

Explicitly run the separate real-model benchmark after setup:

```bash
RUN_LOCAL_EMBEDDING_BENCHMARK=1 PERFORMANCE_OUTPUT=docs/evidence/ranking-performance.json uv run pytest backend/tests/test_ranking_performance.py -m performance -q
```

Recorded run on 2026-10-21: 20 timed jobs passed, p95 9.32 seconds. Same Ryzen CPU,
but Linux kernel 7.2.11-1 versus earlier approved 7.2.9-2; report this as a current-host
measurement, not formal acceptance on the unchanged original reference environment.

## Human journey and usefulness

- Explicit OpenAlex Search is still a real external action, not an offline test.
  Obtain permission before any agent-run live search; never trigger one just to
  validate the local adapter. The user can choose to search in their local app.
- Confirm every result remains, score ordering/labels make sense, old results
  survive a failed search, refreshed results retain score/provenance, and legacy
  results show “Not ranked” rather than fake scores.
- Follow the plan's frozen >=20 provider-paper, human-blind 0/1/2 label protocol.
  Record actual human labels or leave SC-RNK-003 pending, report metrics/limitations
  honestly and ask the user whether ordering is useful. No AI-created citations,
  human labels, universal accuracy claim, or inherited-calibration validation.
- Obtain explicit human keyboard/usability review and final feature acceptance.
