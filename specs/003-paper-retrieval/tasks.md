# Tasks: OpenAlex retrieval and deduplication

**Created**: 2026-10-19 | **Feature**: `003-paper-retrieval` | **Actual Git branch**: `main`
**Status**: Approved by the user on 2026-10-19 (reply: “yes i reviewed go ahead”); feature-003 implementation is authorized.

**Inputs**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [API contract](contracts/api.md),
[provider contract](contracts/provider.md), and [quickstart.md](quickstart.md).

Tests are mandatory under constitution Principle VI even though the generic task
template calls them optional. Write behavior tests before corresponding production
logic. No tests may contact OpenAlex or OpenAI. No task authorizes live smoke calls,
paid API keys, feature 004/005 work, or fixing deferred BUG-PRJ-001.

## Phase 1: Setup

**Goal**: Reconfirm gates and prepare only this feature's safe test/configuration paths.

- [X] T001 Verify approved feature-003 spec/plan/API/provider contracts in `docs/evidence-log.md`, current active feature in `.specify/feature.json`, and Constitution Principles I–VII in `specs/003-paper-retrieval/plan.md`; record baseline commit/environment and preserve actual Git branch `main`. Baseline commit `c5f2274`; branch `main`; PostgreSQL 17 container healthy; full non-performance suite 279 passed, 2 deselected.
- [X] T002 Verify existing runtime HTTPX and locked version in `pyproject.toml` and `uv.lock`; do not add dependencies or an OpenAlex/OpenAI credential. Record no-dependency decision in `specs/003-paper-retrieval/plan.md` and keep OpenAI unconfigured per user preference. Verified HTTPX 0.28.1 in the project environment and runtime/lock declarations; no OpenAI/OpenAlex key or model is configured; no dependency added.
- [X] T003 Update `README.md` and `specs/003-paper-retrieval/quickstart.md` with the approved explicit-Search/OpenAlex disclosure, no OpenAI request, no API-key/paid-account setup, and safe local test database prerequisites; do not make provider calls. Done; see updated files. No provider calls.

## Phase 2: Foundational schema, models, and fixtures

**Goal**: Create common provider/domain types and guarded durable storage needed by both user stories.

- [X] T004 [P] Write pure domain tests in `backend/tests/test_papers.py` for strict normalized Paper fields, DOI normalization, inclusive year bounds, ordered raw-budget allocation (1/20/100/250), zero allocations, title normalization, richness scoring and deterministic conflicting-DOI/transitive-bridge behavior; record failures before T006 (FR-RET-002–005). Added importable `NotImplementedError` domain scaffolds; red phase: 18 failed, all at unimplemented behavior.
- [X] T005 [P] Write PostgreSQL migration/model tests in `backend/tests/test_retrieval_postgres.py` for migration version 003, repeat migration, rollback, Paper provider-ID uniqueness, ProjectPaper uniqueness/order, SearchRun status/count constraints, one pending run per project, project cascades, and test-target guards; record failures before T008 (FR-RET-006–008). Red phase: 4 failed, all due absent migration/reflection/schema behavior.
- [X] T006 Implement common normalized `Paper`, `PaperSearchResult`, attempt/query allocation types, DOI/title normalization, allocation, deterministic dedup/merge and URL validation in `backend/researchpilot/paper_domain.py`; add the vendor-free `PaperProvider` protocol and safe error/result types in `backend/researchpilot/paper_provider.py`. Preserve missing optional facts; never accept LLM metadata (FR-RET-002–005). `backend/tests/test_papers.py`: 25 passed.
- [X] T007 [P] Implement the additive `migrations/003_paper_retrieval.sql` schema and `backend/researchpilot/persistence.py` reflection for `papers`, `project_papers` and `search_runs`. Include required source identity/title, nonnegative count checks, status enum `pending/succeeded/failed`, unique `(provider, provider_id)`, unique current project/paper and ordinal, and a partial unique pending-run-per-project index. Do not edit migrations 001/002 or add reference/ranking tables (FR-RET-006–008). Applied only to guarded disposable test DB; existing project migrations remain unchanged.
- [X] T008 Extend `backend/tests/conftest.py` cleanup to truncate only the explicitly configured local disposable database's reviewed feature tables in FK-safe order; preserve opt-in/name/host/distinct-target guards, redacted URLs and test-only provider injection. Run migration safety tests in `backend/tests/test_retrieval_postgres.py` before proceeding (Principles III/VI/VII). `backend/tests/test_retrieval_postgres.py backend/tests/test_project_postgres.py`: 30 passed; OpenAI/OpenAlex keys stripped from subprocess test environment.

## Phase 3: User Story 1 — Retrieve real papers (Priority: P1, MVP)

**Goal**: On explicit Search, retrieve normalized, unique OpenAlex works for the exact enabled query snapshot and show safe source links.

