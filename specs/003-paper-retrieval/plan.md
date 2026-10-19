# Implementation Plan: OpenAlex retrieval and deduplication

**Branch**: `003-paper-retrieval` (actual Git branch: `main`) | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: User-approved feature specification in `specs/003-paper-retrieval/spec.md`.

**Status**: Plan, API/provider contracts and tasks approved by the user on 2026-10-19; implementation of feature 003 is authorized.

## Summary

Retrieve real OpenAlex works for the exact enabled-query snapshot, normalize
provider-owned metadata, and deduplicate before an atomic replacement of current
project results. Use the existing HTTPX/PostgreSQL/FastAPI stack, a `PaperProvider`
interface, bounded user-triggered OpenAlex requests, and persistent attempt ownership.
No OpenAI call, paid/live smoke test, ranking, or reference-management feature is
part of this slice. Search query text and inclusive year filters are disclosed to
OpenAlex only after explicit Search; project question/keywords are retained in the
audit snapshot but not transmitted.

## Technical Context

**Language/Version**: Python 3.12+; vanilla JavaScript/HTML/CSS.

**Primary Dependencies**: Existing FastAPI, Pydantic, SQLAlchemy, psycopg, HTTPX,
uvicorn, pytest, Playwright and Ruff. No new dependency proposed.

**Storage**: Existing local PostgreSQL 17; one additive versioned migration for
provider-owned papers, current project-paper associations, and search attempts.

**Testing**: pytest, HTTPX `MockTransport`/fake `PaperProvider`, guarded disposable
PostgreSQL, and real local Chromium/loopback HTTP; no live provider in automated tests.

**Target Platform**: Local single-user Linux web app, same-origin on loopback.

**Project Type**: Existing Python web service with static vanilla-JS frontend.

**Performance Goals**: Approved target (2026-10-19): local mock-provider normalization,
deduplication and PostgreSQL replacement of 250 papers p95 <2 seconds over 20
sequential searches on the approved 001 reference host. Excludes startup and external
OpenAlex latency. Approved by the user with the plan on 2026-10-19.

**Constraints**: 1–250 raw-record budget; 1–20 saved queries; at most 20 OpenAlex
HTTP requests per attempt; at most two concurrent requests; proposed 10-second
per-request and 120-second whole-attempt deadlines; proposed 150-second ownership
lease; 2 MiB response cap per request; no automatic retries. These request/deadline/
performance values were approved with the plan on 2026-10-19. No API key is needed for
the bounded basic-use path; never set up a paid key/account as part of implementation.

**Scale/Scope**: Single user; one active retrieval per project; at most 250 fetched
records per attempt. OpenAlex only. No clustering, ranking, saved-reference UI,
full-text/PDF retrieval, or multiple providers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Design assessment | Gate |
|---|---|---|
| I. Provider facts | Only the OpenAlex `PaperProvider` maps authoritative work metadata; LLM output is absent. | PASS at design level |
| II. Structured LLM | This slice makes no LLM call; no prompts or LLM metadata path added. | PASS |
| III. Integration boundaries | OpenAlex HTTP is confined to its adapter; service/domain use normalized `Paper` and `PaperProvider`. Retrieval, normalization, deduplication and persistence remain separate. | PASS at design level |
| IV. User query control | Exact enabled stored queries are snapshotted at attempt start; no regeneration or query mutation is introduced. | PASS at design level |
| V. Transparency/recovery | Persist input snapshot, provider, timestamps, status/counts and sanitized error; visible pending/success/failure; prior results preserved on failure; bounded ownership prevents stale commit. | PASS at design level |
| VI. Tests/evidence | Fakes/mock HTTP only in repeatable tests; PostgreSQL/concurrency/browser coverage and FR-RET mapping required. | PASS at design level; execution pending |
| VII. Phased simplicity | Only approved 003 retrieval; no ranking, references, full-text, caches, auth, or other provider. Existing HTTPX reused. | PASS at design level |

