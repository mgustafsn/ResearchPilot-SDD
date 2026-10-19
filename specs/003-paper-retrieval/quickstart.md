# Feature 003 validation guide — draft

**Status**: Plan/contract and task review pending. This guide is not authorization for
live provider calls. Automated tests must use fake `PaperProvider` and HTTPX `MockTransport`.

## Prerequisites

- Existing local Python/uv, Docker Compose/PostgreSQL, Node and Chromium setup.
- Dedicated `researchpilot_sdd` application DB and guarded disposable
  `researchpilot_sdd_test`; never point tests at the application/original database.
- No OpenAI key is needed or used. No OpenAlex API key/account is created for tests.
- In the running app, only clicking Search may contact OpenAlex. That sends enabled
  saved query text and selected year filters to OpenAlex; project question/keywords
  are kept in the attempt snapshot but not transmitted.

## Automated validation journeys

1. Create a project with stored queries and select an inclusive year range. Search
   with a fake provider; assert exact enabled query texts and year filters are sent,
   no project question/keywords are sent, and the input snapshot is complete.
2. Verify paper allocation in stored-query order for limits 1, 20, 100 and 250,
   including zero-allocation queries, and prove no request/page exceeds the allocation
   or 20-request attempt bound.
3. Map fixed OpenAlex work fixtures for DOI, OpenAlex ID, abstract inverted index,
   authors, publication fields, venue, citation count and OA links. Missing optionals
   remain missing; missing title is skipped/counted; malformed envelopes fail.
4. Exercise DOI/identity/title dedup, distinct conflicting DOIs, transitive bridges,
   richness merge/ties and stable result order using deterministic fixtures.
5. Inject 429, timeout, malformed/oversized response and DB write/commit failure.
   Confirm previous result associations remain byte-for-byte equivalent and references
   are not touched. A fully successful empty result replaces associations with none.
6. Use PostgreSQL barriers for active ownership, project/query mutation conflicts,
   expiry/new attempt, stale worker commit rejection, restart persistence and atomic
   rollback. Never hold a database lock while waiting on the provider.
7. Browser test explicit Search disclosure, pending/success/failure, current results,
   text-only malicious metadata, unsafe URL rejection, focus/keyboard behavior,
   navigation during a pending call and preserved results on failure.
8. Confirm no OpenAI API request, model output, LLM metadata, full-text download,
   ranking score, reference editing or out-of-scope schema appears in the slice.

## Repeatable commands after implementation

```bash
docker compose up -d --wait db
uv run --env-file .env pytest -m "not performance" -q
uv run ruff check backend
node --check frontend/app.js
```

The guarded disposable test DB must be configured as documented in the repository
README. On the approved reference host, run the separately approved mock-provider
PostgreSQL pipeline benchmark. Do not include live OpenAlex or paid-service latency in
that measurement. Exact provider limits/performance budgets remain proposals until the
plan is approved.

## Separate live-service use

The approved product behavior permits an explicit Search to contact OpenAlex after a
clear disclosure. No live smoke test has been authorized. Tests, quickstart validation,
and CI must remain offline with fakes. Do not create an OpenAlex key/account or call
OpenAlex on the user's behalf.
