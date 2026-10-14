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

## Implementation milestone 3 — edit/delete — 2026-10-12

- Milestone 2 commit `8b74762` pushed successfully to private GitHub `main`.
- RUN-004-RED: `uv run --env-file .env pytest backend/tests/test_project_api.py backend/tests/test_project_browser.py -q --tb=no`:
  9 failed, 13 passed in 11.95s. Expected missing PUT/DELETE routes and edit/delete
  controls; existing create/reopen workflows still passed. New tests preceded logic.
- Implemented full transactional PUT and DELETE with stable identity/createdAt,
  success-only updatedAt, strict input checks, approved status/error shapes, and
  project isolation. No future-owned tables or search locks were added.
- Implemented edit form population and a keyboard-accessible native confirmation
  dialog explicitly warning of permanent deletion/no undo. Cancel sends no DELETE;
  confirmed deletion does not remove another project's records.
- Added real PostgreSQL application restart checks for successful update/deletion
  and commit-failure rollback tests for both mutations. Raw injected exception/SQL
  strings remain absent from API responses and captured application logs.
- RUN-004-GREEN: `uv run --env-file .env pytest -q`: 93 passed in 7.25s with the
  same single test-client deprecation warning. `uv run ruff check backend`,
  `node --check frontend/app.js`, and `git diff --check`: PASS after an import-order
  correction. All T015–019 tasks completed; final verification/human gates pending.
- Tests use synthetic project inputs and explicitly disposable PostgreSQL only.
  No human audit, feature acceptance, or later-slice approval is implied.

## Implementation milestone 4 — automated verification — 2026-10-12

- Milestone 3 commit `d7c0959` pushed successfully to private GitHub `main`.
- Added execution/commit fault injection for create/update/delete with successful
  retry and no partial writes; failed multi-statement migrations leave no partial
  table/version. Added canary and generated-password response/asset/log checks,
  malicious HTML text-only rendering, Escape focus return, and failed deletion UI.
  These new regressions passed existing behavior; no fake red-phase claim is made.
- AUD-IMPL-002 (FR-PRJ-007): generic field errors did not explain how to correct
  numeric input. Added a failing correction-message regression before adding safe
  field-specific messages for numeric/text/length/year/JSON errors; no raw input,
  arbitrary unknown keys, SQL, or exception context reaches the response.
- AUD-IMPL-003 (NFR-PRJ-001): test guard could allow reset without an application
  target to compare. Added a failing regression, then required a configured
  application URL and local test host in addition to the explicit opt-in/name checks.
  Combined regression command on PostgreSQL/API tests: 2 failed, 45 passed in 2.22s.
- AUD-IMPL-004 (local scope/original isolation): runtime storage accepted unrelated
  database names and nonlocal/SQLite targets. Before fixing, `pytest ... -k
  runtime_refuses -q --tb=no`: 3 failed, 23 deselected. Added safe runtime refusal
  for non-PostgreSQL, nonloopback, or non-dedicated DB names, retaining only this
  rebuild's application/test databases. No authentication/public deployment added.
- RUN-005-GREEN: `PERFORMANCE_OUTPUT=docs/evidence/project-performance.json uv run --env-file .env pytest -q -s --junitxml=docs/evidence/project-tests.xml`:
  **110 passed in 10.39s**, one known Starlette/httpx test-client deprecation warning.
  Actual JUnit output is in `docs/evidence/project-tests.xml`; raw sanitized timing
  evidence is in `docs/evidence/project-performance.json`.
- NFR-PRJ-003: **p95 2.39 ms**, below the approved 500 ms target. Actual approved
  Ryzen 7 5700X3D host, Linux 7.2.9-2-cachyos, PostgreSQL 17.11, real loopback HTTP,
  100 seeded projects, 10 untimed reads, 20 five-operation cycles, 100 retained
  successful samples, nearest-rank 95th value. Report includes versions/load,
  baseline commit `d7c0959`, dirty-tree disclosure, timestamp, and source hashes.
  This small controlled sample does not establish load scalability or scientific
  ranking accuracy. It covers only the approved project-operation budget.
