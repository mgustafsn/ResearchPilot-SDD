# Tasks: Local semantic relevance ranking

**Created**: 2026-10-21 | **Feature**: `004-relevance-ranking` | **Actual Git branch**: `main`
**Status**: Tasks approved and implementation authorized by the user on 2026-10-21
(reply: “Start” to “Approve tasks and start implementation?”).

**Inputs**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [API contract](contracts/api.md),
[embedding contract](contracts/embedding.md), [quickstart.md](quickstart.md).

Tests are mandatory under constitution VI; generic optional-test wording does not
apply. Write behavior tests and record genuine red failures before implementation.
No automated test contacts OpenAlex, OpenAI, a package registry or the model Hub.
Only explicit approved setup may download weights; never startup, Search or CI.
Do not implement feature 005, clustering, embedding caches, or deferred BUG-PRJ-001.

## Phase 1: Setup

**Goal**: Confirm gates and prepare the approved dependency/configuration paths.

- [X] T001 Reconfirm explicit task/implementation approval, active feature, constitution I–VII, clean/dirty baseline and prior full-suite evidence in `docs/evidence-log.md`; preserve unrelated work and actual branch `main`; run the existing complete suite against the guarded disposable DB before changes. Baseline: 358 passed.
- [X] T002 Resolve `sentence-transformers==6.2.0`, necessary CPU-only torch and directly declared `huggingface-hub` in `pyproject.toml` and `uv.lock`; verify compatibility/imports and explicit CPU wheel sourcing without CUDA dependencies. Record actual versions/download sizes in `docs/evidence-log.md`; stop/report incompatibility rather than silently replace the approved model. Do not download model weights yet. CPU torch 2.14.1+cpu verified; packages installed before model setup.
- [X] T003 Add ignored `.models/` installation location in `.gitignore` and server-only `EMBEDDING_MODEL_DIR` documentation in `.env.example` and `README.md`; document explicit setup/offline runtime, no cloud keys, fixed revision and no automatic repair/download. Do not overwrite user `.env` or expose model paths to browsers.

## Phase 2: Foundational rules and storage

**Goal**: Establish vendor-free contracts and additive storage without disturbing 003.

- [X] T004 [P] Write `backend/tests/test_ranking.py` for exact NFC/whitespace/separator/order normalization, title-only input, SHA-256 UTF-8 and canonical token hashes, finite-vector/type/coverage validation, overflow-safe cosine, zero norms, calibration/clipping/rounding and score/title/source ordering; record red behavior failures before T006 (FR-RNK-001–004/006). Initial pure rules: 30 failed on unimplemented behavior.
- [X] T005 [P] Write `backend/tests/test_ranking_postgres.py` migration tests for 003→004 legacy preservation, fresh/repeated migration, transactional rollback, score/provenance constraints and restart. Quote model constraints: score “Between 0 and 1 inclusive; null only for legacy unranked rows”, provenance “Present iff score present”; JSON object shape and paired nullability. Retain guarded disposable-target checks; record red failures before T007 (FR-RNK-006/007). Initial schema tests: 7 failed before migration 004.
- [X] T006 Implement `backend/researchpilot/ranking_domain.py` and `backend/researchpilot/embedding_provider.py` with vendor-free structured input/batch/error models, exact approved normalization/inputVersion, hash helpers and validation/scoring/order. Require unique ordered IDs, complete coverage, numeric finite nonboolean vectors, common dimension >0 (384 for local adapter); provenance hashes lowercase SHA-256, tokens 1–256, fixed model/revision. Domain logic must not import ML vendors or alter provider Paper metadata (FR-RNK-001–004/006/008).
- [X] T007 Implement additive `migrations/004_local_ranking.sql` and extend `backend/researchpilot/persistence.py`: nullable NUMERIC(7,6) `embedding_score`, nullable JSONB-object `ranking_provenance` on project_papers, paired nullability and 0–1 bound; nullable run-level JSONB-object provenance. Preserve all old rows/order as null/null; no backfill, vector table or earlier migration edits. Keep service-level structured validation for all provenance fields (FR-RNK-006). Existing automatic table reflection required no persistence-code edit. Rules/schema green: 37 passed.
- [X] T008 Adapt only necessary migration-version assertions and fake-provider wiring in `backend/tests/conftest.py`, `backend/tests/test_project_postgres.py`, `backend/tests/test_retrieval_postgres.py` and other affected tests; retain exact test table cleanup, opt-in/name/host/distinct-target guards and secret redaction. Add injectable fake embedding providers with no live dependencies, no production fake mode and no bypass of ranking validation; rerun migration/previous regression tests (FR-RNK-006–009).

## Phase 3: User Story 1 — Browse ranked results (P1, MVP)

