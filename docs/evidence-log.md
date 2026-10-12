# Evidence log

## Artifact preparation — 2026-10-11

- User request (verbatim): "okay. can you create the SDD stuff from the current vibecoded version?"
- Prior steering: use a smaller subset; select GitHub Spec Kit; preserve course-report template.
- Agent: OpenCode; session-reported model `openai/gpt-6.1-sol`.
- Activity: inspect source documentation/domain rules and installed templates; derive
  five draft specs and first-slice plan/tasks/contracts; propose constitution amendment.
- This is direct artifact preparation, not recorded execution of Spec Kit commands.
- Existing constitution and original implementation were not modified.
- No runtime app or tests exist in this rebuild yet; no implementation outcome recorded.
- Installed Spec Kit version, baseline dirty-state audit, team identity and approval: pending.

### Documentation consistency check

Ran a Python check over 19 Markdown files: local Markdown links resolved, all five
specifications contained the required scenario/requirement/success/assumption headings,
43 requirement IDs were unique, and `.specify/feature.json` resolved to an existing spec.
Result: PASS. This checks artifact structure only, not semantic completeness or runtime
correctness. Application tests were not runnable because no implementation exists.

## Repository setup and SDD continuation — 2026-10-11

- User request (verbatim): "We have setup the SDD. Now setup the github repo, private repo mind you, then start continue working on the SDD"
- Initialized this rebuild as a Git repository on `main`; original repository untouched.
- Target GitHub repository: `mgustafsn/ResearchPilot-SDD`, explicitly private.
- Created and pushed the initial commit `0ef298b`. `gh repo view` confirmed
  `visibility: PRIVATE`, `isPrivate: true`, and default branch `main`.
- Added root ignore rules for local environment files, credentials, and runtime artifacts.
- Pre-publication scan of 50 staged files for common credential/private-key patterns:
  PASS, no matches. This limited pattern scan is not a comprehensive security audit.
- Began `speckit-clarify` for active feature 001. Constitution amendment and feature
  approval remain pending; this request is not recorded as their ratification.
- Ran `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` successfully;
  it resolved `specs/001-project-management/spec.md`. `.specify/feature.json` remains
  deliberately machine-local under the installed Spec Kit ignore rules.
- No application tests executed: this checkout still contains planning artifacts only.

## Decision log

| Date | Decision/proposal | Approver | Status | Affected artifacts |
|---|---|---|---|---|
| 2026-10-11 | Constitution amendment 1.0.0 → 2.0.0 for reduced scope | User, reply "a", as recorded in constitution 2.0.0 | Ratified; dependent drafts require re-review | .specify/memory/constitution.md; docs/constitution-amendment.md; dependent drafts |
| 2026-10-12 | Five-slice discovery MVP and listed exclusions | User, reply "A" to scope walkthrough | Feature boundaries approved; product decisions and individual review gates pending | docs/scope.md; specs/001–005 |
| 2026-10-12 | Required project name/question; optional keywords/year bounds; paper limit 1–250, UI default 100 | User, reply "A" to project-fields walkthrough | Field choices approved; remaining validation, specification, and implementation gates pending | specs/001-project-management/spec.md; docs/scope.md |
| 2026-10-12 | Permanent project deletion and owned-data removal after an explicit warning/confirmation; no undo; other projects and original application untouched | User, reply "A" to deletion walkthrough | Deletion behavior approved; specification and implementation gates pending | specs/001-project-management/spec.md |
| 2026-10-12 | Proposed project validation limits, normalization, duplicate names, readable errors, preserved form input, and unchanged stored data on invalid input | User, reply "A" to validation walkthrough | Validation behavior approved; specification and implementation gates pending | specs/001-project-management/spec.md |
| 2026-10-12 | Current Linux reference host; local CRUD p95 below 500 ms, 100 requests, 100 stored projects, excluding startup/external services | User, reply "A" to performance walkthrough | Host and target approved; no performance measurement executed | specs/001-project-management/spec.md; docs/verification.md |
| 2026-10-12 | Project-management specification as a whole | User, reply "approve project specification." | Specification approved; plan, contracts, tasks, and implementation not approved | specs/001-project-management/spec.md |

## Project-management clarification — 2026-10-12

- User request: "Walk me through these decisions". Used `speckit-clarify` to guide
  five sequential decisions; the user answered "A" to each. Exact questions and
  accepted answers are retained in the active specification's Clarifications section.
- Product decisions do not approve the whole specification, plan, contract, tasks,
  or implementation. No application code or dependencies were added.
- Inspected reference host using `lscpu`, `uname -srmo`, and `free -h`:
  AMD Ryzen 7 5700X3D, 8 cores/16 threads, 31 GiB reported RAM,
  Linux 7.2.9-2-cachyos x86_64. This is an environment inventory, not a benchmark.
