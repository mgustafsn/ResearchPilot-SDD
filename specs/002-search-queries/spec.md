# Feature Specification: User-controlled search queries

**Feature Branch**: Proposed `002-search-queries` (not created)
**Created**: 2026-10-11
**Status**: Draft — clarification/review active; human specification approval required
**Input**: Retain description-driven query suggestions and user control; exclude categorization.

## User Scenarios & Testing

### User Story 1 — Review suggestions (Priority: P1)

As a researcher I can generate short suggestions, inspect them, and decide what to search.
**Why this priority**: The long research description is context, not a provider query.
**Independent Test**: With a saved project and fake suggestion provider, generate and reload.
**Acceptance Scenarios**:
1. **Given** a project, **When** generation succeeds, **Then** 3–6 unique short suggestions appear and persist (AC-QRY-001).
2. **Given** saved queries, **When** generation times out or returns invalid output, **Then** the list is unchanged and a readable error appears (AC-QRY-002).

### User Story 2 — Control the query list (Priority: P1)

**Why this priority**: The user must control the actual search inputs.
**Independent Test**: Add/edit/toggle/delete queries without a live LLM or search.
**Acceptance Scenarios**:
1. **Given** suggestions, **When** I edit one and add another, **Then** both survive regeneration and reopening (AC-QRY-003).
2. **Given** disabled queries, **When** search runs in feature 003, **Then** only enabled query texts are sent (AC-QRY-004).
3. **Given** no enabled queries, **When** I request search, **Then** validation prevents a provider call (AC-QRY-005).

### Edge Cases

Empty output; duplicate normalized texts; all queries disabled; malformed structured
response; deletion during generation; project edits while a suggestion request is pending.

## Requirements

### Functional Requirements

- **FR-QRY-001**: Generate 3–6 suggestions using the question and keywords as context; request a structured list and validate before persisting.
- **FR-QRY-002**: Each query MUST collapse whitespace and contain 1–160 characters; equivalent case-folded texts MUST NOT be duplicated within a project.
- **FR-QRY-003**: Users MUST add, edit, delete, enable, and disable queries; persist their changes. New suggestions/manual queries default to enabled.
- **FR-QRY-004**: Regeneration MAY replace only untouched generated queries. Edited queries become user-owned and MUST survive regeneration.
- **FR-QRY-005**: Failed regeneration MUST leave the entire saved list unchanged. Manual query entry remains available; no silent fallback is generated.
- **FR-QRY-006**: Long research descriptions MUST NOT be searched directly. The enabled stored query list is the authoritative search input.
- **FR-QRY-007**: Generation uses a snapshot; if the project or query-list revision changes before persistence, reject the stale write with a conflict and preserve newer data.

### Key Entities

SearchQuery: ID, project ID, text, enabled flag, origin, user-owned flag.
Project/query-list revision: concurrency identity used to reject stale generation.

## Success Criteria

- **SC-QRY-001**: AC-QRY-001–005 pass with fake providers, including invalid-output and timeout injection.
- **SC-QRY-002**: Regeneration preserves edited/manual texts and enabled state in all relevant regression fixtures.
- **SC-QRY-003**: A spy provider confirms zero scholarly calls for no enabled queries and no direct research-description queries.

## Assumptions

Depends on approved feature 001, accepted by the user with BUG-PRJ-001 deferred on
2026-10-12; see `../../docs/known-issues.md`. Its outstanding audit evidence and
year-input nonconformance are not silently resolved by this feature. Only query
suggestion uses runtime LLM text generation.
Model and timeout choices belong in the reviewed plan. Failure preservation differs
from the original fallback behavior and needs approval.