Security/configuration gate: PostgreSQL only; loopback/local same-origin; OpenAlex
request made only by explicit action; no OpenAI key/request; no API key or paid OpenAlex
plan introduced; if an optional key is considered later, it must come from the server
environment and require separate reviewed approval. No licensed full text is fetched
or stored. Parameter, request-count, concurrency, timeout, lease, payload-size, and
performance values above were approved with the plan.

Pre-design and post-design Constitution Checks both pass at design level for
Principles I–VII. They do not establish implementation verification; the approved
operational/performance budgets must be verified during implementation.

## Project Structure

### Documentation (this feature)

```text
specs/003-paper-retrieval/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── contracts/provider.md
└── tasks.md             # Separate /speckit-tasks gate
```

### Source Code (repository root)
```text
backend/researchpilot/
  paper_domain.py
  paper_provider.py
  retrieval_service.py
  persistence.py
  api.py
  integrations/openalex_papers.py
backend/tests/
  test_papers.py
  test_retrieval_api.py
  test_openalex_provider.py
  test_retrieval_postgres.py
  test_retrieval_browser.py
migrations/003_paper_retrieval.sql
frontend/{index.html,app.js,styles.css}
```

**Structure Decision**: Extend the existing single Python web app, with a focused
provider adapter and common domain model. Reuse current persistence, API, frontend,
and test fixture patterns. No separate service, repository abstraction, SDK, or
frontend framework is proposed.

## Approved design decisions

### Provider request and bounds

- Use `GET https://api.openalex.org/works` with the stored query text as `search`,
  optional inclusive `from_publication_date` / `to_publication_date` filters,
  `per_page` at most 100, and basic page numbers only as needed for that query's
  allocation. Do not send project question/keywords, project name, or unused queries.
  Do not request reranking, semantic search, or full text.
- Divide the raw-record budget by enabled-query count in stored slot order as required
  by FR-RET-002. Never fetch beyond each allocation. Enforce at most 20 provider
  requests per attempt. No retry after 429, timeout, transport, or invalid response.
- Two in-flight requests, 10-second request deadline and 120-second total
  attempt deadline; no API key by default. OpenAlex documents no-key basic use and
  10 requests/second, with keys raising daily budget and paid usage beyond included
  quotas. Keep under that rate; do not create a key or paid plan. Log request count
  and provider cost metadata if returned, without credentials.
- Fetch only required selected fields. Reject oversized/malformed response envelopes;
  count individual missing-title records as skipped. Do not store raw response JSON.

### Normalization and deduplication

- Map OpenAlex `id`, `doi`, `title`, `abstract_inverted_index`, `authorships`,
  `publication_year`, `publication_date`, `primary_location.source.display_name`,
  `primary_location.landing_page_url`, `best_oa_location`, `open_access`, and
  `cited_by_count` to common `Paper` fields. Rebuild abstract words by ascending
  inverted-index positions; malformed optional abstracts are omitted, not invented.
  Work-list results expose at most the first 100 authors; accept this provider limit
  rather than adding per-work follow-up calls.
- Retain only `http`/`https` source/publication/full-text links; use `textContent` in
  the UI. `is_oa` missing stays unknown. Never fetch or persist PDF/publisher content.
- Normalize DOI as specified. Deduplicate first by canonical DOI, then OpenAlex ID,
  then normalized title. Build DOI-equality groups first; then union same OpenAlex ID
  only where the resulting component contains no more than one distinct nonempty DOI.
  For title fallback, if all same-title records contain zero or one distinct DOI,
  merge them; if multiple distinct DOIs exist, keep each DOI group separate and merge
  DOI-less records only with one another, unless provider-ID equality already safely
  connected them. Thus a DOI-less record cannot bridge two conflicting DOI groups.
  Choose the richest source record (number of valid populated normalized fields); ties
  keep earliest query-allocation/API order. Fill missing fields from later records;
  never overwrite a populated field from the selected richest record with a less-rich
  conflicting value. Dedup is deterministic.
