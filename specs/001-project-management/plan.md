# Implementation Plan: Research-project management

**Branch**: Proposed `001-project-management` | **Date**: 2026-10-11
**Spec**: [spec.md](spec.md)
**Status**: Draft; BLOCKED by constitution amendment and human review.

## Summary

Implement only project CRUD and a same-origin browser interface. Preserve the
baseline stack and field naming to avoid mixing methodology comparison with a
framework migration. Do not copy baseline business logic or implement future slices.

## Technical Context

- **Language/Version**: Proposed Python 3.12+, vanilla JavaScript, HTML/CSS.
- **Primary Dependencies**: FastAPI (validated HTTP API), SQLAlchemy (persistence),
  psycopg (PostgreSQL driver), uvicorn (local server). Pin compatible versions in a
  newly generated uv lockfile when implementation begins; do not copy the old lockfile.
- **Storage**: PostgreSQL, versioned SQL migrations; SQLite only for fast unit/API tests.
- **Testing**: pytest, HTTPX for API tests, Playwright for browser tests, Ruff for lint.
- **Target Platform**: Local Arch/Linux, loopback binding, no public deployment.
- **Project Type**: Same-origin web application with server-side configuration.
- **Performance Goals**: NFR-PRJ-003 proposed budget; reference host still to be approved.
- **Constraints**: No auth, external API calls, vectors, clustering, or provider SDKs
  needed for this first slice. No migrations of the original database.
- **Scale/Scope**: One local user, 100 projects for first-slice performance fixture;
  later searches at most 250 raw papers per project.

## Constitution Check

| Principle | Draft design | Gate |
|---|---|---|
| Provider facts | No scholarly metadata created in this slice | Compatible |
| Structured LLM output | No LLM calls in this slice | Compatible |
| Interface isolation | No vendor dependencies in domain/services | Compatible |
| User organization | Current constitution mandates excluded categorization | BLOCKED pending amendment |
| Transparency | UTC timestamps and structured sanitized errors | Full-scope mandates need amendment |
| Testing | Unit, API, PostgreSQL and browser tests mandatory | Planned, not verified |
| Phased scope | This checkout's reduced scope conflicts with parent scope references | BLOCKED pending amendment |

Recheck after approval and design review; do not treat this table as a passed gate.

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
- UI confirms deletion; API deletion does not require an extra confirmation flag.
- Client treats titles/questions/keywords as text, never HTML; errors preserve form input.
- Migration tests use a separately named disposable database; never point destructive
  test fixtures at an application or original ResearchPilot database.
- Persist only projects now. Add search ownership constraints with feature 003.

## Complexity Tracking

No implementation exemption is requested. The existing scope conflict is a governance
blocker, not permission to bypass the constitution. Retaining PostgreSQL adds local
setup but supports baseline comparability and actual transactional verification.