- CI-parity command `uv run --env-file .env pytest -m "not performance" -q`:
  109 passed, 1 deselected in 9.44s. Ruff, JS syntax, and diff whitespace checks:
  PASS. GitHub workflow added for PostgreSQL/browser/unit/API/lint checks with
  synthetic disposable CI-only credentials; remote execution is not yet claimed.
- Evidence verification: JUnit 110 tests/0 failures/0 errors, 100 timing samples,
  all source hashes match; actual generated credential absent from all 75 current
  publishable files. This is a bounded leak check, not a comprehensive secret audit.
- Added `docs/evidence/project-traceability.md` with actual FR/NFR test mappings.
  T020–022 complete. T023 awaits workflow publication/observation; T024 human audit,
  T025 final post-audit verification, and T026 explicit acceptance remain unchecked.
- AI static audit by OpenCode/GPT-6.1 Sol: project inputs rendered through textContent,
  DB/API errors sanitized, environment configuration isolated, no provider/LLM SDK
  paths, only 001 schema plus migration bookkeeping, loopback deployment retained.
  Remaining limitation: no human reviewer keyboard/usability findings yet. Built-in
  checklist markers were not changed by implementation; no human review fabricated.

## GitHub verification and remaining human gates — 2026-10-12

- Verification commit `077b2b1` pushed successfully. GitHub Actions run
  https://github.com/mgustafsn/ResearchPilot-SDD/actions/runs/38243969348
  completed successfully for full SHA `077b2b18ade38c6369a8279a1445fd914b828cae`.
  `gh run watch 38243969348 --exit-status` returned success; test job took 1m12s.
- Remote logs confirm CPython 3.12.15, Ruff PASS, JavaScript syntax PASS, and
  **109 passed, 1 deselected, 1 warning in 11.69s**. Real PostgreSQL 17 and Chromium
  browser tests ran; approved-host performance was deliberately deselected.
  JUnit evidence was uploaded as `project-test-results` by the workflow.
- CI annotations retained: Node 20-based action versions are forced onto Node 24
  by GitHub; ubuntu-latest has a scheduled Ubuntu 26 migration. Neither prevented
  this run. They are future maintenance considerations, not erased failures.
- T023 complete. **23/26 tasks completed**; T024 human keyboard/usability review,
  T025 final post-audit verification, and T026 explicit acceptance remain pending.
  The AI/static/browser audit cannot impersonate a human reviewer. Feature 002
  planning/implementation is still blocked by feature 001 acceptance.
- To review locally, run `./scripts/start-local.sh` and open
  `http://127.0.0.1:8000`; test creating/reopening/editing, validation, keyboard
  navigation, cancelled deletion, confirmed deletion, and persistence on restart.
  Existing ignored local configuration and dedicated PostgreSQL are ready on this
  machine. The original repository/database remain untouched.
- Final documentation assertions: PASS (23 completed/3 pending tasks, checklist
  unchanged at 8/10, local links/headings valid, measured source hashes still match).
  `git diff --check`: PASS. No configured after-implementation hooks found.

## User project-management review finding — 2026-10-12

- User feedback (verbatim): "I'vet tried all that you can do, publication years allow for characters other than numbers then default to \"Any - Any\" if letters were put in. This should be fixed in future MVPs".
- Human reviewer: user; self-reported review of available functionality. Exact
  browser/version, typing sequence, and individual keyboard/audit scenarios were
  not supplied, so no more detailed manual test evidence is inferred.
- Recorded BUG-PRJ-001 (FR-PRJ-004/007, AC-PRJ-004) in `docs/known-issues.md`:
  invalid publication-year entry may silently become unbounded. User explicitly
  deferred the fix; no application code or approved requirements were changed.
- Inspected current number controls and empty-value-to-null conversion. This is
  a possible mechanism, not an independently reproduced/confirmed root cause.
  The earlier 110-test result remains historical evidence, not verification of
  this newly reported case. No new application tests were executed.
- Explicit feature acceptance with this known limitation still needs confirmation;
  the reported defect is not marked fixed/compliant and feature 002 is not started.

## Feature 001 acceptance with limitation; feature 002 review entry — 2026-10-12