- Re-reviewed the specification quality checklist: 5/10 → 8/10 items passing;
  newly passing items cover count/deletion approval, performance host/budget approval,
  and constitution ratification (recorded in constitution 2.0.0 on 2026-10-11).
  Specification/design/tasks approval and reviewed test mapping/acceptance evidence
  remain unchecked. Dependent planning drafts still require constitution re-review.
- No application tests executed: no implemented application or test suite exists yet.
- Documentation-only Python assertions passed: exactly five clarification answers,
  checklist 8/10, and no duplicate level-two headings in the active specification
  or verification strategy. This is not application verification.

## Project-management specification approval — 2026-10-12

- User approval (verbatim): "approve project specification."
- Marked `specs/001-project-management/spec.md` approved without changing its
  requirements. No approval is inferred for the plan, contracts, tasks, later
  features, or implementation. The combined specification/design/task checklist
  gate remains unchecked until all its parts have been reviewed and approved.
- No application tests run: this is an approval-record update, not implementation
  or verification evidence.

## Project-management plan review preparation — 2026-10-12

- User request (verbatim): "OK lets review". This authorizes review preparation,
  not approval of the plan/contract/task list or implementation.
- Used the installed `speckit-plan` workflow. Ran
  `.specify/scripts/bash/setup-plan.sh --json`: PASS; existing plan preserved.
  It resolved feature identifier `001-project-management`; the actual Git branch
  remains `main`. No branch was created. No extension hooks were configured.
- Reviewed constitution 2.0.0, approved 001 specification, scope, plan template,
  and existing design artifacts. Updated `plan.md`, `research.md`, `data-model.md`,
  `contracts/api.md`, and `quickstart.md` in `specs/001-project-management/`.
  This is repository-based design review, not external research or experimentation.
- Proposed runtime dependencies each have a stated purpose: FastAPI, SQLAlchemy,
  psycopg, and uvicorn. Tests use pytest, HTTPX, pytest-playwright/Chromium and Ruff;
  no frontend framework, provider SDK, or dependency installation was added.
- Added proposed mappings for FR-PRJ-001–008 and NFR-PRJ-001–003 and a reproducible
  real-HTTP/PostgreSQL timing protocol. None represents executed acceptance evidence.
- AUD-PLAN-001: stale constitution blockers in planning and governance documentation
  corrected from the recorded ratification. Later-slice reviews remain pending.
- AUD-PLAN-002 (FR-PRJ-007/008): propagated retained form input and the permanent
  deletion warning/no-undo decision into the API/UI contract, model, and plan.
- AUD-PLAN-003 (NFR-PRJ-003): replaced unspecified timing method with a proposed
  100-request balanced CRUD workload, 10 warm-up reads, real PostgreSQL/loopback HTTP,
  nearest-rank p95, raw samples, and required environment evidence. Plan approval
  must cover this protocol; no benchmark was run.
- Pre/post-design constitution assessment: Principles I–VII compatible at design
  level, with PostgreSQL, secrets, local deployment and testing requirements retained.
  This is not human approval or proof of runtime compliance.
- Task list updated only to correct gate status; all 21 tasks remain unchecked and
  need reconciliation/review after plan approval. Checklist remains 8/10: combined
  specification/design/task approval and test mapping/acceptance evidence pending.
- No application tests run: there is still no implemented application/test suite.
- Documentation validation: Python assertions PASS across 18 Markdown files for
  local links and duplicate section headings, all 11 project requirement mappings,
  five retained clarification answers, checklist 8/10, and 21 unchecked tasks.
  `git diff --check`: PASS (no output). `git branch --show-current`: `main`.
  These checks do not establish application correctness or performance acceptance.

## Project-management plan and API contract approval — 2026-10-12

- User approval (verbatim): "approve plan and API contract".
- Recorded approval in `specs/001-project-management/plan.md` and
  `contracts/api.md`, including the plan's supporting design and performance
  protocol. Updated current gate descriptions without changing approved requirements.
- Task reconciliation and separate task-ordering approval remain pending. All
  implementation tasks remain unchecked. The combined specification/design/task
  checklist gate remains unchecked until task approval; no implementation permission,
  later-slice approval, or acceptance is inferred from this decision.
- No application tests run: this is approval documentation only.

## Project-management task review — 2026-10-12

- User request (verbatim): "Yes review". This is task-review authorization, not
  task approval or permission to begin implementation.
- Used `speckit-tasks`; ran `.specify/scripts/bash/setup-tasks.sh --json`
  successfully. Required spec/plan and rationale/model/contract/quickstart resolved
  under `specs/001-project-management/`. No extension hooks were configured.
- Re-reviewed the task draft against approved 001 requirements, plan/API contract,
  and constitution 2.0.0. Updated `specs/001-project-management/tasks.md` from 21
  unchecked draft tasks to 26 unchecked reconciled tasks; no implemented/completed
  task IDs were changed. Requirement/acceptance IDs are unchanged.
