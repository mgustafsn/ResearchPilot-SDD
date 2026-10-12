# Project-management traceability — 2026-10-12

This maps approved requirements to implemented automated tests, not human sign-off.
Tests run against synthetic inputs and a safeguarded disposable PostgreSQL database.
See `project-tests.xml` for actual execution and `project-performance.json` for the
approved-host timing parameters, 100 samples, versions, baseline commit/dirty state,
and source hashes. No coverage percentage or security certification is claimed.

| Requirement | Implemented evidence (under `backend/tests/`) |
|---|---|
| FR-PRJ-001 | `test_project_api.py`: `create_list_read`, `full_update_preserves_identity`, `delete_isolated_and_unknown_ids`; `test_project_browser.py`: create/reopen and edit/delete journeys |
| FR-PRJ-002 | `test_projects.py`: normalization, invalid/exact boundaries and required fields; `test_project_postgres.py`: database constraints |
| FR-PRJ-003 | `test_projects.py`: first spelling/order, case-fold deduplication, empty/omitted keywords and 30/31/100/101 boundaries |
| FR-PRJ-004 | `test_projects.py`: optional bounds, strict integers, reversed years and exact boundaries; PostgreSQL constraint tests |
| FR-PRJ-005 | `test_projects.py`: required count, 1/250 and rejected 0/251/types; browser default 100 |
| FR-PRJ-006 | API timestamps/duplicate-name/tie-order checks; PostgreSQL migration reruns and actual application recreation for create/update/delete |
| FR-PRJ-007 | API validation/malformed JSON/unknown-ID tests, execution/commit fault injection, readable correction messages; browser retained failed saves/edits/deletion; atomic failed migrations |
| FR-PRJ-008 | Isolated transactional deletion, permanent/no-undo dialog, no DELETE on cancellation, restart persistence and other-project preservation; future-owned tables intentionally absent |
| NFR-PRJ-001 | Canary/actual generated-password checks on assets/API/captured logs, malicious-text rendering, dedicated-local runtime targets, safe test targets and redacted URL representations; AI static audit recorded in log |
| NFR-PRJ-002 | Browser labels/focus/error text, keyboard creation and deletion cancellation/confirmation, Escape focus return; **human keyboard/usability audit remains pending** |
| NFR-PRJ-003 | `test_project_performance.py`: actual loopback HTTP/PostgreSQL, 100 stored projects, 10 warm-up reads and 100-request CRUD mix, nearest-rank p95 below 500 ms |

## Remaining gates

- T024: human keyboard/usability audit, with truthful reviewer identity/findings.
- T025: final post-audit verification and completion of review gates; automated
  execution evidence is already available but cannot substitute for the human audit.
- T026: explicit user acceptance before feature 002 planning/implementation.
- Built-in checklist markers remain read-only under the implementation skill;
  their stale approval marker is not an unrecorded revocation of approved artifacts.