- User reply (verbatim): "Yesw", interpreted as yes to the immediately preceding
  explicit question accepting project management with the known publication-year
  issue so feature 002 can be reviewed. No claim that BUG-PRJ-001 is fixed, that
  every requirement passes, or that missing detailed human audit evidence exists.
- Feature 001 accepted with BUG-PRJ-001 deferred. T024 detailed human-audit evidence
  and T025 final post-audit verification remain outstanding. User self-reported
  trying available functionality; exact browser/keyboard cases remain unspecified.
- Feature 002 specification review may begin; approval of its spec/plan/tasks or
  implementation is not inferred. No application code, schemas, prompts, secrets,
  or dependencies changed as part of this transition.
- Machine-local `.specify/feature.json` now points to `specs/002-search-queries`;
  it remains ignored by Git. No branch was created; the working branch is `main`.
- Re-read constitution 2.0.0 and feature 002 draft. Next review focuses on editable
  query suggestions and preservation of user-controlled text/enabled state; no
  scholarly retrieval/ranking/reference implementation is authorized here.
- Re-ran `uv run --env-file .env pytest -q`: 110 passed, one known test-client
  warning in 10.41s. This does not cover or resolve the newly reported browser-year
  issue. `git diff --check`: PASS. Feature path prerequisite check resolved 002.
- T026 records user acceptance with the known limitation; 24/26 tasks checked,
  T024/T025 still outstanding. Neither their audit evidence nor full compliance
  is fabricated by this acceptance. Feature 002 clarification begins separately.

## Feature 002 clarification decisions — 2026-10-12

- User chose "A" for suggestion regeneration: replace only untouched AI queries;
  preserve manual queries and generated queries edited or enabled/disabled by the
  user, including their stored text and enabled state. Recorded the exact question
  and accepted answer in `specs/002-search-queries/spec.md`.
- Applied the decision to FR-QRY-004 and AC-QRY-003. User ownership remains tracked
  after a subsequent restoration of the original text/state; regeneration cannot
  silently reclaim user-controlled queries. This is a product-decision approval,
  not approval of the whole specification, plan, tasks, or implementation.
- No application code, runtime prompts, or dependencies changed; no application
  test outcome is claimed by this documentation update.
- User chose "A" for duplicate suggestions: validate a 3–6 unique normalized batch
  first, then skip collisions with preserved queries; allow zero new additions and
  a combined list larger than six. Updated FR-QRY-001/002 and AC-QRY-001 without
  changing the approved protection of user-owned text or enabled state.
- User chose "A" for query-list size: at most 20 saved queries per project,
  counting enabled and disabled entries together. Manual additions over the limit
  fail without writes; regeneration fills free slots without removing user-owned
  queries. Added FR-QRY-008, SC-QRY-004, and explicit capacity edge cases; batch
  order determines which suggestions fit. Whole-spec/plan/task approval is pending.
- User chose "a" for changed research context: retain all queries/enabled states,
  show a refresh notice, and make no automatic provider call or query deletion.
  Added FR-QRY-009/SC-QRY-005. The notice is durable until successful generation
  for the current question/keywords; failed/stale generation cannot clear it.
- User chose "A" for deleted suggestions: delete the stored entry without a
  text-suppression history; permit the same text in a later explicit generation.
  Disabling preserves the user-owned entry/state; pending generation is rejected
  if deletion changes the revision. Added FR-QRY-010/SC-QRY-006.
- Clarification loop complete: five questions asked/answered. Updated sections:
  Clarifications, User Scenarios & Testing, Edge Cases, Functional Requirements,
  Key Entities, and Success Criteria. No feature 002 checklist exists to toggle;
  no before/after clarification hooks are configured.
- AUD-QRY-SPEC-001: draft success criteria implied that 002 needed implemented
  scholarly searches. Clarified AC-QRY-005/SC-QRY-001/003 so 002 verifies stored-query
  selection with fixtures and actual search/provider-spy acceptance belongs to 003.
  This scope-consistency correction remains part of the draft awaiting review.
- Coverage: scope, domain/state, interaction and edge cases resolved; interface
  boundaries, terminology, completion signals and placeholders clear at spec level.
  Exact provider/model configuration, timeout/request limits, error contracts,
  safe concurrency persistence and measurable performance protocol are deferred to
  plan review, not silently approved by these five product decisions.