- Breakdown: 3 setup, 3 foundational, 8 US1 create/reopen, 5 US2 edit/delete, and
  7 verification/acceptance tasks. Suggested first demo remains US1 only; complete
  feature acceptance still requires both stories and all cross-cutting evidence.
- AUD-TASK-001 (Principle VI): moved migration/database tests before storage logic
  and separated US2 browser test authoring from UI implementation. Red-phase failures
  must demonstrate missing behavior, not broken setup. Full-suite passing evidence
  is still required before declaring implementation tasks complete.
- AUD-TASK-002 (FR-PRJ-002–008): made normalization/boundaries, server-owned fields,
  permanent deletion warning/no undo, retained failed edits, and cross-project
  isolation explicit in tasks; mapped all 11 FR/NFR requirement IDs to task IDs.
- AUD-TASK-003 (NFR-PRJ-001–003): made safe disposable-DB opt-in/name/target checks,
  loopback/configuration, versioned migrations, secret/rendering/keyboard checks,
  and the approved real-HTTP/PostgreSQL performance protocol explicit.
- Optional parallel authoring pairs: T007/T008 (US1) and T015/T016 (US2), each
  after its prerequisites. No delegation was used; shared test-database execution
  remains sequential. No query/retrieval/ranking/reference schema was introduced.
- Human task approval and actual application acceptance remain pending. Checklist
  remains 8/10; no application tests, CI jobs, benchmarks, or installation ran.
- Documentation-only Python assertions: PASS for 26 sequential unchecked task IDs,
  checklist format/file paths, US1=8 and US2=5, four parallel-authoring markers,
  all 11 requirement mappings, and headings/local links across 18 Markdown files.
  `git diff --check`: PASS (no output). No configured after-tasks hooks found.
  These checks do not verify application behavior or satisfy acceptance criteria.

## Task approval and implementation entry gate — 2026-10-12

- User approval/instruction (verbatim): "approve tasks and start project management. Remember to commit and push to github regularly".
- Approved the reconciled feature 001 tasks and authorized implementation of that
  slice only. Record small milestone commits and push to the private repository
  regularly; later features and acceptance remain unapproved.
- Loaded `speckit-implement`; ran
  `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`:
  PASS, resolving the active feature and task list. No before-implementation hooks
  were configured. Git working tree contained only the 13 planning files edited
  during this conversation; no unrelated application changes were discarded.
- `gh repo view --json nameWithOwner,visibility` confirmed
  `mgustafsn/ResearchPilot-SDD`, `PRIVATE`. Actual Git branch is `main`.
- Read-only checklist gate: `requirements.md` contains 10 items, 8 checked and
  2 unchecked. The combined approval marker is now stale relative to the recorded
  approvals; actual application acceptance evidence is still absent. Do not mark
  either checklist item passed within the implementation workflow or fabricate
  test evidence. Explicit confirmation to proceed with unchecked items is required
  by the installed workflow before coding can begin.
- No application code/dependencies/tests were added or run. All 26 tasks remain
  unchecked; this is an approval-record and planning-publication milestone.
- Pre-publication documentation assertions: PASS across 18 Markdown files for
  local links/section headings and 26 unchecked tasks; limited common credential
  pattern scan found no matches. `git diff --check`: PASS (no output). These are
  documentation checks, not application tests or a comprehensive secret audit.

## Implementation milestone 1 — local PostgreSQL foundations — 2026-10-12

- User confirmed unchecked-checklist continuation (verbatim): "yes". Checklists
  remain read-only in the implementation workflow; no acceptance evidence inferred.
- Starting commit `26927cc`, branch `main`, working tree clean. Principles I–VII
  rechecked: only approved 001, no paper/LLM/provider code, mandatory tests,
  PostgreSQL, loopback, environment secrets, and original-repository isolation.
- Observed tools: uv 0.13.0, system Python 3.14.7, project interpreter selected by
  uv CPython 3.13.15, Docker 29.9.0, Compose 5.6.0, Node v26.11.1. PostgreSQL
  container reports 17.11; exact Python dependencies are pinned in the new uv.lock.
- Created isolated Compose project `researchpilot-sdd-001`, new durable volume,
  loopback port 55432, application DB `researchpilot_sdd`, and disposable DB
  `researchpilot_sdd_test`. Generated local credentials only in ignored `.env`,
  permission 0600. No original database/repository was used or modified.
- Commands: `uv sync`, `docker compose up -d --wait db`, and dedicated `createdb`
  command from README: PASS. `uv run playwright install chromium`: PASS with an
  unsupported-OS warning; Playwright downloaded its Ubuntu 24.04 fallback Chromium
  153.0.8010.12. Browser runtime execution remains to be tested in the UI increment.
