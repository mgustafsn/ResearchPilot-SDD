# Tasks: Research-project management

**Status**: Approved by the user on 2026-10-12 (reply: "approve tasks and start project management. Remember to commit and push to github regularly").
Implementation of feature 001 is in progress. The user confirmed proceeding with
unchecked checklist items on 2026-10-12 (reply: "yes"); actual acceptance remains pending.
**Input**: spec.md, plan.md, research.md, data-model.md, contracts/api.md.
Tests are mandatory under constitution Principle VI, regardless of optional-test
wording in the installed template. Write and review failing behavior tests before
the corresponding implementation; record failure and passing evidence truthfully.
Paths below are intended implementation paths, not existing files. Do not build
queries, retrieval, ranking, references, future tables, accounts, or provider SDKs.

## Phase 1: Setup

**Goal**: Confirm authorization and establish the reviewed local toolchain only.

- [X] T001 Verify constitution, specification, plan/API contract, and explicit task approval in `docs/evidence-log.md`; recheck Principles I–VII in `specs/001-project-management/plan.md`, record the baseline Git state and observed tools, and stop if task approval is missing. Later slices remain unapproved.
- [X] T002 Initialize `pyproject.toml`, generate a new `uv.lock`, preserve existing `.gitignore` rules, and create `backend/researchpilot/__init__.py` and the approved test/frontend layout; include only the plan's justified runtime/dev dependencies, pytest/Playwright configuration, Ruff configuration, and backend import configuration.
- [X] T003 Add credential-free `.env.example`, PostgreSQL 17 service `db` and durable volume in `compose.yaml`, and `scripts/start-local.sh`; read environment configuration without printing credentials, bind HTTP to `127.0.0.1:8000` and any exposed database port to loopback, run migrations before serving, and document setup/prerequisites in `README.md`. Do not connect to the original database.

## Phase 2: Foundational prerequisites

**Goal**: Safe isolated fixtures and versioned durable storage. Blocks both stories.

- [X] T004 Add isolated unit/API fixtures and real-server browser/PostgreSQL fixtures in `backend/tests/conftest.py`; require `TEST_DATABASE_URL` database name `researchpilot_sdd_test`, `ALLOW_TEST_DATABASE_RESET=1`, and a target distinct from `DATABASE_URL` before any test cleanup. Add refusal tests in `backend/tests/test_project_postgres.py` for missing opt-in, wrong name, and equivalent application target; never log URLs/credentials. Optional SQLite tests cannot replace PostgreSQL checks.
- [X] T005 Write migration, version tracking, repeat-startup preservation, rollback, connection disposal/recreation, and basic database constraint tests in `backend/tests/test_project_postgres.py` before storage implementation; record expected behavioral failures in `docs/evidence-log.md` (FR-PRJ-002–006/007, SC-PRJ-003).
- [X] T006 Create only the Project table in `migrations/001_projects.sql` and SQLAlchemy/database lifecycle in `backend/researchpilot/persistence.py`; identity is "Server generated; stable across edits" and timestamps are "Server owned; createdAt unchanged on update". Use PostgreSQL UUID, timezone-aware timestamps, JSON keywords, nullable years, required count, database length/range/year-order checks, applied migration versions, and transactional rollback. Wire migration startup to `scripts/start-local.sh` without clearing application data; pass T004–005 checks.

## Phase 3: US1 — Create and reopen a project (P1)

**Goal**: Create, list, and reopen persisted project settings with clear validation.

**Independent test**: Start empty, create through the browser, restart the application
and reconnect to actual PostgreSQL, and reopen identical values (AC-PRJ-001–004).