- Documentation assertions PASS: five recorded clarification answers, ten query
  functional requirements, 46 globally unique requirement IDs, valid local links
  and no duplicate section headings. `git diff --check`: PASS. No feature 002
  implementation, application tests, dependency installation, or live AI calls ran.

## Feature 002 specification approval — 2026-10-12

- User approval (verbatim): "approve query specification".
- Marked `specs/002-search-queries/spec.md` approved, including the five recorded
  clarification decisions, FR-QRY-001–010, and the clarified distinction between
  stored-query selection in 002 and scholarly search integration in 003.
- Updated README/scope gate status without changing approved requirements. Query
  generation failure preserves the existing list and manual entry; this is approved
  behavior, not proof of implementation or approval for live AI calls.
- Plan, provider/model configuration, timeout/request budgets, contracts, task
  ordering, and implementation still require their separate review gates. Feature
  001's publication-year issue remains open/deferred; no audit evidence was invented.
- No application code, prompts, schemas, dependencies, or tests changed. No new
  application test outcome is claimed for this approval-record update.

## Feature 002 plan preparation — 2026-10-12

- User request (verbatim): "Lets start that" after the proposed implementation-plan
  review. This authorizes drafting/review, not plan approval or feature 002 coding.
- Loaded `speckit-plan`; `.specify/scripts/bash/setup-plan.sh --json` succeeded and
  resolved 002 paths. The copied generic template was replaced with the feature
  design. Actual branch remains `main`; feature identifier is `002-search-queries`.
  No extension hooks were configured.
- Reviewed constitution 2.0.0, approved spec, scope, existing database/service/API,
  dependencies, CI, known issue and verification artifacts. No original repository
  or credential file was read as source material.
- The planning skill explicitly asks for research agents; delegated two independent
  read-only research tasks, with no implementation/dependency/secret access:
  `general` session `ses_ecfeb1312ffe7fPfbPMir0n5mN` checked official OpenAI model,
  structured-output/endpoint/privacy documentation; `explore` session
  `ses_ecfeadc7affeWbn2qfcqQzVzwT` inspected current persistence/integration risks.
  Child model versions were not separately pinned/reported. Their findings are
  research/design recommendations, not runtime tests or human approval.
- Created draft `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`,
  `contracts/provider.md`, and `quickstart.md` under `specs/002-search-queries/`.
  No `tasks.md` or application implementation was generated in this phase.
- Proposed pinned `gpt-4.1-mini-2025-04-14`, strict JSON Chat Completions over
  existing HTTPX (promoted to runtime only after implementation approval), one
  call/no retries, 512 completion tokens, actual async 20 s deadline, phase limits,
  64 KiB body bound, and two upstream connections. Model/budgets are unapproved
  proposals; no SDK/new package family or live API calls were introduced.
- PROMPT-QRY-001: candidate `query_suggestions_v1` prompt is recorded verbatim in
  the provider contract as a proposal, not a created runtime prompt or executed
  LLM call. Context is user-role JSON data, not privileged instructions; output
  permits query text only, never authoritative paper/citation metadata.
- Privacy disclosure: proposed `store:false` does not mean zero retention. Official
  docs describe default abuse-monitoring retention up to 30 days with exceptions;
  external generation sends stored question/keywords only on explicit action.
  Manual management requires no API key; live smoke testing needs separate consent.
- AUD-QRY-PLAN-001 (FR-QRY-007/008/009): proposed parent-first locks and one combined
  revision, separate context/generation counters, and bounded slots/key uniqueness.
  No external call under a DB transaction, no lease/job/history schema. First
  committed concurrent generation wins; newer edits/delete prevent stale overwrite.
- AUD-QRY-PLAN-002: existing migration-count assertions, projects-only truncation,
  project update/delete, and frontend delayed-response behavior need reviewed
  integration changes. Preserve existing project JSON shapes/timestamps/PUT rules,
  explicit test-target safeguards, and unchanged deferred year conversion.
- AUD-QRY-PLAN-003: corrected stale verification-strategy claims that no 001 tests
  or benchmark had run. Added an explicitly unapproved 002 query-CRUD timing
  protocol; no query benchmark or quality evaluation was run.
