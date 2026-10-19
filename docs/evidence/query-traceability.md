# Search-query feature traceability — 2026-10-19

This maps FR-QRY-001–010 to automated evidence for the implemented feature 002
slice. Tests use fakes/mock HTTP and the guarded disposable PostgreSQL database;
no live OpenAI request was used. Passing automation is not human acceptance,
remote CI verification, or proof of live suggestion quality.

| Requirement | Automated evidence (`backend/tests/`) |
|---|---|
| FR-QRY-001 | `test_query_provider.py`: exact request/prompt/schema and strict-output cases; `test_query_api.py`: generation output, revalidation and typed metadata; `test_query_browser.py`: explicit generation and no automatic call on load/context change |
| FR-QRY-002 | `test_queries.py`: normalized text and batch validation; `test_query_provider.py`: Unicode/invalid batches; `test_query_api.py`: strict API input; `test_query_postgres.py`: normalized-key uniqueness |
| FR-QRY-003 | `test_query_api.py`: manual CRUD/default ownership; `test_query_postgres.py`: persistence/restart/selection; `test_query_browser.py`: controls, keyboard focus and inert hostile text |
| FR-QRY-004 | `test_queries.py`: merge/ownership rules; `test_query_api.py`: edited/toggled/manual query preservation and restoration; `test_query_postgres.py`: sticky ownership; `test_query_browser.py`: regeneration preserves owned state |
| FR-QRY-005 | `test_query_provider.py`: refusal, malformed response, timeout, one-attempt, body bound, cancellation and canary-log checks; `test_query_api.py`: unchanged state for provider/storage failures and sanitized errors; `test_query_postgres.py`: rollback; `test_query_browser.py`: error/input retention |
| FR-QRY-006 | `test_queries.py` and `test_query_postgres.py`: exact enabled stored-text selection; no scholarly search route is implemented in 002 |
| FR-QRY-007 | `test_query_postgres.py`: same-revision writes/generation, context edits, deletion, cancellation and stale merge; `test_query_browser.py`: edit/manual mutation/navigation/deletion during pending generation |
| FR-QRY-008 | `test_queries.py`, `test_query_api.py`, `test_query_postgres.py`: 1–20 capacity/slot behavior; `test_query_performance.py`: 100-request approved-host CRUD protocol, raw results in `query-performance.json` |
| FR-QRY-009 | `test_queries.py`, `test_query_api.py`, `test_query_postgres.py`, `test_query_browser.py`: durable context notice, preservation, acknowledgment and restart |
| FR-QRY-010 | `test_query_api.py`, `test_query_postgres.py`, `test_query_browser.py`: delete/reappearance without suppression, stale response and deleted-project behavior |

## Current gates and limitations

- Full local suite: 281 passed, 1 existing Starlette/HTTPX test-client deprecation
  warning; exact final command and environment are in `docs/evidence-log.md`.
- Query performance: 100/100 successful requests; nearest-rank p95 3.81 ms against
  the approved 500 ms budget. Raw samples, environment, dirty-state disclosure and
  source hashes are in `query-performance.json`.
- `docs/evidence-log.md` records the prompt version/hash, static audit, findings,
  test evidence and limitations. No live model quality/cost/latency or zero-retention
  claim is made.
- Remote GitLab CI remains unverified (VPN required). Human keyboard/usability review
  and explicit feature acceptance remain outstanding. Feature 001 BUG-PRJ-001 remains
  deferred and is not fixed or re-evaluated here.