- [X] T007 [P] [US1] Write boundary/normalization tests in `backend/tests/test_projects.py` for FR-PRJ-002–005/007: name "Trimmed, 1–200 characters", question "Trimmed, 1–5000 characters", keywords "At most 30 inputs; trim, validate length 1–100, case-fold deduplicate", years "1–9999, start ≤ end if both supplied", count "1–250, required input". Include omitted keywords/years, first spelling/order, whitespace-only and extra fields, noninteger strings/floats/booleans, and exact inside/outside boundaries; record behavioral failures before T009.
- [X] T008 [P] [US1] Write create/list/read API contract tests in `backend/tests/test_project_api.py` for FR-PRJ-001/006/007: 201/200 results, empty list, 422 field errors/invalid UUID, 404 unknown IDs, 503 sanitized storage errors, camelCase response shape, UTC timestamps, duplicate names, and newest-update/ascending-UUID order. Record expected failures before T010.
- [X] T009 [US1] Implement ProjectInput/ProjectOutput validation in `backend/researchpilot/domain.py`: title "Trimmed, 1–200 characters", researchQuestion "Trimmed, 1–5000 characters", keywords "At most 30 inputs; trim, validate length 1–100, case-fold deduplicate", years "1–9999, start ≤ end if both supplied", count "1–250, required input"; default omitted keywords to [] and years to null, reject extra keys/coercible numeric types, retain first keyword spelling/order, and keep ID/timestamps server-owned (FR-PRJ-002–007).
- [X] T010 [US1] Implement transactional create/list/read operations in `backend/researchpilot/service.py` and JSON/static routes in `backend/researchpilot/api.py`; return the approved error envelope, commit before success, sanitize browser responses and logs, bind configuration from the environment, and serve the UI/API together without permissive CORS (FR-PRJ-001/006/007, NFR-PRJ-001).
- [X] T011 [US1] Write real-server/isolated-PostgreSQL browser tests in `backend/tests/test_project_browser.py` for empty/create/detail journeys, labeled keyboard controls, default count 100, readable validation/storage errors, and retained form input after failed saves; record failures before T012 (AC-PRJ-001–004, FR-PRJ-005/007, NFR-PRJ-002).
- [X] T012 [US1] Implement project list/create/detail UI in `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`; display `title` as "Project name", label all fields, offer count 100 initially, retain invalid form values, expose errors as text, and render all user input as text rather than HTML (FR-PRJ-001/005/007, NFR-PRJ-001/002).
- [X] T013 [US1] Extend and run `backend/tests/test_project_postgres.py` with API-created project persistence across application shutdown/recreation and fresh PostgreSQL connections, stable IDs/UTC timestamps, duplicate titles, ordering ties, migration reruns, and unchanged values after rejected writes (FR-PRJ-006/007, AC-PRJ-003, SC-PRJ-003).
- [X] T014 [US1] Run the full currently implemented unit/API/browser/PostgreSQL suite and the US1 quickstart journey; record commands, environment, requirement IDs, failures/fixes, and actual results in `docs/evidence-log.md`. Stop at this create/reopen checkpoint before extending the story (SC-PRJ-001–003); this is not full-feature acceptance.

## Phase 4: US2 — Edit and delete a project (P2)

**Goal**: Safely change project settings and permanently delete selected projects.

**Independent test**: Using an existing project fixture, edit/reload, cancel deletion,
then confirm deletion and restart. Another project remains unchanged (AC-PRJ-005–007).

- [X] T015 [P] [US2] Extend `backend/tests/test_project_api.py` with full PUT/DELETE contract tests for stable ID/createdAt, advanced updatedAt, normalization, 422/404/503, transactional rollback, deletion 204 with no body, and cross-project isolation; record expected failures before T017 (FR-PRJ-001/006–008, AC-PRJ-005–007).
- [X] T016 [P] [US2] Extend `backend/tests/test_project_browser.py` with edit/reopen, retained input after failed update, explicit permanent-deletion warning/no undo, cancellation sending no DELETE, and confirmed deletion; record expected failures before T018 (FR-PRJ-007/008, AC-PRJ-005/006, NFR-PRJ-002).
- [X] T017 [US2] Implement transactional full update/delete in `backend/researchpilot/service.py` and `backend/researchpilot/api.py`; preserve ID/createdAt, reject invalid changes without modifying stored values, update updatedAt on success, return approved not-found/storage errors, and delete only the selected project. Do not add future-owned tables or search locks (FR-PRJ-001/006–008).
- [X] T018 [US2] Add edit and delete controls in `frontend/app.js` with supporting labels/styles in `frontend/index.html` and `frontend/styles.css`; retain failed edits, require the permanent-deletion/no-undo warning, cancel without a DELETE request, and preserve keyboard access and text errors (FR-PRJ-007/008, NFR-PRJ-002).
- [X] T019 [US2] Extend `backend/tests/test_project_postgres.py` to verify updates/deletion across restart/reconnect, unchanged other projects, and unchanged stored data after injected failed update/delete; run all currently implemented tests and record actual evidence in `docs/evidence-log.md` (FR-PRJ-006–008, AC-PRJ-005–007).

## Phase 5: Verification and cross-cutting concerns

**Goal**: Verify both stories, audit safety/usability, and obtain feature acceptance.