- Mapped all FR-QRY-001–010 to proposed fake-provider/mock-HTTP/unit/API/PostgreSQL/
  browser evidence. Scholarly search/provider-spy acceptance remains in 003, not 002.
- Pre/post-design Constitution Check: Principles I–VII compatible at design level;
  environment-only secrets, local PostgreSQL, source/prompt/test evidence and review
  gates retained. Not human approval, full 001 compliance, or application acceptance.
- No code, dependencies, migration, runtime prompt, CI configuration, or live API
  request changed. Plan/contract approval and separate tasks review remain pending.
- Documentation validation PASS: six 002 planning artifacts, ten requirement/test
  mappings, 26 Markdown files checked for local links/headings and limited common
  credential patterns; no unresolved template markers or prematurely generated
  tasks. `git diff --check`: PASS. No application tests ran for this documentation
  phase. No configured after-plan hooks found.

## Feature 002 plan and contract approval — 2026-10-12

- User approval (verbatim): "approve query plan and contracts".
- Recorded approval of `specs/002-search-queries/plan.md`, API/provider contracts,
  supporting design/validation guide, and the 002 verification protocol. Approved
  choices include pinned GPT-4.1 Mini, structured JSON, one call/no retries,
  512-token cap, 20 s total deadline, parent revision/lock design, and local query
  CRUD p95 below 500 ms under the documented reference-host protocol.
- Task generation/review/approval and implementation remain separate gates. No
  paid/live smoke call is authorized by this decision. No runtime code, migration,
  prompt file, dependency, or test was added or changed; no test result is claimed.
- BUG-PRJ-001 remains deferred and uncorrected. Feature 001's missing detailed
  audit evidence is not supplied by this approval; feature 003 remains unapproved.

## Feature 002 task preparation resumed — 2026-10-13

- User request (verbatim): "Ok lets continue"; after an interrupted response,
  user requested continuation and then "resume". This authorizes task drafting/
  review, not task approval, application implementation, or paid/live AI calls.
- Loaded `speckit-tasks` and read its template plus approved specification, plan,
  API/provider contracts, model, rationale, quickstart, constitution and scope.
  The setup script completed before the interruption; interrupted patch created
  no file. On resume, Git was clean on `main` before the new task draft was written.
- Generated `specs/002-search-queries/tasks.md`: 36 sequential unchecked tasks,
  comprising setup 3, foundations 5, US2 manual control 8, US1 suggestions 11, and
  verification/audits/acceptance 9. Both stories are P1; manual control comes first
  per the approved plan, so the initial demo needs no API key.
- AUD-QRY-TASK-001: explicit tests-before-logic sequence, deliberate contract
  scaffolds rather than import/setup failures as red evidence, exact model/budget/
  prompt constraints, revision/context/ownership/slot rules and legacy compatibility
  are included. Generic optional-test wording remains overridden by Principle VI.
- AUD-QRY-TASK-002: include real-PostgreSQL/barrier and browser delayed-response
  schedules, safe multi-table fixture rollout, entire batch validation, zero-add
  context acknowledgment, no-op ownership/revisions, and ordinary manual use
  without configuration. The deferred year-input bug is explicitly out of this
  implementation task list; no full 001 audit evidence is invented.
- All FR-QRY-001–010 have task mappings; task IDs are local to feature 002, and
  original US1/US2/requirement IDs are unchanged. Independent authoring pairs are
  T009/T010 and T017/T018 after their listed prerequisites; no delegation was used
  and destructive test execution remains sequential by default.
- Tasks include regular tested commit/push milestones and separate human audit/
  acceptance. No app code, migration, runtime prompt, dependency, test, or CI file
  was changed during drafting; no application/quality/performance result is claimed.
- Explicit task/implementation approval is still required. No scholarly provider,
  search route, ranking/reference work, history/lease, SDK, or live smoke is added.
- Documentation validation PASS: 36 sequential unchecked tasks with checklist
  format/file paths, US2=8/US1=11, four independent-authoring markers, all ten query
  requirement mappings, and 27 Markdown local-link/heading/limited credential-pattern
  checks. `git diff --check`: PASS. No configured after-tasks hooks found. These
  checks are not application verification, and no application tests ran.

