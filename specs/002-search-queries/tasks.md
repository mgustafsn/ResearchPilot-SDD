# Tasks: User-controlled search queries

**Created**: 2026-10-13 | **Feature**: `002-search-queries` (Git branch: `main`)
**Status**: Draft for human task review. Specification, plan and API/provider
contracts are approved; this task list and implementation are not yet approved.
**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md),
[research.md](research.md), [API contract](contracts/api.md),
[provider contract](contracts/provider.md), and [quickstart.md](quickstart.md).

Tests are mandatory under constitution Principle VI, overriding the generic
template's optional-test wording. Write/review behavioral failures before the
corresponding logic; missing imports, unsafe fixtures, or unavailable infrastructure
are not evidence of missing business behavior. Never call live AI APIs in tests.

Both stories are P1. Implement **US2 manual control first**, then US1 generation,
matching the approved delivery plan and enabling a useful first demo without a key.
All paths below are intended implementation paths, not completed work. Only 002
is authorized for task review: no papers, retrieval/search routes, ranking,
references, jobs/leases, suppression history, or fix to deferred BUG-PRJ-001.

## Phase 1: Setup

**Goal**: Verify authorization and prepare the existing toolchain/configuration.

- [ ] T001 Verify explicit task/implementation authorization plus recorded spec/plan/contract approvals in `docs/evidence-log.md`; recheck Principles I–VII in `specs/002-search-queries/plan.md`, capture current Git/tool state, and stop if task approval is absent. Preserve unrelated work; commit/push verified milestones regularly without force-pushing.
- [ ] T002 Promote existing HTTPX from dev-only to runtime in `pyproject.toml`, update `uv.lock` without adding an SDK/package family, and create only minimal importable contract scaffolds at `backend/researchpilot/query_domain.py`, `backend/researchpilot/query_provider.py`, `backend/researchpilot/query_service.py`, `backend/researchpilot/integrations/__init__.py`, and `backend/researchpilot/integrations/openai_queries.py`; add the minimal test-provider injection signature to `backend/researchpilot/api.py`, configure new test paths and preserve the existing 001 suite. Scaffolds must expose deliberate missing behavior, not implement it; use test-local prompt/context fixtures until the runtime prompt is created.
- [ ] T003 Add blank optional `OPENAI_API_KEY` and pinned `OPENAI_QUERY_MODEL=gpt-4.1-mini-2025-04-14` documentation to `.env.example` and `README.md`; explain explicit question/keyword disclosure and non-zero retention, missing-key manual-only operation, and separate live-smoke permission. Never copy, overwrite, print, or commit values from the user's ignored `.env`.

## Phase 2: Foundational schema, models and fixtures

**Goal**: Shared query invariants and safe durable storage; blocks both stories.

- [ ] T004 Extend `backend/tests/conftest.py` with fake/disabled suggestion-provider injection, barrier helpers, and a real loopback browser server using test-only dependency injection. Preserve local-host/disposable-name/opt-in/distinct-target guards and redacted URLs; explicitly clean only the reviewed feature tables that exist during migration rollout. Adapt `backend/tests/test_project_postgres.py` to reviewed migration versions and pre-failure counts, without weakening safeguards or allowing production fake-provider switches.
- [ ] T005 Write domain tests in `backend/tests/test_queries.py` for whitespace/casefold normalization, 0/1/160/161 lengths, strict booleans/nonnegative integer revisions, extra-field rejection, whole 3–6-unique batch validation, sticky ownership/no-op rules, pure capacity/merge ordering, notice derivation, and exact enabled-stored selection/empty rejection; record failures before T006 (FR-QRY-001–006/008–010).
- [ ] T006 Implement common query input/output/snapshot/batch schemas and pure rules in `backend/researchpilot/query_domain.py`, plus the async `QuerySuggestionProvider` protocol/common safe metadata/errors in `backend/researchpilot/query_provider.py`. Enforce text "Collapse all Unicode whitespace, then validate 1–160 characters", key "Application-computed text.casefold()", enabled "Accept only JSON booleans at API boundary", 3–6 unique normalized suggestions, and actual nonnegative integer expectedRevision values; keep vendor imports and authoritative scholarly fields absent (FR-QRY-001–006/008–010).
- [ ] T007 Write PostgreSQL migration/constraint/revision tests in `backend/tests/test_query_postgres.py` and project compatibility regressions in `backend/tests/test_project_api.py`: initial revisions, repeat migrations/rollback, UUID identity, Unicode key uniqueness, slots/capacity including disabled entries, ownership, cascading isolation, effective/no-op project updates, context restoration, and unchanged project JSON/timestamps/PUT semantics; record failures before T008 (FR-QRY-002–004/007–010).
- [ ] T008 Add `migrations/002_search_queries.sql` and shared reflection in `backend/researchpilot/persistence.py`; extend project update/delete in `backend/researchpilot/service.py` with parent-first locks and revision hooks. Add mutation revision "Nonnegative combined project/query concurrency identity; never decreases", context revision "Nonnegative; advances when validated question/keywords actually change", and generated-context revision "nonnegative when present and ≤ current context revision". Create query identity "Server generated; stable across text/state edits", parent FK "NOT NULL; ON DELETE CASCADE", text bounds 1–160, key `COLLATE "C"`/per-project uniqueness, boolean enabled/default TRUE, origin "CHECK manual/generated; server-owned and never changes on user edits", ownership "Manual origin implies TRUE; sticky TRUE after effective user text/state changes", and slot "CHECK 1–20; UNIQUE(project_id, slot)". Preserve project output fields, existing timestamp behavior and no-op revisions; never edit applied migration 001 or hold locks across provider calls.