- [X] T020 Expand fault-injection regressions in `backend/tests/test_project_api.py` and `backend/tests/test_project_postgres.py` for failed reads/writes/commit and migration startup, sanitized errors/logs, no partial writes, and safe retry; write failing regressions before any necessary fixes in `backend/researchpilot/persistence.py`, `backend/researchpilot/service.py`, or `backend/researchpilot/api.py` (FR-PRJ-007, NFR-PRJ-001).
- [X] T021 Implement and run `backend/tests/test_project_performance.py` on the approved host with real loopback HTTP/PostgreSQL, 100 seeded projects, 10 untimed warm-up reads, 20 POST/list/detail/PUT/DELETE cycles, 100 raw timing samples, no omitted failures, nearest-rank p95 below 500 ms, and per-operation/environment reporting exactly as `docs/verification.md` specifies (NFR-PRJ-003).
- [X] T022 Add canary-secret/error-log/API/asset tests in `backend/tests/test_project_api.py` and malicious-text rendering/keyboard/error-label regressions in `backend/tests/test_project_browser.py`; write regressions before fixes, verify no credentials/SQL/raw exception content escapes, and keep provider SDKs/LLM metadata paths absent (NFR-PRJ-001/002).
- [X] T023 Add `.github/workflows/ci.yml` for unit/API/browser tests, disposable PostgreSQL 17 tests, Ruff, and `node --check frontend/app.js`; configure safe test opt-in without application secrets and treat approved-host latency acceptance separately. Update actual runnable commands in `README.md` and `specs/001-project-management/quickstart.md`.
- [ ] T024 Perform and record secret/rendering/dependency-boundary and human keyboard audits in `docs/evidence-log.md`; exercise labels, focus, error text, retained forms, and deletion confirmation, recording reviewer identity, findings, remaining limitations, and regression-backed fixes (NFR-PRJ-001/002).
- [ ] T025 Run the full application suite, PostgreSQL migration/restart/fault tests, approved-host performance fixture, Ruff, JS syntax check, and complete quickstart; record exact commands, tool/host versions, working-tree/commit identifiers where available, outputs, failed runs and fixes in `docs/evidence-log.md`, and update only evidence-supported gates in `specs/001-project-management/checklists/requirements.md` (SC-PRJ-001–004).
- [ ] T026 Present the working feature and recorded evidence for explicit human acceptance in `docs/evidence-log.md`; update `README.md` with truthful status and do not begin planning or implementation of feature 002 until this sign-off. Do not mark acceptance complete without the user's approval.

## Dependencies and checkpoints

```text
Task approval + unchecked-checklist confirmation → Setup T001–003 → Foundations T004–006
  → US1 tests T007–008 → domain T009 → API T010
  → browser tests T011 → UI T012 → persistence/checkpoint T013–014
  → US2 tests T015–016 → API T017 → UI T018 → persistence/checkpoint T019
  → Verification T020–025 → human acceptance T026
```

- Missing task approval stops all implementation. Review authorization is not approval.
- US2 requires US1's working persistence/API; its acceptance test uses an existing
  project fixture rather than depending on the create journey in the same test.
- Review failing tests before corresponding logic; failures must expose missing
  behavior, not just missing dependencies or an unsafe/unconfigured database.
- Run the full available suite before marking a task complete. Adding a test task
  does not turn expected red-phase failures into passing application evidence.
- T021 requires the approved reference host; CI on different hardware cannot satisfy
  NFR-PRJ-003. T025 depends on T020–024. Human audit/acceptance cannot be fabricated.
- Later-owned data deletion is covered when those slices add their reviewed schemas;
  implementing their tables, search locks, or provider interfaces now is excluded.

## Parallel opportunities

- US1: after T006, T007 validation tests and T008 API tests may be authored in
  parallel; they touch different files. Both must be reviewed before implementation.
- US2: after T014, T015 API tests and T016 browser tests may be authored in parallel;
  T017/T018 wait for their corresponding test reviews.
- These are authoring opportunities, not permission to run destructive test fixtures
  concurrently against one test database or to spawn delegated agents. Execution is
  sequential by default; shared application modules and fixtures are not parallel work.

## Implementation strategy and requirement coverage

Deliver the create/reopen increment first (US1: 8 tasks), then editing/deletion
(US2: 5 tasks). The suggested first demo is US1, but it does not replace full 001
acceptance. Setup/foundations: 6 tasks; cross-cutting verification: 7 tasks;
total: 26. All task IDs were resequenced from the prior 21-task draft; none had been
implemented or completed. Requirements and acceptance IDs remain unchanged.

| Requirement | Task coverage |
|---|---|
| FR-PRJ-001 | T008, T010–012, T015–019 |
| FR-PRJ-002 | T005–007, T009 |
| FR-PRJ-003 | T007, T009 |
| FR-PRJ-004 | T005–007, T009 |
| FR-PRJ-005 | T005–007, T009, T011–012 |
| FR-PRJ-006 | T005–006, T008–010, T013, T015, T017, T019 |
| FR-PRJ-007 | T005–013, T015–020 |
| FR-PRJ-008 | T015–019, T024 |
| NFR-PRJ-001 | T003–004, T010, T012, T020, T022–025 |
| NFR-PRJ-002 | T011–012, T016, T018, T022, T024–025 |
| NFR-PRJ-003 | T021, T025 |

At each checkpoint record requirement IDs, prompt changes, audit findings, and actual
test evidence in `docs/evidence-log.md`. No dependency installation, implementation,
benchmark, CI execution, or application test result is implied by this task review.