## Feature 002 implementation authorization — 2026-10-13

- User approval (verbatim): "approve query tasks and start implementation".
- Approved all 36 reviewed tasks and implementation of feature 002 only. Start
  with manual controls, then structured suggestions. Continue regular verified
  commits/pushes. No live/paid provider smoke call or BUG-PRJ-001 fix authorized.
- Baseline commit `6d11deb`, actual branch `main`, clean worktree. Implementation
  prerequisite check resolved feature 002/tasks. No 002 checklist files or extension
  hooks exist; no unchecked checklist confirmation is required for this feature.
  Existing 001 audit/checklist limitations remain recorded, not overwritten.
- Existing ignore rules cover credentials, Python/browser/build artifacts and
  Docker context. Checked dedicated Compose service: not running at entry; startup
  is limited to this rebuild's named service/volume, never the original database.
- Promoted already-present HTTPX to runtime and added deliberate missing-behavior
  contract scaffolds. Config example contains no secret values; ignored user
  configuration is not overwritten. No live HTTP/model call is introduced.

## Feature 002 milestone 1 — manual query controls — 2026-10-13

- Restarted only the dedicated Compose PostgreSQL service successfully; preserved
  its volume and user configuration. `uv sync` promoted existing HTTPX with no new
  package family. Baseline full suite: 110 passed in 10.85s, one known test-client
  deprecation warning. No application/production data cleanup was performed.
- QRY-RED-001: `uv run --env-file .env pytest backend/tests/test_queries.py -q --tb=no`:
  36 failed, 2 passed; missing constraints/normalization/notice/selection behavior
  in intentional importable scaffolds. Added ownership/merge tests before those
  helpers: 3 failed, 38 passed. Then implemented strict common models, immutable
  context, metadata validation, batch/merge/selection rules and provider protocol.
- QRY-RED-002: PostgreSQL query-schema tests: 8 failed before migration/reflection/
  revision changes. Added migration 002, shared reflection, parent locks and
  effective/context revision hooks. Preserved existing project JSON/timestamps/PUT
  rules; tests now expect the reviewed two migration versions and real pre-failure
  rollback counts. Explicit multi-table fixture cleanup retains all safeguards.
- QRY-RED-003: manual API tests: 7 failed before query routes/service implementation.
  Added real same-revision concurrency/failed-commit tests: 2 failed, 8 passed
  before manual query logic. Implemented transactional CRUD, uniqueness/capacity/
  revision checks, typed sanitized errors, sticky ownership and exact stored selection.
- QRY-RED-004: real Chromium/injected-provider browser tests: 3 failed in 10.61s
  against the page without query controls. Implemented labeled manual controls,
  ownership/state display, retained invalid drafts, text rendering, and context
  notices. View/revision guards prevent obsolete callbacks clearing newer drafts.
- Added actual application close/recreate PostgreSQL persistence, restored generated
  ownership, no-op behavior and enabled-only service-selection regressions. Provider
  fakes/barrier helpers exist only in tests; no production fake setting or live
  adapter call is implemented. Runtime adapter and prompt creation remain pending.
- QRY-GREEN-001: `uv run --env-file .env pytest -q`: **180 passed in 15.50s**, one
  known Starlette/httpx test-client warning. Existing project/browser/performance
  regressions are included. `uv run ruff check backend`, `node --check frontend/app.js`,
  and `git diff --check`: PASS after fixing import/line-length findings.
- T001–016 completed for the manual-control milestone; T017–036 pending. Full
  feature 002 acceptance, live-model quality, external latency, query-specific
  performance protocol, and human audit are not claimed. BUG-PRJ-001 is unchanged.
- No runtime LLM prompt has changed or executed yet. Ordinary manual query actions
  never call an AI/scholarly provider. Secrets remain in ignored environment state.
- Bounded pre-publication checks: 16 completed/20 pending tasks, generated database
  credential absent from publishable files, original publication-year conversion
  unchanged. This is not a comprehensive secret audit or a reproduction/fix of
  the deferred browser issue.
