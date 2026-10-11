# Feature Specification: Durable saved references

**Feature Branch**: Proposed `005-saved-references` (not created)
**Created**: 2026-10-11
**Status**: Draft — human approval required
**Input**: Retain a minimal project reading list from retrieved papers.

## User Scenarios & Testing

### User Story 1 — Save and reopen references (Priority: P1)

**Why this priority**: Discovery should produce a durable, useful reading list.
**Independent Test**: Seed project results, save one paper, replace results, and restart.
**Acceptance Scenarios**:
1. **Given** a search paper, **When** I save it twice, **Then** exactly one reference exists (AC-REF-001).
2. **Given** a saved reference, **When** later searches replace results and the application restarts, **Then** its saved metadata remains accessible (AC-REF-002).
3. **Given** a saved reference, **When** I remove it, **Then** the paper stays in search results and other projects are unaffected (AC-REF-003).
4. **Given** a paper not associated with this project, **When** I try to save it here, **Then** the operation is rejected (AC-REF-004).

### Edge Cases

Concurrent duplicate saves; missing DOI; provider metadata changes; removal after later
searches; project deletion; cross-project IDs; reference save while search is pending.

## Requirements

### Functional Requirements

- **FR-REF-001**: Save a reference only from a paper currently associated with the requested project's results.
- **FR-REF-002**: Store a provider-derived metadata snapshot, source identity, project ID, and save timestamp independently of current search associations.
- **FR-REF-003**: Saving the same source identity twice in one project MUST be idempotent, including concurrent requests; use a persistence uniqueness constraint.
- **FR-REF-004**: List saved references by case-folded title then source identity; show available authors/year/DOI/source and safe publication links.
- **FR-REF-005**: Later searches/provider refreshes MUST NOT silently change saved snapshots or delete them.
- **FR-REF-006**: Remove references independently of search papers; delete references when their owning project is explicitly deleted.
- **FR-REF-007**: Scope every read/delete/save to its project. Unknown/cross-project IDs return not found; saves are rejected during an active search, while reads/removals remain permitted.
- **FR-REF-008**: Do not support manual citations, metadata editing, notes, reading status, or citation numbering in this slice.

### Key Entities

Reference: project ownership, source identity, immutable scholarly snapshot and savedAt.
It is not dependent on a currently present ProjectPaper association.

## Success Criteria

- **SC-REF-001**: AC-REF-001–004 pass with PostgreSQL uniqueness/concurrency checks and browser tests.
- **SC-REF-002**: The complete scope acceptance journey passes including replacement and restart.
- **SC-REF-003**: Cross-project operations cannot disclose or mutate another project's references.

## Assumptions

Depends on 003; ranked final demonstration also needs 004. Snapshot semantics and
provider-identity-only duplicate detection are deliberate simplifications needing approval.
