# OpenAlex retrieval traceability — feature 003

Maps approved FR-RET-001–010 and AC-RET-001–006 to repeatable evidence. Tests use
fakes, HTTPX MockTransport, guarded disposable PostgreSQL and Chromium only. No live
OpenAlex or OpenAI request was made.

| Requirement | Evidence in `backend/tests/` |
|---|---|
| FR-RET-001 | `test_openalex_provider.py::test_FR_RET_001_request_sends_exact_query_and_inclusive_year_filters_only`; `test_retrieval_api.py::test_FR_RET_001_002_search_uses_exact_enabled_queries_and_inclusive_bounds`; `test_retrieval_browser.py::test_FR_RET_001_006_search_is_explicit_and_displays_provider_results` |
| FR-RET-002 | `test_papers.py::test_FR_RET_002_*`; `test_openalex_provider.py::test_FR_RET_002_*`; `test_retrieval_api.py::test_FR_RET_002_*`; `test_retrieval_performance.py::test_FR_RET_002_006_mock_provider_pipeline_reference_host` |
| FR-RET-003 | `test_papers.py::test_FR_RET_003_*`; `test_openalex_provider.py::test_FR_RET_003_*` |
| FR-RET-004 | `test_papers.py::test_FR_RET_004_*` |
| FR-RET-005 | `test_papers.py::test_FR_RET_005_*` |
| FR-RET-006 | `test_retrieval_api.py::test_FR_RET_006_*`; `test_retrieval_postgres.py::test_FR_RET_006_*`; `test_retrieval_browser.py::test_FR_RET_001_006_*`; retrieval performance report |
| FR-RET-007 | `test_retrieval_api.py::test_FR_RET_007_*`; `test_retrieval_postgres.py::test_FR_RET_007_*` |
| FR-RET-008 | `test_retrieval_api.py::test_FR_RET_008_*`; `test_retrieval_postgres.py::test_FR_RET_008_*` |
| FR-RET-009 | `test_openalex_provider.py::test_FR_RET_009_*`; `test_retrieval_browser.py::test_FR_RET_001_006_*` |
| FR-RET-010 | `test_papers.py::test_FR_RET_010_*`; `test_retrieval_browser.py::test_FR_RET_010_*` |

## Current evidence and boundaries

- Final local verification on 2026-10-19: **358 passed**, one known Starlette/HTTPX
  deprecation warning. The additive migration 003 was applied at local app startup;
  app root responds HTTP 200. Full output and commands are in `docs/evidence-log.md`.
- The approved-host fake-provider benchmark measured **204.55 ms p95** under the
  2-second target; see `retrieval-performance.json`.
- `docs/evidence/retrieval-performance.json` contains the approved-host mock-provider
  benchmark's raw timings, statuses, source hashes, software versions and host/load.
  It measures local normalization/deduplication/persistence, not live provider latency.
- Query text and inclusive year filters are sent to OpenAlex only after explicit
  Search. Project question/keywords are retained locally in the attempt snapshot and
  are not sent. OpenAI remains unconfigured per the user's preference.
- No coverage percentage, live result quality, ranking accuracy or remote GitLab CI
  success is claimed. Human usability review and explicit feature-003 acceptance remain
  separate gates. Features 004–005 and full-text/PDF work are excluded.