- Application migration smoke applied 002 to this rebuild's application database
  and verified every original field of its one existing project unchanged; no
  application records were deleted or shown. First bare `uv run` Python import
  failed before DB access because backend is not installed as a package; retried
  successfully with `PYTHONPATH=backend`, as the launcher already configures.

## Query manual-control milestone publication — 2026-10-13

- Implementation milestone `5fd0a3f` pushed successfully to private GitHub `main`.
- GitHub Actions run https://github.com/mgustafsn/ResearchPilot-SDD/actions/runs/38373581252
  completed successfully for `5fd0a3f1bcb8ff65b67a822acf8a2bc89eba48c6`.
  Remote logs: **179 passed, 1 deselected, 1 warning in 21.68s**; Ruff and JS
  checks passed. CI intentionally excludes reference-host performance acceptance.
- Full local suite remains 180 passing, including the existing project performance
  regression. Query-specific performance, real-model evaluation, generation/UI
  integration, final audits and human acceptance are still pending (T017–036).
- To review the manual increment, restart `./scripts/start-local.sh`, open the
  existing project's details at `http://127.0.0.1:8000`, and use Search queries.
  Migration retains existing project values; no key is needed. Adding a key does
  not activate the unimplemented generator and no paid call has been made.
- No after-implementation hooks are configured. This is a verified incremental
  checkpoint, not completion of feature 002 or authorization for feature 003.

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

## GitLab repository migration — 2026-10-14

- User supplied the new private repository URL:
  `https://gitlab.abo.fi/marcgust/ResearchPilot-SDD`.
- Changed local `origin` fetch/push URL to the corresponding `.git` URL. Added
  `.gitlab-ci.yml` with loopback PostgreSQL, repeatable non-performance tests,
  Ruff, JavaScript syntax, and JUnit artifacts. Updated forward-looking 002
  plan/task references (T031) and README; retained historical GitHub run evidence.
- No application prompt or business logic changed. Requirement mapping: the
  existing T031 CI work and constitution VI test evidence.
- `git diff --check`: PASS. `uv run ruff check backend`: PASS.
  `node --check frontend/app.js`: PASS.
- Initial `uv run pytest -m 'not performance' -q` lacked the guarded test
  database settings: 109 passed, 70 setup errors, 1 deselected. Retried with
  `.env`; the isolated PostgreSQL container was stopped, so that run had
  connection errors. After `docker compose up -d --wait`,
  `uv run --env-file .env pytest -m 'not performance' -q --tb=short`:
  **179 passed, 1 deselected, 1 warning in 13.88s**. The warning is a
  Starlette/HTTPX test-client deprecation notice.
- `git ls-remote origin HEAD` reached GitLab but could not authenticate to
  the private repository (`could not read Username`). GitLab CI has not run
  remotely, and no push or remote pipeline result is claimed.
- User clarified that pushing requires their VPN; push is deferred to the user.
  The migration is committed locally only. The legacy
  `.github/workflows/ci.yml` is retained unchanged pending a decision to remove it.

## Query generation milestone (T017–T027) — 2026-10-14

- Scope: feature 002 US1 only. No live OpenAI call, no real API key used, no
  scholarly provider/search route, no BUG-PRJ-001 change. Base commit `92804b6`.
- Environment: Python 3.13.15 (uv venv), HTTPX 0.28.1, FastAPI 0.143.0,
  Pydantic 2.14.1, Node v26.11.1, local loopback PostgreSQL via `docker compose`.
- Red phase (T017–T019, before T020–T022):
  `uv run --env-file .env pytest backend/tests/test_query_provider.py
  backend/tests/test_query_api.py backend/tests/test_query_postgres.py -q`:
  **88 failed, 20 passed**. Causes were missing behavior only: adapter takes no
  arguments / no `from_environment` (54), generate route 405 (31), no
  `QueryService.generate` (2), plus barrier waits. Browser red phase (T023):
  **7 failed, 3 passed** (no Generate control).