## Phase 3: US2 — Control the query list (P1, first demo)

**Goal**: Manually add/edit/delete/toggle saved queries without an AI key or search.

**Independent test**: With a saved project and disabled provider, manage queries,
restart/reopen, exercise normalization/duplicates/capacity/notice behavior, and
verify exact enabled-text selection with fixtures, not a scholarly search route.

- [ ] T009 [P] [US2] Write manual-list/API tests in `backend/tests/test_query_api.py` for coherent QueryListOutput, strict input/types, expectedRevision, default enabled/owned, scoped CRUD, no-op updates, duplicate/capacity/stale conflicts and error precedence, missing-key operation, context notices, and unchanged project timestamps; verify 200/201/422/404/409/503 envelopes before T011–012 (FR-QRY-002–010).
- [ ] T010 [P] [US2] Write PostgreSQL manual-mutation/restart/concurrency tests in `backend/tests/test_query_postgres.py` for ownership restoration, consistent list/revision reads, two same-revision writes, 19/20/21 capacity with disabled rows, lowest-free-slot reuse, context vs noncontext changes, and atomic failure/cross-project deletion; record failures before T011 (FR-QRY-002–004/007–010).
- [ ] T011 [US2] Implement manual list/add/patch/delete and authoritative enabled-query selection in `backend/researchpilot/query_service.py`; lock parent first, compare expected revision before scoped-child work, reject duplicates/capacity without writes, use stable slots/IDs, keep origin server-owned and ownership sticky after effective changes, retain no-op revisions, and increment revisions atomically. Derive the durable notice from context counters; never update project timestamps for query-only changes, substitute the description, or call a provider (FR-QRY-002–010).
- [ ] T012 [US2] Wire approved GET/POST/PATCH/DELETE nested query routes and sanitized error fields/codes in `backend/researchpilot/api.py`; preserve existing project routes/JSON shapes. Support safe explicitly injected disabled/fake providers in tests without consulting real credentials, return generationAvailable without configuration disclosure, and keep project/manual startup usable with missing or invalid provider settings (FR-QRY-002/003/005/007–010).
- [ ] T013 [US2] Write real-server/Chromium manual-query tests in `backend/tests/test_query_browser.py` for labels/focus, add/edit/toggle/delete/reopen, preserved failed input, missing-key controls, capacity errors and durable context notice with zero automatic provider calls; record failures before T014 (FR-QRY-002–005/008–010).
- [ ] T014 [US2] Add manual query list/form/controls and notice to `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`; display origin/ownership/enabled state, use text-only rendering, retain unsaved/failed input, handle current revision/conflicts, and provide keyboard focus/readable messages. Introduce view/project identity checks for these requests without changing the deferred year-number conversion (FR-QRY-002–005/007–010).
- [ ] T015 [US2] Run actual PostgreSQL query/project restart, cascade/rollback, context restoration and default-disabled-provider checks using `backend/tests/test_query_postgres.py`, `backend/tests/test_query_api.py`, and `backend/tests/test_query_browser.py`; prove query-only operations preserve project output/timestamps and no manual action issues an external call (FR-QRY-003–010).
- [ ] T016 [US2] Run the full currently implemented suite, Ruff and JS syntax checks, and demonstrate the manual-query quickstart increment; record actual commands/versions/FR-QRY evidence and failures/fixes in `docs/evidence-log.md`, then commit/push this verified milestone. This first demo is not full 002 acceptance.

