# Implementation Plan: Durable saved references

**Branch**: `005-saved-references` (actual Git branch: `main`) | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification, technical plan/supporting design, and task list approved by the user on 2026-10-22. Implementation and automated verification are complete; human review and final acceptance remain open.

## Summary

Add a project-scoped reading list containing immutable snapshots of papers that
currently belong to that project's search results. Store a normalized provider
snapshot in PostgreSQL, keyed for idempotency by `(project_id, provider,
provider_id)`. Add scoped list/save/remove API routes and a small UI section with
save/remove controls. Reuse current Paper validation, project locking, FastAPI,
SQLAlchemy, PostgreSQL, and browser-test patterns. Do not add metadata editing,
manual citations, notes, reading status, or other excluded features.

## Technical Context

**Language/Version**: Python 3.12+; vanilla JavaScript/HTML/CSS.

**Primary Dependencies**: Existing FastAPI, Pydantic, SQLAlchemy, psycopg, pytest,
HTTPX, Playwright, and Ruff. No dependency additions proposed.

**Storage**: Local PostgreSQL 17; one additive migration creating
`saved_references`. Existing provider-owned `papers` and search associations stay
unchanged. The saved row copies a validated provider snapshot and has no foreign
key to `papers` or `project_papers`, so later search replacement and provider
refreshes cannot alter or remove the saved record.

**Testing**: Fake provider-derived records for API/domain tests; guarded disposable
PostgreSQL for migration, snapshot durability, concurrency, project isolation and
restart tests; local Chromium/loopback for UI journeys. No live providers in the
automated suite.

**Target Platform**: Local single-user Linux web app, same-origin on loopback.

**Project Type**: Existing Python web service with static vanilla-JS frontend.

**Performance Goals**: No feature-specific latency budget is approved. Do not make
performance acceptance claims; measure only if a reviewed verification plan adds
a budget and reference environment.

**Constraints**: A reference can be saved only from a current project result;
reject saves during an active search. List and remove remain available during a
search. All operations are project-scoped. Project deletion cascades to its saved
references. Keep provider-owned metadata separate from project-specific saved
state; never store ranking scores as paper facts.

**Scale/Scope**: Single user; paper retrieval remains bounded to 250 per search.
No new cap on a project's saved reading list is specified. Use the simple
project-scoped list query; do not add pagination or background processing without
a reviewed requirement.

## Constitution Check

Pre-design and post-design assessment against constitution 2.0.0:

| Principle | Design assessment | Gate |
|---|---|---|
| I — Provider facts | A save copies an already normalized Paper from OpenAlex search results. No manually supplied or LLM-generated metadata is accepted. | PASS at design level |
| II — Structured LLM | No LLM call, prompt, or generated metadata is added. | PASS |
| III — Integration boundaries | Routes/service consume normalized Paper/domain models and existing persistence; no vendor SDK imports. | PASS at design level |
| IV — Query control | Saved references do not change or regenerate query records. | PASS |
| V — Transparency and recovery | Snapshots retain provider/source identity and links. Search replacement and failures do not alter saved rows; project deletion is explicit and cascades. | PASS at design level |
| VI — Tests/evidence | Fake-backed business/API tests, PostgreSQL migration/concurrency/restart tests, browser checks, stable FR/AC mapping and truthful evidence are required before completion. | PASS at design level; execution pending |
| VII — Scope/simplicity | Implements approved Feature 005 only, with one table and existing stack. All excluded reference-management features stay out. | PASS at design level |

Security/configuration: PostgreSQL only; same-origin local deployment; no new
secrets, external requests, or licensed full-text fetch/storage. Snapshot fields
are validated with the strict normalized Paper model before storage and after
loading for display. Project ownership is checked in every read/write path.

These were design assessments before implementation. Implementation findings and
test evidence are recorded in `docs/evidence-log.md`; human review and final feature
acceptance remain outstanding.

## Project Structure

### Documentation (this feature)

```text
specs/005-saved-references/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/api.md
  tasks.md                 # Approved implementation and acceptance checklist
```

### Source Code (repository root)

```text
backend/researchpilot/
  api.py
  paper_domain.py
  retrieval_service.py
  references_domain.py     # Reference request/output models, snapshot validation
  references_service.py    # Project-scoped transactional operations
  persistence.py
backend/tests/
  test_references.py
  test_references_api.py
  test_references_postgres.py
  test_references_browser.py
migrations/005_saved_references.sql
frontend/{index.html,app.js,styles.css}
```

**Structure Decision**: Extend the current monolithic local application. A focused
references service keeps the snapshot and ownership rules together; a new provider
interface, repository abstraction, service process, database, or frontend framework
would add no needed capability.

## Design Decisions

See [research](research.md), [data model](data-model.md), and
[API contract](contracts/api.md). The main concurrency rule is to lock the owning
project row before reading active-search state or modifying a saved reference. This
matches the existing retrieval/project-service lock order and serializes concurrent
same-project saves. A database uniqueness constraint remains the final idempotency
guard.

## Requirement-to-Test Mapping

| Requirement | Planned evidence |
|---|---|
| FR-REF-001/007 | API/service tests reject missing, unrelated, and cross-project paper IDs; save during active search returns the agreed conflict. |
| FR-REF-002/005 | PostgreSQL tests verify a copied provider snapshot survives result replacement, paper refresh, and restart without mutation. |
| FR-REF-003 | Concurrent duplicate-save PostgreSQL test plus unique-constraint migration assertion; both calls return one stable reference. |
| FR-REF-004 | API/browser list-order and safe-link rendering tests, including Unicode case-folded title ordering and missing DOI. |
| FR-REF-006 | Remove leaves search results intact; project deletion cascades; cross-project remove is not found. |
| FR-REF-008 | Contract/UI audit confirms no metadata edit, manual citation, notes, reading status, or numbering controls. |
| AC-REF-001–004 | Browser journey with fake provider and disposable PostgreSQL across save, duplicate save, replacement, restart, removal and project isolation. |
| SC-REF-001–003 | Full automated suite, actual PostgreSQL migration/concurrency/restart evidence, and final human acceptance. |

## Complexity Tracking

No constitutional deviations. One additive snapshot table is needed for durability
and independence from current search associations. A unique index and existing
project-row lock jointly handle duplicate concurrent saves without adding queueing,
distributed locks, caches, or new dependencies.

## Open Review Items

- Review the proposed snapshot schema and API status/error behavior in the supporting
  artifacts before approving tasks.
- No latency threshold or saved-reference count limit is invented; introduce either
  only through an explicitly reviewed spec/verification change.
- Human browser/usability review and feature acceptance remain later gates.
