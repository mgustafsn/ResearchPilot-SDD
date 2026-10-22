# Feature 005 implementation tasks: Durable saved references

**Status**: Implementation and automated verification complete. Approved by the user
on 2026-10-22 (reply: “I reviewed and I approve”). Human review and final acceptance
remain open. The implementation stays within Feature 005.

## Requirements and acceptance scenarios

- FR-REF-001: Save only from a paper currently associated with the project.
- FR-REF-002: Persist an independent provider-derived metadata snapshot.
- FR-REF-003: Same-source saves are idempotent, including concurrent requests.
- FR-REF-004: List by case-folded title/source identity with safe provider links.
- FR-REF-005: Searches/provider refreshes do not mutate or delete saved snapshots.
- FR-REF-006: Remove independently; project deletion removes owned references.
- FR-REF-007: Scope operations to project; saves fail during active search.
- FR-REF-008: No manual citation, editing, notes, reading status, or numbering.
- AC-REF-001–004 and SC-REF-001–003 are mapped below.

## Phase 1 — baseline and tests first

- [X] T001 Reconfirm task approval, active Feature 005, constitution I–VII, and actual branch/dirty state. Full baseline suite on Python 3.13.15 with guarded disposable PostgreSQL: `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -q --tb=short` — **426 passed, 1 skipped in 52.52s**. Initial sandbox run could not reach the local PostgreSQL port; the same command passed with authorized local-network access. No code changes preceded this baseline; application database was not reset.
- [X] T002 Add pure domain tests for normalized provider snapshots, UUID/request validation, absent ranking fields, Unicode case-fold sorting, and null optional metadata. Existing Paper-domain tests cover unsafe URL rejection (FR-REF-002/004/008).
- [X] T003 Add PostgreSQL migration, uniqueness, JSON object/identity checks, cascade, refreshed-paper independence, reopen durability, and repeated-migration coverage. The guarded disposable fixture now truncates the new table; a separate migration-failure rollback injection was not added (FR-REF-002/003/006).
- [X] T004 Add fake-backed API/service tests for current-project results, client metadata rejection, duplicate response semantics, active-search rejection, scoped list/remove, restart, sanitized not-found errors, and saved snapshot independence after provider refresh/search replacement (FR-REF-001/002/003/005/006/007).
- [X] T005 Verify concurrent duplicate saves, stale-lease handling, save rejection while the provider has an active search, list/remove during search, cross-project IDs, and project deletion cascade (FR-REF-003/006/007).
- [X] T006 Add a Chromium journey for save/state/list/remove, inert hostile text, safe provider links, and preserving the search result after removal (FR-REF-004/006/008; AC-REF-001/003). Sorted multiple-item rendering is covered by the domain sort test; excluded controls were checked in the rendered UI.

## Phase 2 — persistence, domain, and API

- [X] T007 Implement additive migration 005 with project cascade, provider/source identity, validated JSONB snapshot, title sort key, timestamp, idempotency constraint, and project/list index. Earlier migrations remain unchanged and saved rows have no paper/result FK (FR-REF-002/003/006).
- [X] T008 Implement validated request/output and JSON snapshot parsing through the normalized `Paper` model; output omits ranking state (FR-REF-002/004/008).
- [X] T009 Reflect the table and implement project-locked current-result save, stale lease handling, active-search rejection, immutable snapshot, conflict-safe idempotency, case-fold sorting, and project-scoped list/delete (FR-REF-001–007).
- [X] T010 Add the approved GET/POST/DELETE routes; POST accepts only `paperId` and responses contain provider facts (FR-REF-001–008).
- [X] T011 Wire the service into app construction; preserve safe errors, search behavior, startup configuration, and project cascade (FR-REF-005–007).

## Phase 3 — browser experience and regressions