- Provider-returned search order is retained for 003 display, with deterministic
  ties by source identity. Do not expose OpenAlex relevance score as scientific
  quality; feature 004 owns embedding ranking.

### Atomic storage and ownership

- Store provider-owned `Paper` rows separately from project-specific `ProjectPaper`
  result associations and `SearchRun` attempt records. Do not add feature-005 saved
  reference tables; replacement must not delete any future independent references.
- Lock the project row before checking/creating an active run. A partial unique index
  permits one pending run per project. Capture query/context/filter/budget/provider
  snapshot; commit before network calls. No database transaction is held during HTTP.
- The 150-second lease exceeds the 120-second attempt deadline.
  Project/query edits, deletion and another search conflict while a nonexpired attempt
  is active. Expired attempts are marked failed/interrupted before ownership is
  replaced. Final transaction verifies attempt token and live lease, upserts normalized
  provider facts and atomically replaces associations. Stale/expired workers cannot
  update run success or current results.
- On any request/normalization/storage failure, mark the run failed with a safe
  category and retain previous associations. A successful empty run atomically removes
  current associations. Attempt snapshot/history is retained; no history UI/polling is
  proposed in this slice.
- On current-results reads, a pending run whose lease has expired is lazily marked
  failed/interrupted and released; this lets an application restart recover without a
  background worker. Remove provider `Paper` rows only when no current project
  association remains; future references use independent snapshots and are not FK-bound
  to this table.

### UI, observability, and verification

- Add explicit Search control and visible pending/success/failure state, actual queries
  used/unused, fetched/skipped/duplicate counts, and safe metadata/source links. Render
  untrusted values as text and allow only safe link schemes.
- Test API, provider mapping, DOI/title identity cases, malformed records, year bounds,
  budget allocation, 429/timeout/cancellation, rollback, active-owner expiry and stale
  worker races with fakes plus real disposable PostgreSQL and browser tests.
- Approved reference-host pipeline benchmark is documented in Technical Context;
  actual OpenAlex network latency is recorded separately and is not a hard latency
  acceptance criterion. These budgets and normalization/merge rules were approved
  with the plan; implementation must verify them as specified.

## Requirement-to-Test Mapping

| Requirement | Proposed evidence |
|---|---|
| FR-RET-001 | `test_openalex_provider.py`: exact request/data-flow/year filter; API/browser explicit-search disclosure and no automatic calls |
| FR-RET-002 | `test_papers.py`: ordered allocation/zero-use; provider mock asserts request/page cap |
| FR-RET-003 | `test_openalex_provider.py`: provider field mapping, missing optionals and abstract reconstruction; no LLM source |
| FR-RET-004 | `test_papers.py`: DOI normalization, DOI precedence, conflicting DOI, OpenAlex identity and title normalization |
| FR-RET-005 | `test_papers.py`: richness/tie fixtures, transitive bridge cases and deterministic merge output |
| FR-RET-006 | `test_retrieval_api.py`, `test_retrieval_postgres.py`, `test_retrieval_browser.py`: snapshots, lifecycle/counts, sanitized errors and visible state |
| FR-RET-007 | `test_retrieval_postgres.py`: failure/commit rollback preserves associations; successful empty attempt replaces them |
| FR-RET-008 | `test_retrieval_postgres.py`: one owner, expiry, mutation conflicts and stale-worker commit rejection |
| FR-RET-009 | `test_retrieval_browser.py`: provider/source/OA links, unknown OA state, allowed schemes |
| FR-RET-010 | `test_retrieval_browser.py`: hostile provider text and unsafe URLs are inert/nonclickable |

Every automated provider test uses a fake or HTTPX mock. Requirement mappings do not
replace human audit/acceptance or a separately authorized live-provider smoke test.

## Complexity Tracking

No constitutional deviations are proposed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
