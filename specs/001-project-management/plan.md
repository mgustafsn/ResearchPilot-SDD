# Implementation Plan: Research-project management

**Feature identifier**: `001-project-management` (Git branch remains `main`) | **Updated**: 2026-10-12
**Spec**: [spec.md](spec.md)
**Status**: Approved by the user on 2026-10-12 (reply: "approve plan and API contract").
Tasks were reconciled and separately approved on 2026-10-12; the user authorized
implementation of feature 001. The workflow's unchecked-checklist confirmation
remains pending. None of these approvals constitutes acceptance evidence.

## Summary

Implement only project CRUD and a same-origin browser interface. Preserve the
baseline stack and field naming to avoid mixing methodology comparison with a
framework migration. Do not copy baseline business logic or implement future slices.

## Technical Context

- **Language/Version**: Proposed Python 3.12+, vanilla JavaScript, HTML/CSS.
- **Primary Dependencies**: FastAPI (validated HTTP API), SQLAlchemy (persistence),
   psycopg (PostgreSQL driver), uvicorn (local server). Pin compatible versions in a
   newly generated uv lockfile when implementation begins; do not copy the old lockfile.
- **Storage**: PostgreSQL 17 in a local Compose service with a durable volume and
  versioned SQL migrations. SQLite may serve fast unit/API tests only; actual
  PostgreSQL migration, API, rollback, and restart tests remain mandatory.
- **Testing**: pytest (test runner), HTTPX (API requests), pytest-playwright and
  Chromium (browser acceptance), Ruff (Python lint), Node for JS syntax checks.
  Test-only dependencies are separate from runtime dependencies. No frontend packages.
- **Target Platform**: Local Arch/Linux, loopback binding, no public deployment.
- **Project Type**: Same-origin web application with server-side configuration.
- **Performance Goals**: Approved NFR-PRJ-003: p95 below 500 ms across 100 local
  requests with 100 stored projects on the approved Linux host. The measurement
  protocol in `../../docs/verification.md` was approved with this plan.
- **Constraints**: No auth, external API calls, vectors, clustering, or provider SDKs
  needed for this first slice. No migrations of the original database.
- **Scale/Scope**: One local user, 100 projects for first-slice performance fixture.
  This slice only stores the 1–250 paper limit; retrieval semantics belong to 003.

## Constitution Check

| Principle | Revised design | Design check |
|---|---|---|
| I. Provider facts | No papers or scholarly metadata created | PASS at design level |
| II. Structured LLM output | No LLM calls or prompts needed | PASS at design level |
| III. Interface isolation | No provider SDK imports; required provider interfaces arrive with their approved slices | PASS at design level |
| IV. User query control | No queries generated or modified in 001 | PASS at design level |
| V. Transparency | UTC timestamps, sanitized errors, persisted project data; search/reference provenance deferred to its slices | PASS at design level |
| VI. Testing | Mandatory unit/API/browser/PostgreSQL tests, requirement mapping, fault tests and actual evidence | PASS at design level; execution pending |
| VII. Phased scope | Approved 001 only; simple modules; no future tables, accounts, or external services | PASS at design level |

Pre-design and post-design review on 2026-10-12 found no conflict with constitution
2.0.0 in this slice. This is a design assessment, not human approval or runtime
verification. Environment-only secrets, loopback-only same-origin operation, durable
PostgreSQL storage, and isolated test databases remain mandatory. Generic template
wording cannot make tests optional. Later feature drafts still need their own review.

## Project Structure

```text
backend/researchpilot/
  domain.py          # validated project inputs/outputs
  persistence.py     # database lifecycle and project table
  service.py         # project business operations
  api.py             # HTTP routes, error handling, same-origin static serving
backend/tests/
  conftest.py
  test_projects.py
  test_project_api.py
  test_project_postgres.py
   test_project_browser.py
   test_project_performance.py
frontend/
  index.html
  app.js
  styles.css
migrations/001_projects.sql
scripts/start-local.sh
pyproject.toml
compose.yaml
.env.example
.github/workflows/ci.yml
```

