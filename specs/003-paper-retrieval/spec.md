# Feature Specification: OpenAlex retrieval and deduplication

**Feature Branch**: Proposed `003-paper-retrieval` (not created)
**Created**: 2026-10-11
**Status**: Draft — human approval required
**Input**: Retrieve real papers from OpenAlex using approved stored queries.

## User Scenarios & Testing

### User Story 1 — Retrieve real papers (Priority: P1)

**Why this priority**: Real, attributable scholarly records are the product's core.
**Independent Test**: Seed a project/query list and use fixed OpenAlex HTTP responses.
**Acceptance Scenarios**:
1. **Given** enabled queries, **When** retrieval succeeds, **Then** normalized unique papers and source links are persisted and shown (AC-RET-001).
2. **Given** duplicate DOI/identity/title records, **When** results are processed, **Then** duplicates merge and the removed count is shown (AC-RET-002).
3. **Given** a successful empty response, **When** the attempt completes, **Then** an empty result state replaces old results but references survive (AC-RET-003).

### User Story 2 — Recover safely (Priority: P1)

**Why this priority**: Provider failures must not destroy useful work.
**Independent Test**: Seed old results and inject timeout, invalid response, and database failure.
**Acceptance Scenarios**:
1. **Given** previous results, **When** any query fails, **Then** the attempt fails and previous results/references remain unchanged (AC-RET-004).
2. **Given** an active search, **When** another search or project/query mutation is requested, **Then** it returns a conflict (AC-RET-005).
3. **Given** an expired search owner, **When** a newer attempt starts, **Then** late writes from the old attempt cannot replace its results (AC-RET-006).

### Edge Cases

Missing abstract/year/DOI; missing title; malformed records; provider rate limiting;
same normalized title with conflicting DOIs; expired worker; unsafe provider URLs;
enabled query count greater than paper budget.

## Requirements

### Functional Requirements

- **FR-RET-001**: Search OpenAlex only, through PaperProvider, using a snapshot of enabled queries, question/keywords, years, and paper limit.
- **FR-RET-002**: Divide the raw-record budget across enabled queries in stored order: floor(limit/count) each, with one extra for the first remainder queries. Queries with zero allocation are recorded as unused, not called. Show actual queries used.
- **FR-RET-003**: Normalize provider metadata: source identity/URL, title, abstract, authors, DOI, publication year/date, venue, citation count, publication/full-text links, and open-access status. Missing optional values stay absent; no LLM completion.
- **FR-RET-004**: DOI normalization trims/case-folds and removes doi:/resolver prefixes. Deduplicate by valid DOI, then provider identity, then normalized title. Distinct nonempty DOIs MUST NOT merge on title alone. Title normalization uses Unicode NFKD, ASCII folding, lowercase alphanumeric tokens, and collapsed whitespace, retaining baseline behavior pending collision review.
- **FR-RET-005**: Merge richer provider records and fill gaps without generating facts. Define richness and tie handling in the plan and test transitive identity bridging.
- **FR-RET-006**: Persist attempt ID, input snapshot, timestamps, status, ownership token/expiry, fetched/skipped/duplicate counts, and sanitized error. Show pending/success/failure; missing-title records are skipped and counted.
- **FR-RET-007**: Replace project result associations atomically only after the full enabled-query attempt succeeds and ownership remains current. Failure preserves all prior results and references.
- **FR-RET-008**: Permit one active attempt per project. Reject project/query edits, deletion, and a second search while active. Expired ownership releases the lock; late workers cannot commit.
- **FR-RET-009**: Display available source/publication/open-access links and metadata without asserting that missing access metadata means closed access.
- **FR-RET-010**: Treat source text as untrusted: render as text, permit only http/https links, never interpolate provider text into executable HTML.

### Key Entities

Paper: provider facts and identity. ProjectPaper: association to current results.
SearchRun: input snapshot, ownership, lifecycle and counts. References are separate.

## Success Criteria

- **SC-RET-001**: AC-RET-001–006 pass with mock HTTP, transactional storage, and browser tests.
- **SC-RET-002**: Result counts never exceed the project's raw-record budget; deduplication fixtures prove DOI precedence and transitive merging.
- **SC-RET-003**: Fault injection and concurrent attempts cannot erase old results or accept stale writes.
- **SC-RET-004**: Malicious metadata renders inertly and unsafe URL schemes cannot become clickable links.

## Assumptions

Depends on 001/002. All-query failure semantics simplify baseline partial success.
When feature 004 is added, ranking becomes part of the pre-commit pipeline and ranking
failure also preserves old results. Timeout/lease values need a reviewed technical plan.
