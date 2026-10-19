# Feature 002 validation guide — implementation and evidence

The specification, plan, contracts, and tasks are approved. Manual query management
and fake-tested suggestion generation are implemented. Repeatable tests and query
performance evidence are recorded in `docs/evidence-log.md` and
`docs/evidence/query-performance.json`; audits, human review, remote CI, and feature
acceptance remain pending. Feature 001's BUG-PRJ-001 remains deferred.

## Prerequisites

- Existing local Python 3.12+/uv/FastAPI/PostgreSQL 17 setup and vanilla browser UI.
- Continue using this rebuild's dedicated application database and safeguarded
  `researchpilot_sdd_test` database; never use the original database.
- Existing test guards require the disposable name, local host, distinct
  `DATABASE_URL`, and `ALLOW_TEST_DATABASE_RESET=1` before cleanup.
- No provider credentials are needed for manual-query acceptance or the automated
  suite. Inject fake suggestion providers and HTTPX mock transports in tests.
- A real generation request sends the stored research question/keywords to the
  configured external AI provider. It requires server-side environment credentials
  and explicit user action; opening/editing a project must not cause an AI call.

## Automated acceptance journeys

1. Create/reopen a project and inspect its query list. Manually add a query, edit
   it, disable/re-enable it, and reopen/restart. Stored text/state remains unchanged
   and all controls have labels and keyboard operation (FR-QRY-002/003).
2. With a fake provider returning a valid batch, explicitly generate suggestions.
   Review origin labels and enabled states; no paper/citation/search result is
   shown. Query selection is tested independently, not through a search route
   (FR-QRY-001/006).
3. Edit one generated query and disable another. Regenerate: both are user-owned
   and retain text/state, while only untouched generated queries are replaced.
   Restore the original text/state and regenerate again: ownership persists
   (FR-QRY-004).
4. Return a batch duplicating preserved queries. Validate the complete batch first,
   skip collisions, and permit zero new additions without modifying preserved
   entries. Invalid/malformed/refused/truncated batches fail atomically
   (FR-QRY-001/002/005).
5. Populate 20 saved queries, including disabled ones. Manual addition fails without
   losing input or stored data. Regeneration preserves user-owned entries, respects
   available slots, and reports capacity/duplicate skips (FR-QRY-008).
6. Change the question/keywords. Existing queries/enabled states remain, and the
   refresh notice survives reload/restart. A failed/stale generation cannot clear
   it; successful generation for the current context clears it (FR-QRY-009).
7. Pause the fake provider with a test barrier. Edit/toggle/delete a query, change
   the project, or delete it before releasing the provider. Reject the obsolete
   response without stale writes or resurrected data (FR-QRY-007/010).
8. Delete a query and generate in a later attempt: the same text may reappear.
   Disable instead when retaining the excluded entry is desired. No suppression
   history is created (FR-QRY-010).
9. Simulate timeout, unavailable configuration, upstream error, invalid JSON, and
   storage/commit failure. Existing queries/refresh state remain intact, errors
   are readable and sanitized, and manual management remains usable (FR-QRY-005).
10. Use browser request interception/barriers to navigate between projects or edit
    queries while generation is pending. A delayed response must not repaint a
    different project or overwrite newer displayed state.

## Repeatable automated commands

From the repository root with the dedicated local PostgreSQL and disposable test
database configured:

```bash
uv sync --locked
uv run playwright install chromium
uv run --env-file .env pytest -m "not performance" -q
uv run ruff check backend
node --check frontend/app.js
```

On the approved reference host, run performance regressions separately with
`uv run --env-file .env pytest -m performance -q`; retain query results using
`PERFORMANCE_OUTPUT=docs/evidence/query-performance.json`.

The suite must cover `test_queries.py`, `test_query_api.py`,
`test_query_provider.py`, `test_query_postgres.py`, and `test_query_browser.py`
under `backend/tests/`, alongside all existing project regression tests.
Update hard-coded migration expectations for the reviewed 002 migration without
weakening version tracking, rollback, or PostgreSQL restart checks.

Performance measurements run separately on the approved reference host after
approval of the 002 protocol. A fast fake-provider result does not measure live AI
latency or suggestion quality; CI must not claim approved-host timing acceptance.

## Evidence and manual review

- Record actual commands, commit/working-tree state, host/software versions, all
  failures/fixes, requirement mappings, and sanitized output in the evidence log.
- Audit browser responses/assets/logs for credentials, raw provider bodies, input
  snapshots, and unsafe rendering. Record prompt versions and mock request shape.
- Run human keyboard/usability review and obtain explicit feature acceptance;
  automated tests cannot impersonate that reviewer.
- Live-provider smoke testing is separate, opt-in, and requires explicit permission
  for data disclosure/cost. Never make it a default test, migration, or CI step.
- Do not start OpenAlex retrieval or ranking/reference work in this slice.