Keep familiar structure but keep backend boundaries explicit. No generic repository
framework, frontend bundler, provider registry, or background-job system for CRUD.

## Design Decisions

- Explicit input validation matches reviewed FR-PRJ rules; unknown fields forbidden.
- UUID identity, UTC timestamps; full PUT replacement, preserving createdAt and ID.
- Database transactions around each mutation; rollback on error, no success response
  before commit. Return sanitized storage failures.
- UI warns that deletion permanently removes the project and its contents with no
  undo; cancellation changes nothing. API deletion needs no extra confirmation flag.
- UI labels the `title` API field as "Project name". Treat names/questions/keywords
  as text, never HTML. Errors preserve form input; all controls are keyboard usable.
- Migration tests use a separately named disposable database; never point destructive
  test fixtures at an application or original ResearchPilot database.
- Persist only projects now. Add search ownership constraints with feature 003.
- Local configuration comes from the environment. The launcher does not print
  database URLs or credentials. Bind HTTP and any exposed database port to loopback;
  serve the UI and API together, with no permissive CORS configuration.
- Migrations run before serving requests, track applied versions, and never erase
  application data on restart. Restart tests close/recreate the application and
  database connections, verifying retained values in PostgreSQL.
- Test cleanup requires an explicit disposable test database, a test-only database
  name, and a target different from `DATABASE_URL`; abort if these safeguards fail.
  Browser tests run a real local server backed by that isolated PostgreSQL database.

## Planned requirement-to-test mapping

All entries are proposed tests, not executed results. Each implementation test must
retain requirement IDs in its name or metadata. Human review of this mapping belongs
to the plan/task gates; acceptance evidence is collected only after execution.

| Requirement | Proposed tests / evidence |
|---|---|
| FR-PRJ-001 | API CRUD routes; browser create/reopen/edit/delete (AC-PRJ-001–007) |
| FR-PRJ-002 | Name/question whitespace and exact lower/upper boundary tests |
| FR-PRJ-003 | Empty/omitted keywords, 30/31 inputs, item length, case-fold deduplication retaining first spelling/order |
| FR-PRJ-004 | Missing bounds, 1/9999, out-of-range, reversed years, noninteger and boolean rejection |
| FR-PRJ-005 | 1/250, 0/251, missing value, noninteger/boolean rejection; UI default 100 |
| FR-PRJ-006 | Stable IDs, timestamps, duplicate names, list tie ordering, actual PostgreSQL application restart/reconnect |
| FR-PRJ-007 | Extra-key and malformed input rejection; unknown IDs; injected storage failure/rollback; sanitized errors and retained form values |
| FR-PRJ-008 | Cancellation/confirmation warning/no undo, deletion persistence, cross-project isolation; no future tables in 001 |
| NFR-PRJ-001 | Canary-secret checks in API/assets/logs, sanitized exceptions, rendering audit |
| NFR-PRJ-002 | Labeled fields, keyboard navigation and confirmation, focus and text errors; browser checks and human audit |
| NFR-PRJ-003 | Real loopback HTTP and PostgreSQL latency fixture under the proposed protocol; host/software inventory and raw samples |

## Delivery and review sequence

1. Human reviews and approves this plan and `contracts/api.md`.
2. Reconcile the existing draft `tasks.md` against this design; review and approve
   task ordering separately. Do not mark tasks complete based on design checks.
3. Set up local configuration and isolated tests, then write/review failing tests
   before their corresponding project logic and UI.
4. Implement create/list/reopen, then edit/delete; no later-slice work.
5. Run the full suite, PostgreSQL restart/fault checks, lint, JS syntax, keyboard
   and secret audits, and approved performance protocol; record actual outcomes.
6. Obtain feature acceptance before planning 002. No acceptance is inferred here.

## Complexity Tracking

No constitutional violations or implementation exemptions are proposed. PostgreSQL
is constitutionally required; the small local service and optional SQLite test path
do not replace PostgreSQL acceptance evidence. No background jobs, provider registries,
frontend frameworks, authentication, or speculative future schemas are introduced.