**Independent test**: With a fake PaperProvider/HTTPX mock and disposable PostgreSQL, create a project and stored queries, explicitly search, then verify allocation, normalized unique papers, source links, counts, query snapshot, and a successful empty result replacing old current results. No live provider is required.

### Tests for User Story 1

- [X] T009 [P] [US1] Write HTTPX `MockTransport` tests in `backend/tests/test_openalex_provider.py` for exact HTTPS `/works` request, saved query as-is, inclusive year filters, bounded `per_page`/page/`select`, at most 20 calls, no question/keywords/API key, no redirects/proxy inheritance, response-size bounds and normalized OpenAlex fields; record failures before T013 (FR-RET-001–003/009). Red phase: 15 failed on the importable adapter's unimplemented behavior.
- [X] T010 [P] [US1] Write fake-provider API tests in `backend/tests/test_retrieval_api.py` for explicit `POST /api/projects/{id}/search`, exact enabled query/year snapshot, ordered per-query allocations, zero-allocation queries unused, actual queries used, result/summary output, no-enabled-query behavior and `GET` never triggering a provider call; record failures before T015 (FR-RET-001/002/006). Red phase: 4 failed because search/results routes are absent.
- [X] T011 [P] [US1] Write real-PostgreSQL success tests in `backend/tests/test_retrieval_postgres.py` for normalized Paper upsert, ordered ProjectPaper replacement, duplicate counters, successful empty replacement, SearchRun snapshots/counts and restart persistence. Ensure writes happen only after all provider calls succeed; record failures before T014 (FR-RET-003–007). Red phase: 2 failed because success-path endpoints/persistence are absent; foundational schema tests remained green.
- [X] T012 [P] [US1] Write real-server/Chromium tests in `backend/tests/test_retrieval_browser.py` for explicit Search disclosure, pending/success/empty states, result metadata/source links, unknown OA status, keyboard/focus, and text-only hostile metadata/unsafe-link rejection; record failures before T016 (FR-RET-001/003/006/009/010). Red phase: 2 failed because Search/results UI is absent.

### Implementation for User Story 1

- [X] T013 [US1] Implement the bounded HTTPX OpenAlex adapter in `backend/researchpilot/integrations/openalex_papers.py`: no key by default, no OpenAI, exact saved query only, inclusive date filters, select required fields, paginate only to allocation, max 20 requests/attempt and two concurrent calls, approved response/time limits, no retry, strict envelope validation and sanitized errors. Reconstruct abstracts from inverted-index positions; do not fetch full text (FR-RET-001–003/009). Mock adapter tests: 15 passed. Ruff and formatting checks pass.
- [X] T014 [US1] Implement success-path retrieval orchestration in `backend/researchpilot/retrieval_service.py`: capture project/context/enabled-query snapshot under parent-first lock, allocate raw limits in stored order, release DB transaction before provider awaits, normalize/deduplicate deterministically, persist SearchRun/Paper/ProjectPaper atomically only after complete success, and replace current associations with empty on successful zero-result search (FR-RET-001–007). Focused API/PostgreSQL tests pass for snapshot, allocation, persistence, replacement and empty success.
- [X] T015 [US1] Add `POST /api/projects/{project_id}/search` and `GET /api/projects/{project_id}/papers` in `backend/researchpilot/api.py`; compose only the OpenAlex PaperProvider for explicit retrieval, return fixed safe response/error schemas, avoid exposing raw provider data/query URLs, and keep existing project/query JSON contracts intact (FR-RET-001/006/009). Search only runs on explicit POST; GET does not call the provider.
- [X] T016 [US1] Add labeled Search/results/status controls in `frontend/index.html`, `frontend/app.js` and `frontend/styles.css`; show the approved OpenAlex-not-OpenAI disclosure, actual query/count status and safe source links, use text nodes only, reject unsafe URL schemes, and bind callbacks to project/view identity without triggering on page load (FR-RET-001/006/009/010). Browser tests pass; UI values remain text-only and unsafe links are omitted.

**Checkpoint**: User Story 1 works with mocks and PostgreSQL. Search returns attributable unique metadata; the UI never fabricates paper facts or connects to OpenAI.

## Phase 4: User Story 2 — Recover safely (Priority: P1)

**Goal**: Preserve useful results on failures and reject conflicting or stale workers.

**Independent test**: Seed a known current result set, inject provider, timeout, invalid-response, DB-commit, concurrent-search and expiry schedules; verify failures preserve associations, while successful empty search replaces them.

### Tests for User Story 2