## Phase 4: US1 — Review suggestions (P1)

**Goal**: Explicit structured generation with protected user choices and atomic failure.

**Independent test**: With a saved project and fake provider, generate 3–6 validated
suggestions, reload/restart, regenerate around owned queries, and inject provider/
concurrency failures. No live LLM, scholarly provider, or feature 003 route is required.

- [ ] T017 [P] [US1] Write HTTPX mock-transport tests in `backend/tests/test_query_provider.py` for exact fixed endpoint/model/schema/store:false/n:1/stream:false/request context, approved prompt version, missing/invalid config, one attempt/no retries, no tools/history, success/refusal/truncation/bad JSON/count/Unicode/extra fields, optional safe usage, phase vs actual total deadline, pool/oversized-body limits, cancellation and canary-secret logging; record failures before T020 (FR-QRY-001/002/005).
- [ ] T018 [P] [US1] Extend `backend/tests/test_query_api.py` with fake-provider generation tests for GenerateInput/GenerationOutput, caller-context rejection, summary counts, full-batch validation before merge, preserved-key skipping, zero-add/zero-slot success, unavailable/timeout/invalid/stale/storage errors and unchanged complete stored state; record failures before T021–022 (FR-QRY-001/002/004/005/007–010).
- [ ] T019 [US1] Extend `backend/tests/test_query_postgres.py` with controlled barriers for query add/edit/toggle/delete, effective project changes and project deletion during generation, two same-revision generations, cancellation before merge, and failed merge/commit rollback. Verify no lock spans the provider await, first successful commit wins, context acknowledgment/revision changes are atomic even with zero additions, and no resurrection or user-owned eviction occurs; record failures before T021 (FR-QRY-004/005/007–010).
- [ ] T020 [US1] Create the exact approved versioned prompt at `backend/researchpilot/prompts/query_suggestions_v1.txt` and SDK-free adapter at `backend/researchpilot/integrations/openai_queries.py`; use only `gpt-4.1-mini-2025-04-14`, strict schema Chat Completions, store:false, one call/no retries, 512 completion tokens, shared async HTTPX client/two connections, TLS/no redirects/no environment proxies, 64 KiB incremental body limit, and actual 20 s total deadline with 3/2/5/15 s connect/pool/write/read limits. Parse one complete assistant choice with stop/no refusal; validate the whole batch, sanitize failures/metadata, and log no raw inputs/bodies/headers/exceptions. Record exact prompt/hash/version/mock-request evidence in `docs/evidence-log.md` (FR-QRY-001/002/005).
- [ ] T021 [US1] Implement snapshot/await/re-lock/atomic regeneration in `backend/researchpilot/query_service.py`; release the short DB snapshot transaction before await, offload sync DB phases from the event loop, reject missing parent or changed revision, preserve all owned rows unchanged, remove only untouched generated rows, skip duplicates, and fill free slots in batch order up to 20. Atomically acknowledge current context/increment revision even on zero-add success, return after commit, and never reserve a durable job/lease or retry/fallback (FR-QRY-001/002/004/005/007–010).
- [ ] T022 [US1] Compose environment configuration/shared adapter lifecycle and the async POST generation route in `backend/researchpilot/api.py`; keep manual/startup behavior usable with absent/invalid settings, use explicit test-provider injection, close the client at shutdown, return fixed 409/502/503/504 error envelopes/summary counts, and emit only typed model/prompt/status/duration/count/token metadata. No real API key or live smoke call is needed (FR-QRY-001/005/007–009).
- [ ] T023 [US1] Add real-server/fake-provider browser generation tests in `backend/tests/test_query_browser.py` for explicit-call privacy text, pending/status/failure, origin/ownership, edited/toggled preservation, counts/capacity, durable notice outcomes, navigation/edit/deletion while pending, older-revision responses and unsaved-input retention; use deterministic barriers/interception, not production fake modes or real API calls, and record failures before T024 (FR-QRY-001/003–010).
- [ ] T024 [US1] Add explicit Generate/pending/result/error/privacy controls to `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`; disable duplicate Generate clicks but keep manual edits/navigation available. Capture project/view epochs/revisions for all affected callbacks, ignore obsolete responses/errors, refresh saved state on conflict without clearing unsaved text, preserve protected queries and sticky notice semantics, show merge counts, and never repaint another/deleted project. Keep user data text-only and BUG-PRJ-001 unchanged (FR-QRY-001/003–010).
- [ ] T025 [US1] Run generation persistence, complete-state preservation, enabled-text selection, zero-add/capacity, and PostgreSQL concurrency schedules in `backend/tests/test_query_postgres.py` plus `backend/tests/test_query_api.py`; assert no extra outbound calls and no project-contract/timestamp regressions. Scope AC-QRY-004/005 to domain selection fixtures here; actual scholarly integration remains in 003 (FR-QRY-001–010).
- [ ] T026 [US1] Run the full currently implemented unit/API/mock-adapter/PostgreSQL/browser suite, Ruff and JS checks; record passing/failing runs, prompt changes, environments and requirement mappings in `docs/evidence-log.md`, then commit/push the verified generation/UI milestone. Do not represent fake-provider tests as live quality/cost/latency evidence.
- [ ] T027 [US1] Exercise complete `specs/002-search-queries/quickstart.md` automated journeys with a fake provider and a disabled-provider profile, including restart and recovery; record actual outcomes in `docs/evidence-log.md`. Ensure manual controls remain usable after every generation failure, and all suggestion displays are query text—not papers/citations (SC-QRY-001–006).