**Goal**: Explicit Search produces locally ranked, fully visible results with durable
provenance; every ranking failure preserves previous useful results.

**Independent test**: Create a project with enabled saved queries, inject fake
PaperProvider and fixed embedding vectors, execute explicit Search over loopback,
inspect scores/order/provenance and refresh. Then inject failures/stale ownership
and prove old paper metadata, associations and scores remain unchanged. Separately
test the local adapter with mocked loader/worker; no network/model install needed.

### Tests first

- [X] T009 [P] [US1] Write setup/loader tests in `backend/tests/test_local_embeddings.py` for pinned revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, exact file/module allowlist (Transformer→mean Pooling→Normalize), safetensors-only manifest hashes, staging/promotion, repeat setup without network, partial/corrupt/different target refusal, no credentials/telemetry/remote code and missing model errors. Mock every setup download; record red before T015 (FR-RNK-008/009).
- [X] T010 [US1] Extend `backend/tests/test_local_embeddings.py` for CPU float32/eval/no-grad, batch 32, at most four CPU threads/one interop thread, 256-token right truncation including special tokens, exact consumed-token hashes/count/flags, validated 384-dimensional outputs, offline flags before imports and socket-denied child inference. Assert no project/text/path/vector/secret leakage; record red before T016 (FR-RNK-001/002/006/008/009).
- [X] T011 [US1] Extend `backend/tests/test_local_embeddings.py` for one nonqueued ranking slot, busy error, 60-second inclusive load/inference budget, timeout/cancellation/shutdown child terminate/join/kill cleanup, slot release and malformed/crashed-child outputs. Use deterministic barriers/fake workers, not slow real deadlines; record red before T016 (FR-RNK-007–009). Combined adapter/setup red 14 failed, green 14 passed; real socket-denied model run passed separately.
- [X] T012 [P] [US1] Write `backend/tests/test_ranking_api.py` with fake providers for exact snapshotted context, retrieval→dedup→ranking→commit order, all scores/IDs/provenance, title-only cases, 0%-retention, empty success without model call, null legacy scores, GET/startup never infer/download, and safe embedding-specific error schemas; record red before T017–T019 (FR-RNK-001–009). Initial API/browser red: 10 failed before integration.
- [X] T013 [US1] Extend `backend/tests/test_ranking_postgres.py` for atomic nonempty/empty replacement, per-project scores versus shared provider facts, successful run context and per-paper provenance persistence/restart, no vector storage, every embedding failure and final-commit failure rollback, 240-second ownership/stale-writer rejection, cross-project busy ranking, no DB lock across inference and 210-second pipeline timeout; record red before T017–T019 (FR-RNK-006/007). Additional barrier/cancel/commit regressions were added after integration; this ordering deviation and remaining coverage limits are recorded in the evidence log, not represented as prior red tests.
- [X] T014 [P] [US1] Write `backend/tests/test_ranking_browser.py` for explicit pending/success/failure journey, score ordering/all papers including 0%, one-decimal embedding-similarity percentage, provisional/non-probability/non-quality disclosure, model/revision/English/256-token/truncation labels, legacy “Not ranked”, refresh, safe hostile text/links, keyboard/focus and stale-navigation protection; record red before T020 (FR-RNK-004–009). Browser/API regressions plus retained retrieval/browser tests pass; human keyboard review still T029.

### Implementation