- [X] T017 [P] [US2] Extend `backend/tests/test_openalex_provider.py` for 429, 4xx/5xx, transport failure, timeout/cancellation, invalid JSON/envelope, malformed individual records, oversized body, request-cap exhaustion and single-attempt behavior; assert secrets/query/body/exception text never appear in logs (FR-RET-003/006/007). Provider HTTP suite passes, including redaction after disabling HTTPX query-URL access logs.
- [X] T018 [P] [US2] Extend `backend/tests/test_retrieval_api.py` with old-results preservation for each failed enabled-query call, sanitized 409/502/503/504/DB errors, blocked project/query mutation and second-search conflicts, and stale/expired attempt rejection (FR-RET-006–008). API failure-preservation and safe error tests pass.
- [X] T019 [US2] Add PostgreSQL barrier tests in `backend/tests/test_retrieval_postgres.py` for simultaneous starts, project/query mutation and deletion during a live lease, worker expiry/replacement, stale late commit rejection, every-query-failure rollback, commit failure, restart/lazy expired-run recovery and reference-independent associations. Tests must prove no DB lock spans provider await (FR-RET-006–008). Active conflict, expired-owner replacement, lazy recovery and injected final-commit rollback tests pass.

### Implementation for User Story 2

- [X] T020 [US2] Implement SearchRun ownership-token/lease lifecycle and atomic failure recording in `backend/researchpilot/retrieval_service.py`; all request/validation/storage failures mark a safe terminal state and leave prior ProjectPaper rows and Paper facts unchanged; successful empty results remain a success (FR-RET-006/007/008). Provider, stale-owner and injected commit failures preserve previous associations.
- [X] T021 [US2] Extend parent-first mutation guards in `backend/researchpilot/service.py` and `backend/researchpilot/query_service.py` so project edit/delete and query add/edit/toggle/delete conflict during an unexpired search; expired attempts are marked interrupted and release the project without accepting late writes (FR-RET-008). Tests cover all five mutation operations and reads during provider wait.
- [X] T022 [US2] Add sanitized stale/active/timeout/unavailable/invalid/storage error mapping and lazy lease recovery to `backend/researchpilot/api.py`; keep raw query, upstream body/URL, SQL, exception strings and credentials out of logs and browser responses (FR-RET-006–008). Current-results GET lazily expires stale owners.
- [X] T023 [US2] Complete pending/failure/conflict behavior in `frontend/app.js`, `frontend/index.html` and `frontend/styles.css`; preserve previous results on any failed search, show a readable error, block conflicting actions while active, recover expired pending state, and ignore stale callbacks after navigation/deletion (FR-RET-006–010). Browser tests pass for error preservation, pending state, navigation and safe text/links.
- [X] T024 [US2] Run both stories' focused API/PostgreSQL/browser tests plus the existing project/query regression tests; fix only test-backed issues in `backend/researchpilot/`, `backend/tests/` and `frontend/`, then verify all prior results survive injected failures and stale workers cannot commit (FR-RET-001–010). Full non-performance suite: 350 passed, 2 deselected, 1 existing deprecation warning.

## Phase 5: Polish, performance, audit, and acceptance

**Goal**: Verify requirement traceability, security, local performance and user-facing acceptance without any live provider call.

