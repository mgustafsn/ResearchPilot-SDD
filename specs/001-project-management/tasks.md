# Tasks: Research-project management

**Status**: Draft; all work unstarted. Blocked by constitution/specification approval.
**Input**: spec.md, plan.md, research.md, data-model.md, contracts/api.md.
Tests are mandatory. Tasks use exact intended paths; no unchecked task is evidence
of implementation. Do not run later-feature tasks while implementing this slice.

## Phase 1: Review and setup

- [ ] T001 Resolve `docs/constitution-amendment.md`, approve `docs/scope.md` and this specification; record decision/approver in `docs/evidence-log.md`.
- [ ] T002 Approve `plan.md`, `contracts/api.md`, and reference environment for NFR-PRJ-003; rerun Constitution Check.
- [ ] T003 Initialize `pyproject.toml`, `uv.lock`, `.gitignore`, and backend/frontend test layout per plan with necessary dependencies only.
- [ ] T004 Add credential-free `.env.example`, local `compose.yaml`, and `scripts/start-local.sh`; bind to loopback and document startup in `README.md`.
- [ ] T005 Add `backend/tests/conftest.py` with isolated storage and explicit disposable PostgreSQL configuration safeguards.

## Phase 2: US1 — create and reopen (P1)

- [ ] T006 [US1] Write boundary/normalization tests in `backend/tests/test_projects.py` for FR-PRJ-002–005, including strict integer and unknown-key cases; record expected failures before implementation.
- [ ] T007 [US1] Write API tests in `backend/tests/test_project_api.py` for creation/list/read, errors, timestamps, and ordering (FR-PRJ-001/006/007).
- [ ] T008 [US1] Implement validated project schemas in `backend/researchpilot/domain.py`.
- [ ] T009 [US1] Create `migrations/001_projects.sql` and transaction/database lifecycle in `backend/researchpilot/persistence.py`.
- [ ] T010 [US1] Implement create/list/read services in `backend/researchpilot/service.py` and HTTP/static routes in `backend/researchpilot/api.py`.
- [ ] T011 [US1] Write create/reopen/validation browser tests in `backend/tests/test_project_browser.py` (AC-PRJ-001–004).
- [ ] T012 [US1] Implement labeled keyboard-accessible project list/create/detail UI in `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`; render user input as text.
- [ ] T013 [US1] Verify PostgreSQL migration and reconnect persistence in `backend/tests/test_project_postgres.py` (AC-PRJ-003, SC-PRJ-003).

## Phase 3: US2 — edit and delete (P2)

- [ ] T014 [US2] Extend `backend/tests/test_project_api.py` with update/delete/not-found, validation rollback and cross-project isolation tests (AC-PRJ-005–007).
- [ ] T015 [US2] Implement transactional update/delete in `backend/researchpilot/service.py` and `backend/researchpilot/api.py`.
- [ ] T016 [US2] Extend `backend/tests/test_project_browser.py` for editing, canceled deletion and confirmed deletion; add UI controls in `frontend/app.js`.

## Phase 4: Verification and evidence

- [ ] T017 Inject storage failure and assert sanitized errors/no partial writes in `backend/tests/test_project_api.py` and `backend/tests/test_project_postgres.py`.
- [ ] T018 Add controlled latency measurement in `backend/tests/test_project_performance.py` using the approved NFR-PRJ-003 environment and 100-project fixture.
- [ ] T019 Audit secrets/rendering and keyboard operation; record actual findings and fixes in `docs/evidence-log.md` (NFR-PRJ-001/002).
- [ ] T020 Add `.github/workflows/ci.yml` for unit/API/browser tests, disposable PostgreSQL tests, Ruff and JS syntax checks; update validation commands in `README.md`.
- [ ] T021 Run all relevant tests, link outputs and commit IDs in `docs/evidence-log.md`, and update `checklists/requirements.md`; obtain acceptance sign-off before planning 002.

## Dependencies and checkpoints

T001–002 block implementation. T003–005 precede tests. Review failing tests before
production logic; failures must demonstrate missing behavior, not just broken setup.
T008–010 precede UI integration. US2 requires US1 CRUD foundations. All phase-4 checks
must pass before completion. No tasks are marked parallel because several share files.
At each checkpoint, record prompt revisions and defects, not only successful outputs.