- [X] T015 [US1] Implement `backend/researchpilot/integrations/setup_embeddings.py`: explicit CLI only, pinned public allowlisted safetensors/tokenizer/config/card/license files, no login token or user texts, telemetry disabled, 30-second request/10-minute overall budget, no application retry, staged SHA-256 manifest and atomic completion. Refuse to overwrite partial/different installation; no broad deletion, DB access or startup hooks. Run mocked T009 tests before any actual setup (FR-RNK-008/009).
- [X] T016 [US1] Implement `backend/researchpilot/integrations/local_embeddings.py` behind EmbeddingProvider: verified manifest, offline flags before ML imports, local_files_only/trust_remote_code false/token false/CPU/safetensors, approved module chain and token policy. Spawn one short-lived child per nonempty job with hard 60-second cleanup and nonqueued process-local slot; return structured vectors/token provenance, sanitize every loader/child error and reap on cancellation/shutdown. Run T010–T011 tests; no DB/network in inference (FR-RNK-001/002/006–009).
- [X] T017 [US1] Extend `backend/researchpilot/retrieval_service.py` to snapshot question/keywords in memory, deduplicate before local ranking, validate scores/provenance, preserve duplicate counts, use 210-second pre-commit deadline and 240-second new leases, and atomically commit ranked order/run/provenance only under current ownership. Preserve old metadata/results/scores on any embedding/validation/busy/storage/expiry failure; successful empty retrieval skips model and clears current results (FR-RNK-001–007).
- [X] T018 [US1] Extend response models in `backend/researchpilot/paper_domain.py` and read/commit mapping in `backend/researchpilot/retrieval_service.py` for bounded `embeddingScore`, per-paper `rankingProvenance` and attempt provenance. Legacy rows return null/null in original order; failed latest attempts must not relabel old scores with failed context. Persist input/model/scoring versions, exact normalized/token hashes, token counts/flags, dimension, package versions and run identity; no raw tokens/vectors/paths in JSON/storage (FR-RNK-004–007).
- [X] T019 [US1] Compose the local adapter at `backend/researchpilot/api.py` with test-only injection, lazy safe model availability and managed shutdown; app startup/read must work without model. Add contract-defined EMBEDDING_* 502/503/504 and SEARCH_TIMEOUT mappings without raw exceptions or misleading OpenAlex messages; retain existing 409/storage/project/query contracts (FR-RNK-007–009).
- [X] T020 [US1] Extend `frontend/app.js`, `frontend/index.html` and `frontend/styles.css` with score/model/provenance/truncation/legacy displays and approved disclaimers; retain every paper, provider links and source text safety. Keep previous results visible on pending/failure and ignore stale view callbacks. No new toggles, cloud fallback, stage-history polling or download UI (FR-RNK-004–009).
- [X] T021 [US1] Run focused domain/adapter/API/PostgreSQL/browser tests and all feature-001–003 regressions; fix only test-backed in-scope failures in `backend/researchpilot/`, `backend/tests/` and `frontend/`; record commands, red/green counts, actual versions, requirement mapping and no-prompt-change status in `docs/evidence-log.md` before claiming US1 complete (FR-RNK-001–009, AC-RNK-001–004). Full run: 426 passed, 1 opt-in benchmark skipped; benchmark passed separately.

**Checkpoint**: US1 is demonstrable with fake providers; this is not yet actual
model performance verification, human usefulness evaluation or final acceptance.

## Phase 4: Audit, offline model verification and acceptance

- [X] T022 [P] Add real offline adapter integration/performance protocol in `backend/tests/test_ranking_performance.py` and `docs/verification.md`: pinned installed model, outbound-denied child, 251 inputs reaching the token limit, 3 warm-ups/20 timed jobs, nearest-rank p95 <30 seconds including process/model startup, CPU/batch/thread controls, raw samples/peak RSS/host/load/package/revision/source hashes; keep it separate from repeatable fake tests and prior DB pipeline budgets. Do not claim a run yet (FR-RNK-008/009). Protocol implemented; subsequent actual run is T025.
- [X] T023 [P] Update `.gitlab-ci.yml` and `backend/tests/conftest.py` to run complete repeatable 001–004 logic/migration/mock-adapter/browser tests without weights/downloads/live providers/keys; retain secret/environment/test-DB protections, exclude real-model reference-host performance from ordinary CI, and report remote CI truthfully rather than equating a pending runner with success (Constitution VI). GitHub Actions run 39827940845 passed (423 passed, 4 performance tests deselected); GitLab pipeline 6874 remains unverified.
- [X] T024 Audit code/config/schema/setup under `backend/researchpilot/`, `migrations/004_local_ranking.sql`, `frontend/`, `.gitlab-ci.yml` and `.gitignore` for vendor isolation, no LLM metadata flow/cloud embeddings, no telemetry/implicit credentials/download on Search, exact model/file/module allowlist, no raw text/vector/path logging, bounded child lifecycle and safe DB cleanup. Record findings/fixes/limitations and rerun affected tests in `docs/evidence-log.md` (FR-RNK-001–009).
- [X] T025 After mocked setup/adapter tests and audit pass, explicitly run `backend/researchpilot/integrations/setup_embeddings.py` once using the approved setup design; verify exact revision/file hashes/license, CPU-only installation and ignored model files, then run real inference with outbound-denied child and the approved benchmark. Store actual raw evidence at `docs/evidence/ranking-performance.json`; no OpenAlex/OpenAI request, cloud fallback, hidden retry or fabricated result (FR-RNK-008/009). 11 files/91,578,415 bytes verified; real benchmark p95 9,317.18 ms. Current kernel differs from original reference; formal unchanged-environment performance acceptance not claimed.
- [ ] T026 Prepare the SC-RNK-003 frozen >=20 provider-derived paper set and user-chosen question protocol in `docs/evidence/ranking-quality.md`, using only available provider-derived data or separately authorized retrieval. Ask for human 0/1/2 labels before showing scores; record hashes/provenance and actual labels or mark pending. Report top-five labels, nDCG@10 where defined, saturation/ties/misorderings versus retrieval order; no AI labels or unapproved calibration changes (SC-RNK-003).
- [X] T027 [P] Update `README.md`, `specs/004-relevance-ranking/quickstart.md`, `docs/verification.md` and `docs/evidence/ranking-traceability.md` with runnable setup/recovery/test steps, local-versus-OpenAlex data disclosure, model limitations, all FR-RNK-001–009/AC-RNK-001–004 mappings, actual versus pending evidence and no-prompt-change status; never present instructions as executed verification.
- [X] T028 After audit fixes, run the entire application suite plus separate installed-model offline integration/benchmark and existing approved project/query/retrieval benchmarks; run Ruff, formatting checks for changed files, JS syntax, migration/restart/concurrency, secret/model-ignore and `git diff --check` checks. Record exact environment/commands/results in `docs/evidence-log.md`; resolve failures before claiming implementation tasks complete (Constitution VI). Full suite 426 passed, 1 skipped; real benchmark separately passed. New/formatted feature files checked; legacy shared files not mass-reformatted.
- [ ] T029 Present the local feature for human keyboard/usability and ranking-usefulness review, record explicit acceptance/remaining limitations in `docs/evidence-log.md` and this task list; do not mark human labels, ranking usefulness, or final acceptance complete without actual evidence. Remote CI is recorded separately. Do not begin feature 005 implementation without its separate approved gates.