- RUN-001-RED: `uv run --env-file .env pytest backend/tests/test_project_postgres.py -q`:
  6 passed, 1 failed, 11 setup errors. Missing migration behavior intentionally
  raised NotImplementedError; safety guards passed. No absent-service/import issue
  caused the failures. Migration implementation followed this recorded red phase.
- AUD-IMPL-001: pytest's initial long traceback unexpectedly included credentialed
  fixture argument values. No credentials were committed or included in application
  browser/log output. Rotated generated local DB credentials immediately, added
  redacted URL fixture representations and short pytest tracebacks. Do not retain
  the raw red-run output in committed evidence; counts/errors above are sanitized.
- Added transactional versioned SQL migration, startup serialization, actual
  PostgreSQL constraint/reconnect/rollback tests, and test-target refusal checks.
- RUN-001-GREEN: `uv run --env-file .env pytest -q`: 18 passed in 0.54s.
  `uv run ruff check backend`: PASS after fixing two import and two line-length
  findings. `bash -n scripts/start-local.sh`: PASS. No API/browser acceptance
  results claimed yet. Full application startup smoke remains part of T003/API.
- T001/T002/T004/T005/T006 implemented with the current suite passing. T003 local
  configuration exists but stays unchecked until API/startup smoke is demonstrated.
  Real-server browser fixture is authored; it will be exercised with the API/UI.
- No prompt files changed (001 uses no runtime LLM). No features beyond 001 added.

## Implementation milestone 2 — create/list/reopen — 2026-10-12

- Milestone 1 commit `0d57390` pushed successfully to private GitHub `main`.
- RUN-002-RED: `uv run --env-file .env pytest backend/tests/test_projects.py backend/tests/test_project_api.py -q --tb=no`:
  40 failed, 20 passed. Baseline schema/HTTP scaffolds lacked normalization,
  constraints, strict numeric validation, structured errors, and create/read storage.
  Tests were present and services available before implementation.
- Implemented strict Pydantic project inputs/output, deterministic keyword
  normalization, isolated SQLAlchemy project operations, sanitized error envelopes,
  list ordering, and same-origin FastAPI routes. Pydantic is already a FastAPI
  dependency; no new external integration or LLM prompt was added.
- RUN-003-RED: `uv run --env-file .env pytest backend/tests/test_project_browser.py -q --tb=no`:
  4 failed in 98.15s against an intentionally minimal page without controls.
  Actual Chromium fallback runtime launched and local PostgreSQL/API worked;
  browser failures exposed the missing UI rather than browser installation problems.
- Implemented labeled project form/list/detail, paper count 100, keyboard focus,
  readable field errors, retained failed-save input, and text-only rendering.
- Added actual application lifespan shutdown/recreation and new PostgreSQL
  connection test; persisted API project values survive with stable ID/timestamps.
- Actual `scripts/start-local.sh` smoke: migrated the new application database,
  served UI/API on `127.0.0.1:8000`, returned an empty project list, and shut down
  cleanly. No original database was used and no application project data was created.
- RUN-003-GREEN: `uv run --env-file .env pytest -q`: 83 passed in 4.62s, with one
  Starlette/httpx test-client deprecation warning. `uv run ruff check backend`:
  PASS after correcting line-length findings. `node --check frontend/app.js` and
  `git diff --check`: PASS. Warning is retained, not hidden or treated as a failure;
  no unplanned httpx2 dependency was added.
- T003 and T007–014 completed at the create/reopen checkpoint; all currently
  implemented tests pass. These are automated/browser results, not a human keyboard
  audit, ranking evidence, or full feature acceptance. No later slice implemented.

## Prompt iteration record template

| ID/date | Feature/requirement | Exact prompt and context artifact versions | Model/tool version | Expected output | Actual output/evidence | Failure | Revised prompt | Outcome |
|---|---|---|---|---|---|---|---|---|

Attach full significant prompts or link committed prompt files. Do not reconstruct
missing original prompts as quotations. Save representative responses/diffs.

## Audit record template

| ID/date | Commit/requirement | Human/AI reviewer | Issue and evidence | Severity | Fix/diff | Regression test | Remaining limitation |
|---|---|---|---|---|---|---|---|

## Test execution record template

| Run/date | Commit/env/tool versions | Test/requirement IDs | Exact command | Expected | Actual | Pass/fail | Log/artifact | Defect/fix |
|---|---|---|---|---|---|---|---|---|

Record totals/coverage from actual output only, including failures. Documentation
consistency checks are not application verification or acceptance results.

## Contribution record template

| Member | Student ID | Role | Issues/commits/reviews | Evidence-backed contribution % |
|---|---|---|---|---|

Personal identifiers and percentages remain unfilled until supplied and agreed by the team.