- [X] T012 Add current-result save and project list/remove controls. Use text nodes and checked HTTP(S) links, show saved state, and keep ranking fields out of saved snapshots (FR-REF-004/005/008).
- [X] T013 Use fake PaperProviders and guarded PostgreSQL/Chromium fixtures; no production fake mode, live-provider test, secret, dependency, or disposable-database guard weakening (FR-REF-001–008).
- [X] T014 Verify replacement search/provider refresh leave saved snapshots unchanged, and active search rejects save while list/remove work (FR-REF-005/007; AC-REF-002/003). Failed-search persistence follows the independent snapshot storage design; no separate failure-after-save case was added.
- [X] T015 Verify cross-project save/list/remove isolation and sanitized unknown paper/reference responses; project-not-found handling is implemented and covered by existing API validation patterns (FR-REF-001/006/007; AC-REF-004; SC-REF-003).

## Phase 4 — audit and verification

- [X] T016 Audit migration/data flows, provider-only snapshots, safe rendering/links, project cascade/scope, project-first lock order, no LLM/metadata edits, and API response shape. Findings are in `docs/evidence-log.md`; the audit found no remaining implementation blocker (constitution I–VII; FR-REF-001–008).
- [X] T017 Focused tests: **20 passed**; browser test: **1 passed**; final full suite: **447 passed, 1 skipped in 58.31s**. Ruff, changed-file formatting, secret-pattern scan, JS syntax, concurrency, reopen, and `git diff --check` passed. See `docs/evidence-log.md`; browser and PostgreSQL runs used authorized local access (FR-REF-001–008; AC-REF-001–004; SC-REF-001–003).
- [X] T018 Present the running feature for human keyboard/usability review. User reported satisfaction and requested no changes (SC-REF-001/002).
- [X] T019 User explicitly approved Feature 005 after review on 2026-10-22 (“Feature is approved and can be pushed to github. Project finished.”). Feature acceptance is recorded; automated journey evidence and remaining test limits are documented above and in the evidence log (SC-REF-001–003).

## Dependencies and checkpoints

- T002–T006 are test-first authoring; T002–T004 may proceed in parallel after
  shared request/response expectations are frozen. T005 depends on T003/T004
  fixture patterns; T006 follows the UI contract.
- T007 precedes T003 implementation-green verification; T008/T009 precede T010;
  T010/T011 precede T012; T013–T017 follow their implementation changes.
- No Feature 005 runtime implementation begins until this task list is approved.
- No live OpenAlex call is needed for automated tests; fake provider-derived Papers
  are sufficient. Any human ranking-evaluation retrieval is a separate activity.

Counts: **19 tasks**; setup/baseline **1**, tests-first **5**, implementation **5**,
integration/regression **4**, audit/verification/acceptance **4**. All **19 tasks**
are complete. Limitations and test coverage gaps are documented in the tasks and
evidence log; user review and acceptance were recorded on 2026-10-22.

## Requirement-to-task mapping

| Requirement | Tasks |
|---|---|
| FR-REF-001 | T004, T009–T010, T015, T017 |
| FR-REF-002 | T002–T004, T007–T009, T013, T016–T017 |
| FR-REF-003 | T003–T005, T007, T009, T017 |
| FR-REF-004 | T002, T004, T006, T008, T010, T012, T017 |
| FR-REF-005 | T004, T009, T011–T014, T016–T017 |
| FR-REF-006 | T003–T006, T007, T009–T010, T012, T015–T017 |
| FR-REF-007 | T004–T005, T009–T011, T014–T017 |
| FR-REF-008 | T002, T006, T008, T010, T012, T016–T017 |
| AC-REF-001 | T004, T006, T017, T019 |
| AC-REF-002 | T004, T013–T014, T017, T019 |
| AC-REF-003 | T005–T006, T014, T017, T019 |
| AC-REF-004 | T004–T005, T015, T017, T019 |
| SC-REF-001 | T003–T006, T017–T019 |
| SC-REF-002 | T004–T006, T013–T014, T017–T019 |
| SC-REF-003 | T005, T009–T010, T015–T019 |