## Phase 5: Verification, audits and acceptance

**Goal**: Verify both stories and existing 001 behavior; obtain real human acceptance.

- [ ] T028 Expand fault/security regressions in `backend/tests/test_query_provider.py`, `backend/tests/test_query_api.py`, and `backend/tests/test_query_postgres.py`: repeated invalid/timeout/commit failures, no partial writes/revision/notice changes, safe retry only on later explicit action, missing secrets, malicious context/data and no vendor imports in business logic. Write failing regressions before necessary fixes; never weaken source/secret tests or mask recorded failures (FR-QRY-001/005/007–009, constitution I–VI).
- [ ] T029 Add browser safety/regression schedules in `backend/tests/test_query_browser.py` for hostile text, keyboard/focus/error labels, duplicate-click prevention, slow old responses after navigation/new-project/edit/deletion, and simultaneous manual work. Verify no unsaved-input loss or stale repaint and no automatic provider call on load/context change; fix only regression-backed 002 issues (FR-QRY-003–005/007/009).
- [ ] T030 Implement/run `backend/tests/test_query_performance.py` on the approved reference host using real PostgreSQL/loopback HTTP, 100 projects/1,999 query rows, one target at 19 entries, 10 untimed reads, and 20 add/list/edit/toggle/delete cycles. Retain 100 successful raw samples/statuses, nearest-rank p95 below 500 ms, revision bookkeeping outside timing, and source/host/version evidence exactly as `docs/verification.md` specifies. Rerun existing project performance separately; do not use paid AI timing as this acceptance result.
- [ ] T031 Update `.github/workflows/ci.yml` to run all old/new repeatable tests with PostgreSQL/fake providers/mock HTTP, Ruff and JS syntax, without real keys or external model calls; keep reference-host timing separate and publish sanitized test artifacts. Update runnable commands and manual-only/provider configuration in `README.md` and `specs/002-search-queries/quickstart.md`; verify production dependencies include HTTPX without dev packages.
- [ ] T032 Perform an AI/static secret, rendering, privacy, interface, lock/revision and dependency audit; record reviewer identity, findings/fixes/regression evidence and limitations in `docs/evidence-log.md`. Check no authoritative scholarly metadata path, raw provider body/key/context logging, production fake mode, unauthorized schema, hidden retry, unsafe fixture cleanup, or accidental BUG-PRJ-001 fix (constitution I–VII).
- [ ] T033 Obtain and record a human keyboard/usability review of both manual and fake-provider journeys in `docs/evidence-log.md`, including labels/focus, failed-input retention, enabled/ownership meaning, refresh notices, conflicts, deletion and privacy disclosure. Record the actual reviewer/browser/findings; do not claim an automated browser run is a human audit or that unresolved 001 evidence was supplied.
- [ ] T034 After audit fixes, run the entire application suite, PostgreSQL migration/restart/rollback/concurrency checks, approved-host query and project performance protocols, lint/syntax and quickstart; record exact commands, versions, commit/dirty state, raw sanitized outputs, prompt evidence and failures/fixes in `docs/evidence-log.md`. Preserve older 001 snapshots as historical evidence; do not rewrite them as new verification (SC-QRY-001–006).
- [ ] T035 Add actual query FR-QRY-001–010 test/evidence mappings and remaining limitations to `docs/evidence/query-traceability.md`; link genuine test/timing/CI artifacts from `docs/evidence-log.md` and update `README.md` with evidence-supported status. Respect reviewer-owned/read-only checklist rules; never mark a compliance/audit/acceptance item passed without its actual evidence.
- [ ] T036 Present the working feature and evidence for explicit user acceptance in `docs/evidence-log.md`; record known limitations/deferred issues and update `README.md` truthfully. Do not mark acceptance complete or begin feature 003 planning/implementation without that decision; no live provider smoke test is implied.