- Prompt (T020): `backend/researchpilot/prompts/query_suggestions_v1.txt`,
  version `query_suggestions_v1`, SHA-256
  `0cc54399eb157d45cb5a6f76b82ffad8007d1c5f02fbcc68e6efa0b526de571e`. Text is the
  approved contract prompt verbatim (contract line breaks retained). Mock-request
  evidence: `test_FR_QRY_001_exact_request_shape_and_prompt` asserts the exact
  endpoint, bearer header, model `gpt-4.1-mini-2025-04-14`, `store:false`,
  `stream:false`, `n:1`, `max_completion_tokens:512`, strict schema, two messages
  (system prompt file, user JSON `{researchQuestion, keywords}`) and no tools.
- Adapter limits verified by tests: 20 s total async deadline over headers and
  body (slow-body test times out while per-chunk progress continues), 3/2/5/15 s
  phase timeouts, 2 connections, no redirects, `trust_env=False`, TLS verify,
  64 KiB incremental body cap (stops reading; exact-limit body accepted, +1 byte
  rejected), single attempt for HTTP/transport errors, cancellation propagation,
  sanitized errors with suppressed exception context, canary key/context absent
  from all captured logs.
- Service/API (T021/T022): snapshot transaction released before the provider
  await; re-lock, stale check, merge, context acknowledgment and revision bump in
  one transaction; batch re-validated in the service; provider exceptions mapped
  to 503/504/502 fixed messages; missing parent 404 with no resurrection. Logs:
  project UUID, status, duration, model/prompt version, token counts, merge counts.
  Production composition reads `OPENAI_API_KEY`/`OPENAI_QUERY_MODEL`; missing key or
  unreviewed model disables generation only. The adapter client closes at shutdown.
  The subprocess browser fixture strips `OPENAI_API_KEY` from its environment.
- Audit-test change: `test_NFR_PRJ_001_credentials_absent_from_assets_api_and_logs`
  matched the substring `import openai`, which falsely flagged the composition
  import `from researchpilot.integrations import openai_queries`. Replaced with an
  AST check that is stricter: recursive over `backend/researchpilot`, rejects any
  `openai`/`openalex` module import, and rejects `researchpilot.integrations`
  imports from business modules. Verified by injecting such an import into
  `query_service.py`: the audit failed; the probe was removed.
- Test-harness fix: Playwright leaves an event loop on the main thread, so async
  tests run via `conftest.run_async` (fresh thread). Before that fix the full suite
  had 52 `asyncio.run() cannot be called from a running event loop` failures.
- Mutation checks (temporarily applied, then reverted): disabling the stale-revision
  check → 6 PostgreSQL failures; deleting owned rows during merge → 3 failures;
  removing the browser view guard → navigation test failed.
- UI (T024): explicit "Generate suggestions" button, OpenAI disclosure, disabled
  with readable text when unconfigured, per-project pending state (duplicate
  clicks blocked; manual work, navigation and deletion stay available), merge-count
  status, text-only rendering, epoch/revision-bound responses, saved-state reload on
  error without clearing unsaved input.
- Quickstart (T027): journeys 1–10 are covered by automated tests with fake and
  disabled providers, including restart into a manual-only profile and deleted-query
  reappearance. No manual browser walkthrough or human review was performed.
- Final runs: `git diff --check` PASS; `uv run ruff check backend` PASS;
  `node --check frontend/app.js` PASS;
  `uv run --env-file .env pytest -m 'not performance' -q`:
  **277 passed, 1 deselected, 1 warning** (Starlette/HTTPX test-client
  deprecation notice). Per file: provider 56, query API 29, query PostgreSQL 26,
  query browser 10, query domain 47. `pytest -m performance`: 1 passed (existing
  project budget; not query performance, T030 pending).
- Requirement mapping: FR-QRY-001 (provider/API/browser generation tests),
  FR-QRY-002 (batch/Unicode validation), FR-QRY-004 (preservation/restoration),
  FR-QRY-005 (failure categories, unchanged state, manual still works),
  FR-QRY-007 (stale/concurrency schedules), FR-QRY-008 (zero-slot/capacity),
  FR-QRY-009 (atomic notice acknowledgment), FR-QRY-010 (deletion/no resurrection).
- Not claimed: live model quality, cost, latency, or zero retention. Fake-provider
  results are not live evidence. Committed locally only; push deferred to the user
  (VPN required). T028–T036 (fault/security expansion, browser safety, query
  performance, CI run, audits, human review, acceptance) remain pending.
