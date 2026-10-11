# Feature Specification: Research-project management

**Feature Branch**: Proposed `001-project-management` (not created)
**Created**: 2026-10-11
**Status**: Draft — human approval required
**Input**: Derive the project-management slice from the existing ResearchPilot for the reduced SDD rebuild.

## User Scenarios & Testing

### User Story 1 — Create and reopen a project (Priority: P1)

As a researcher, I can persist my question and constraints so I can return later.
**Why this priority**: Every subsequent workflow needs a durable project.
**Independent Test**: Create via the interface, restart, and reopen the same project.

**Acceptance Scenarios**:
1. **Given** no projects, **When** I open the application, **Then** I see an empty state and a create action (AC-PRJ-001).
2. **Given** valid inputs, **When** I save, **Then** the project has an ID and persisted values and appears in the list (AC-PRJ-002).
3. **Given** a saved project, **When** the application restarts, **Then** reopening retains its values (AC-PRJ-003).
4. **Given** invalid inputs, **When** I save, **Then** field errors appear and no project is created (AC-PRJ-004).

### User Story 2 — Edit and delete a project (Priority: P2)

**Why this priority**: Questions evolve and obsolete projects should be removable.
**Independent Test**: With an existing project fixture, edit, reload, then delete it.

**Acceptance Scenarios**:
1. **Given** a project, **When** I save valid edits, **Then** reopening shows those edits without changing its ID (AC-PRJ-005).
2. **Given** a delete confirmation, **When** I cancel, **Then** nothing changes; confirming removes the project and its owned records (AC-PRJ-006).
3. **Given** an unknown ID, **When** I read, update, or delete, **Then** I receive a not-found response (AC-PRJ-007).

### Edge Cases

Whitespace-only required fields; repeated keywords differing only in case; exact
length bounds; missing or reversed year bounds; booleans supplied as integers;
database failure; deletion of one project leaving another untouched. Search-lock
behavior is added by feature 003, not implemented speculatively here.

## Requirements

### Functional Requirements

- **FR-PRJ-001**: Users MUST create, list, read, fully update, and delete projects.
- **FR-PRJ-002**: Trim name/question; name MUST contain 1–200 characters, question 1–5000.
- **FR-PRJ-003**: Accept at most 30 keywords, each trimmed to 1–100 characters; remove case-insensitive duplicates, retaining first spelling/order.
- **FR-PRJ-004**: Optional year bounds MUST be integers 1–9999, excluding booleans; start MUST NOT exceed end. A missing bound means unbounded on that side.
- **FR-PRJ-005**: Maximum paper count MUST be an integer 1–250, excluding booleans; the UI initially offers 100. This is a reduced-scope proposal.
- **FR-PRJ-006**: Persist IDs, fields, and creation/update timestamps across restart. Duplicate project names are permitted; order lists by newest update then ID.
- **FR-PRJ-007**: Reject unknown input fields and invalid values without changing stored data. Show readable validation/not-found/storage errors.
- **FR-PRJ-008**: Require explicit UI confirmation for deletion; delete owned queries, results, attempts, and references when those features exist, not other projects' records.

### Non-Functional Requirements

- **NFR-PRJ-001**: No credential values appear in browser assets, API responses, or application logs.
- **NFR-PRJ-002**: All project operations are keyboard accessible, fields have labels, and errors are conveyed as text rather than color alone.
- **NFR-PRJ-003**: Proposed local CRUD p95 latency is below 500 ms over 100 requests with 100 stored projects, excluding application startup and external services. Reference environment must be approved before measurement.

### Key Entities

Project: identity, name, question, keywords, optional years, maximum paper count,
created/updated timestamps. Project owns future queries, results, attempts, and references.

## Success Criteria

- **SC-PRJ-001**: AC-PRJ-001–007 pass against persisted storage and the browser.
- **SC-PRJ-002**: Every boundary and invalid-input case in FR-PRJ-002–005 is tested; failed writes preserve values.
- **SC-PRJ-003**: Project persistence passes an actual PostgreSQL restart/reconnect scenario, not SQLite alone.
- **SC-PRJ-004**: NFR-PRJ-001–003 have recorded audit, keyboard, and latency evidence.

## Assumptions

Local single-user deployment, no account system, no migration from the old application.
Validation mostly retains baseline behavior; required 1–250 paper count and deletion
confirmation are proposed product decisions. See `../../docs/scope.md`.