## Dependencies and checkpoints

```text
Explicit task/implementation approval
  → Setup T001–003
  → Foundations T004–008
  → US2 tests T009–010 → service/API T011–012
  → US2 browser tests T013 → UI T014 → restart/checkpoint T015–016
  → US1 tests T017–019 → adapter/service/API T020–022
  → US1 browser tests T023 → UI T024 → verification/checkpoint T025–027
  → Audit/performance/CI T028–033 → final verification/evidence T034–035
  → human acceptance T036
```

- No implementation task starts before explicit authorization. Spec/plan approvals
  and this draft task-generation request do not authorize implementation.
- Shared foundational models/schema serve both stories. US2 is independently
  useful with generation disabled; US1 tests use saved fixtures/fakes and require
  the storage/ownership/revision invariants delivered by US2.
- All new behavioral tests precede corresponding logic. Complete the full available
  suite before declaring any task complete; expected red-phase failures remain
  recorded failures, not green results. Stop and investigate unsafe setup failures.
- Existing project-service/migration/fixture/frontend files are shared; edit them
  sequentially. Never run destructive DB fixtures concurrently against one target.
- T030 requires the approved reference host and protocol. T034 follows actual audit
  fixes and T033 human evidence; T036 follows verification. No fabricated manual
  evidence, independent reproduction, model quality, or zero-retention claim.
- Push milestones after current tests/security/diff checks; report GitHub failure
  truthfully and retry safely, not via force push or discarding unfamiliar work.

## Parallel authoring opportunities

- After T008: T009 API tests and T010 PostgreSQL tests can be authored in parallel
  in separate files. Their reviews precede T011–012.
- After T016: T017 adapter tests and T018 API tests can be authored in parallel;
  T019 follows to avoid conflicting writes to shared test files/fixtures.
- `[P]` denotes independent authoring, not permission to delegate without a request,
  invoke paid services, or parallelize DB cleanup. Default execution is sequential.

## Implementation strategy

First demo: manual query management (US2), needing no API key. Then complete
structured generation/protected regeneration (US1), followed by all final checks.
Both stories are necessary for full 002 acceptance; neither creates feature 003.

Counts: **36 total**; setup **3**, foundations **5**, US2 **8**, US1 **11**, final
verification/audits/acceptance **9**. All tasks remain unchecked/unstarted.

## Requirement-to-task mapping

| Requirement | Tasks |
|---|---|
| FR-QRY-001 | T005–006, T017–024, T025–028 |
| FR-QRY-002 | T005–012, T015, T017–021, T025 |
| FR-QRY-003 | T005–006, T009–016, T023–024, T029, T033 |
| FR-QRY-004 | T005–011, T013–015, T018–021, T023–029 |
| FR-QRY-005 | T003–006, T009, T012–017, T018–024, T026–029 |
| FR-QRY-006 | T005–006, T011, T025, T027 |
| FR-QRY-007 | T004–016, T018–019, T021–025, T028–029 |
| FR-QRY-008 | T005–015, T018–021, T025, T030 |
| FR-QRY-009 | T005–015, T018–025, T028–029, T033 |
| FR-QRY-010 | T005–015, T018–019, T021, T023–025, T033 |

Requirement IDs and original US1/US2 labels are unchanged. Record exact prompts,
audits, test commands/results, consent/approval decisions, and commits prospectively;
this checklist is a work proposal, not evidence that application tests ran.