## Dependencies and execution order

```text
Task/implementation approval (pending)
  → T001–T003 setup
  → T004–T008 foundational tests/rules/schema
  → US1 tests T009–T014
  → setup/adapter T015–T016 → service/models/API T017–T019 → UI T020
  → US1 regression checkpoint T021
  → protocols/CI T022–T023 → audit T024 → real setup/model run T025
  → human evaluation T026 + documentation T027 → full verification T028
  → human acceptance T029
```

Only one user story exists; do not invent independent stories to split its mandatory
failure safety from success behavior. Existing 003 is a prerequisite. T008 may
prepare future injection plumbing but must not bypass ranking for newly ranked
search tests; retest after T019 composition. T013/T014 red-phase runs must fail
because behavior is missing, not unsafe targets, imports or absent external services.

## Parallel opportunities

- Foundations: T004 and T005 author different files before their production changes.
- US1: T009, T012 and T014 author adapter/API/browser tests independently after
  foundations. T010/T011 extend T009's file sequentially; T013 extends T005's file.
- Polish: T022/T023 are file-independent; T027 follows actual run/audit evidence.
- `[P]` denotes file-independent authoring, not delegation permission. No delegates
  are authorized. DB-destructive suites remain sequential against the shared test DB.

## Implementation strategy and scope

MVP is the complete US1 with safe failure behavior, not a partial ranked-results
demo that overwrites old results. Build tests/rules/storage first, mock-tested
setup/adapter next, then integrate service/API/UI. Verify with fakes before explicit
weights setup. Finish real offline performance and honest human usefulness review.
Stop for incompatibility or a failed gate; no cloud or lexical fallback.

Counts: **29 tasks**; setup **3**, foundational **5**, US1 **13** (6 test tasks,
7 implementation/regression tasks), final audit/verification **8**. **27 complete**;
T026 (human-labeled quality evaluation) and T029 (human review/acceptance) remain
pending. GitHub Actions passed; GitLab CI is unverified. No final feature acceptance is inferred.

## Requirement mapping

| Requirement | Tasks |
|---|---|
| FR-RNK-001 | T004, T006, T010, T012, T016–T017, T021, T024, T027–T028 |
| FR-RNK-002 | T004, T006, T010–T012, T016–T017, T021, T024, T027–T028 |
| FR-RNK-003 | T004, T006, T012, T017, T021, T024, T026–T028 |
| FR-RNK-004 | T004, T006, T012, T014, T017–T018, T020–T021, T027–T028 |
| FR-RNK-005 | T012, T014, T020–T021, T027–T029 |
| FR-RNK-006 | T004–T008, T010, T012–T013, T016–T018, T021, T024, T027–T028 |
| FR-RNK-007 | T005, T008, T011–T014, T016–T021, T024, T027–T029 |
| FR-RNK-008 | T003, T006, T008–T012, T015–T016, T019, T021–T025, T027–T028 |
| FR-RNK-009 | T002–T003, T008–T012, T014–T016, T019–T025, T027–T029 |

AC-RNK-001: T004/T012/T013; AC-RNK-002: T004/T012/T014;
AC-RNK-003: T012/T014/T020; AC-RNK-004: T011–T013/T017–T019.
SC-RNK-003 requires T026/T029 human evidence, not unit-test inference.