- [X] T025 [P] Add adversarial rendering/URL cases in `backend/tests/test_retrieval_browser.py` and service log/canary cases in `backend/tests/test_retrieval_api.py` for malicious title/abstract/author/link values, unsupported schemes, raw question/query leakage, and absence of any OpenAI call; render all provider text inertly (FR-RET-001/009/010, Constitution I–VI). Hostile markup/URL tests and secret/query log-redaction test pass.
- [X] T026 [P] Add the fake-provider/PostgreSQL reference-host benchmark in `backend/tests/test_retrieval_performance.py` and its protocol in `docs/verification.md`: 100 projects/2,000 stored queries, 250 results over 20 queries, 10 warm-ups, 20 timed searches, nearest-rank p95 and raw samples. Use the plan-approved <2-second p95 target; benchmark must not contact OpenAlex (FR-RET-002/006). Final audited rerun measured p95 207.47 ms (<2,000 ms); raw samples/hashes in `docs/evidence/retrieval-performance.json`; fake provider only.
- [X] T027 Update `.gitlab-ci.yml` to run all repeatable feature 001–003 tests, PostgreSQL, mock-provider/browser, Ruff and JavaScript syntax without OpenAlex/OpenAI credentials or network calls; publish sanitized test results and keep approved-host performance separate (Principle VI). CI explicitly unsets all OpenAI/OpenAlex key/model variables and excludes performance; remote GitLab run remains unavailable while VPN is down.
- [X] T028 Update `README.md`, `specs/003-paper-retrieval/quickstart.md` and `docs/verification.md` with runnable fake-provider journeys, explicit OpenAlex privacy disclosure, no OpenAI/API-key setup, test/performance commands and known limitations; document that live OpenAlex calls require explicit user action (FR-RET-001/006/009). Updated approved gate status, local commands, explicit data disclosure and benchmark protocol/results.
- [X] T029 Add `docs/evidence/retrieval-traceability.md` mapping FR-RET-001–010 and AC-RET-001–006 to actual tests, result artifacts and remaining limits; update `docs/evidence-log.md` with source versions/hashes, prompt status (no prompt change), actual commands/results and no-live-call disclosure (Principle VI). FR mapping and limits recorded; final run evidence is in the post-audit section of `docs/evidence-log.md`.
- [X] T030 Perform an AI/static security and architecture audit of `backend/researchpilot/`, migrations, `frontend/`, `.gitlab-ci.yml` and fixture cleanup: verify no LLM metadata flow, OpenAI request/key, raw query/body logging, unsafe URLs, unauthorized tables, broad test reset or hidden retries; record reviewer/findings/fixes in `docs/evidence-log.md` (Constitution I–VII). Static audit found no vendor imports outside integrations, no `innerHTML`, only migration 003 added, exact disposable-table cleanup, no configured API keys, and HTTPX URL-log leakage fixed by suppressing access-level logs. Details in `docs/evidence-log.md`.
- [X] T031 Run the approved reference-host mock-provider performance protocol; retain raw output under `docs/evidence/` and report separately from live OpenAlex latency (FR-RET-002/006). Final audited run: 20/20 successful searches, 250 records/20 queries each, nearest-rank p95 207.47 ms; raw evidence at `docs/evidence/retrieval-performance.json`.
- [X] T032 After audit fixes, run the entire application suite, migration/restart/rollback/concurrency/browser tests, approved local benchmark, Ruff, formatting, JavaScript syntax, quickstart and secret checks; record exact results in `docs/evidence-log.md`, then request a human keyboard/usability audit in the running app (SC-RET-001–004). Full suite: 358 passed, 1 existing warning; approved-host project/query/retrieval performance tests pass; Ruff/format/new files/JS/diff checks pass. Requesting your hands-on feature-003 review remains T033.
- [ ] T033 Present the implemented feature and evidence for explicit user acceptance in `docs/evidence-log.md`; record known limitations and approval. Do not begin feature 004 or any excluded work without its own approved gates; do not make a live provider smoke call without separate permission.

## Dependencies and checkpoints

```text
Explicit task approval (granted 2026-10-19)
  → T001–003 setup
  → T004–008 foundations
  → US1 tests T009–012 → adapter/service/API/UI T013–016
  → US2 failure/concurrency tests T017–019 → recovery/UI T020–023
  → focused checkpoint T024
  → audit/CI/performance/traceability T025–032
  → human acceptance T033
```

- User Stories 1 and 2 are both P1. US1 is the first independently demonstrable
  increment; US2 depends on the search attempt/persistence path from US1.
- Tests are mandatory and precede their corresponding implementation. Use fakes and
  `MockTransport`; never use production fake modes or live endpoints in CI.
- Shared DB fixtures must clean only explicitly reviewed tables in the disposable DB.
  Destructive database tests remain sequential; independent test authoring may occur
  in parallel after contracts/models are stable.
- Human review, explicit task approval, and explicit user acceptance remain separate
  gates. Plan/spec approval is not implementation authorization.

## Parallel authoring opportunities

- After the foundational schemas are reviewed, T009/T010/T011/T012 author tests in
  different files; run DB-backed tests sequentially against the shared test database.
- After US1 implementation, T017/T018 can be authored independently from T019's
  PostgreSQL barrier tests, subject to shared model/fixture review.
- `[P]` marks file-independent authoring only; no delegation is authorized or implied.

## Implementation strategy

1. Complete setup/foundations and keep the existing 001/002 suite green.
2. Build the no-key, fake-tested OpenAlex adapter and successful retrieval MVP (US1).
3. Add atomic failure preservation and expiring owner safety (US2).
4. Complete audits, performance, traceability and user review; do not add ranking or
   saved references in this feature.

Counts: **33 total**; setup **3**, foundations **5**, US1 **8**, US2 **8**, polish /
cross-cutting **9**. T001–T032 are implemented/verified; T033 awaits user keyboard/
usability review and explicit acceptance.

## Requirement-to-task mapping

| Requirement | Tasks |
|---|---|
| FR-RET-001 | T009–010, T013–016, T025, T028 |
| FR-RET-002 | T004, T009–011, T014, T026, T031 |
| FR-RET-003 | T004–006, T009, T011, T013, T025 |
| FR-RET-004 | T004, T006, T011, T014 |
| FR-RET-005 | T004, T006, T011, T014 |
| FR-RET-006 | T005, T007–008, T010–011, T014–015, T019–020, T022–024, T026–032 |
| FR-RET-007 | T011, T014, T018–020, T024, T032 |
| FR-RET-008 | T005, T007–008, T018–023 |
| FR-RET-009 | T009, T012–016, T025, T028 |
| FR-RET-010 | T012, T016, T023, T025, T030 |
