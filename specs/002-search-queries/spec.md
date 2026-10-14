# Feature Specification: User-controlled search queries

**Feature Branch**: Proposed `002-search-queries` (not created)
**Created**: 2026-10-11
**Status**: Specification/plan/contracts approved on 2026-10-12; tasks and implementation authorized on 2026-10-13. Manual-query increment implemented and verified; suggestion generation and full feature acceptance remain pending.
**Input**: Retain description-driven query suggestions and user control; exclude categorization.

## Clarifications

### Session 2026-10-12

- Q: When you generate fresh suggestions, should they replace only untouched AI queries, while preserving manual queries and any suggestions you edited or enabled/disabled? → A: Yes. Replace only untouched generated queries; preserve manual queries and generated queries whose text or enabled state the user changed, retaining their text and enabled state.
- Q: If fresh AI suggestions duplicate queries you’ve preserved, should we skip those duplicates even if fewer than three new queries remain? → A: Yes. Validate a batch of 3–6 unique normalized suggestions before merging, then skip suggestions matching preserved queries. Successful regeneration may add 0–6 new queries; the combined list can exceed six, and preserved text/enabled state remains unchanged.
- Q: Should each project allow at most 20 saved queries? → A: Yes. Count enabled and disabled queries together; reject manual additions beyond 20 with a readable error and no stored changes. Regeneration fills only available slots after preserving user-owned queries, without removing those queries to make room.
- Q: When you change a project’s research question or keywords, should existing queries stay unchanged until you explicitly regenerate suggestions? → A: Yes. Retain every saved query and enabled state, show a notice that suggestions may need refreshing, and make no automatic suggestion-provider call or query deletion.
- Q: Should a deleted query be allowed to reappear when you explicitly generate fresh suggestions later? → A: Yes. Delete the stored entry without retaining a text-suppression history; a later explicit generation may suggest it again. Disabling instead preserves the user-owned entry and excludes it from later searches. Deletion during pending generation changes the revision and prevents that stale response from overwriting the newer list.

## User Scenarios & Testing

### User Story 1 — Review suggestions (Priority: P1)

As a researcher I can generate short suggestions, inspect them, and decide what to search.
**Why this priority**: The long research description is context, not a provider query.
**Independent Test**: With a saved project and fake suggestion provider, generate and reload.
**Acceptance Scenarios**:
1. **Given** a project, **When** generation succeeds with a validated batch of 3–6 unique short suggestions, **Then** untouched generated queries are replaced and nonduplicate suggestions persist alongside preserved user-owned queries. If all suggestions match preserved queries, zero new queries are added without failing generation (AC-QRY-001).
2. **Given** saved queries, **When** generation times out or returns invalid output, **Then** the list is unchanged and a readable error appears (AC-QRY-002).

### User Story 2 — Control the query list (Priority: P1)

**Why this priority**: The user must control the actual search inputs.
**Independent Test**: Add/edit/toggle/delete queries without a live LLM or search.
**Acceptance Scenarios**:
1. **Given** suggestions, **When** I edit one, change another's enabled state, and add a manual query, **Then** all user-controlled queries retain their text and enabled state through regeneration and reopening (AC-QRY-003).
2. **Given** disabled queries, **When** search runs in feature 003, **Then** only enabled query texts are sent (AC-QRY-004).
3. **Given** no enabled queries, **When** I request search in feature 003, **Then** validation prevents a provider call (AC-QRY-005).

### Edge Cases

Empty output; duplicate normalized texts; all queries disabled; malformed structured
response; deletion during generation; project edits while a suggestion request is pending;
20 saved queries including disabled queries; no available slots after preserving
user-owned queries; a valid batch with more nonduplicate suggestions than free slots.

## Requirements

### Functional Requirements

- **FR-QRY-001**: Generate a batch of 3–6 unique normalized suggestions using the question and keywords as context; request a structured list and validate before merging or persisting. The 3–6 count applies to the validated suggestion batch, not the combined stored list.
- **FR-QRY-002**: Each query MUST collapse whitespace and contain 1–160 characters; equivalent case-folded texts MUST NOT be duplicated within a project. After batch validation, skip suggestions matching preserved queries without changing preserved text or enabled state. Regeneration may add 0–6 new queries, and the combined stored list may exceed six.
- **FR-QRY-003**: Users MUST add, edit, delete, enable, and disable queries; persist their changes. New suggestions/manual queries default to enabled.
- **FR-QRY-004**: Successful regeneration MUST replace only untouched generated queries, rather than append indefinitely. Manual queries and generated queries whose text or enabled state the user changes become user-owned and MUST survive regeneration with their stored text and enabled state unchanged. User ownership persists even if the user later restores the original text or enabled state.
- **FR-QRY-005**: Failed regeneration MUST leave the entire saved list unchanged. Manual query entry remains available; no silent fallback is generated.
- **FR-QRY-006**: Long research descriptions MUST NOT be searched directly. The enabled stored query list is the authoritative search input.
- **FR-QRY-007**: Generation uses a snapshot; if the project or query-list revision changes before persistence, reject the stale write with a conflict and preserve newer data.
- **FR-QRY-008**: A project MUST contain at most 20 saved queries, counting enabled and disabled entries together. Reject manual additions beyond this limit with a readable error and no stored changes. Successful regeneration MUST preserve user-owned queries first, remove only untouched generated queries, skip duplicate suggestions, and fill remaining slots in validated batch order up to the limit. Never remove preserved queries to make room; zero available slots is not a generation failure.
- **FR-QRY-009**: When the project research question or keywords change, MUST retain all saved queries and their enabled states and display a notice that suggestions may need refreshing. MUST NOT automatically regenerate or delete queries. Only an explicit user generation request may refresh untouched suggestions; manual query use remains available. The notice persists across reopening until successful generation for the current question/keywords; failed or stale generation MUST NOT clear it.
- **FR-QRY-010**: Deleting a query MUST remove its stored entry and release its capacity slot, without retaining a text-suppression history. A later explicit generation MAY suggest the same normalized text again. Disabling instead MUST retain the user-owned query and disabled state through regeneration. Deletion during pending generation MUST change the query-list revision so the stale write is rejected under FR-QRY-007.

### Key Entities

SearchQuery: ID, project ID, text, enabled flag, origin, user-owned flag.
Project/query-list revision: concurrency identity used to reject stale generation.
Query context state: identifies the question/keywords used for successful generation
and whether a later context change requires a durable refresh notice.

## Success Criteria

- **SC-QRY-001**: AC-QRY-001–003 pass with fake suggestion providers, including invalid-output and timeout injection. Query-selection rules supporting AC-QRY-004/005 are verified independently with stored-query fixtures; actual search/provider-call integration acceptance belongs to feature 003.
- **SC-QRY-002**: Regeneration preserves edited/manual texts and enabled state in all relevant regression fixtures.
- **SC-QRY-003**: Query-selection fixtures return exactly enabled stored query texts and reject an empty enabled list, without substituting the research description. Scholarly-provider spy verification for AC-QRY-004/005 is completed in feature 003; no scholarly retrieval route or provider is implemented in feature 002.
- **SC-QRY-004**: Boundary fixtures verify the 20-query limit, counting disabled entries; rejected manual additions leave data unchanged, and regeneration retains every user-owned query while filling only available slots.
- **SC-QRY-005**: Context-change fixtures verify unchanged query text/enabled state, no automatic provider calls, and a durable refresh notice that survives failed/stale generation and clears only after successful generation for the current context.
- **SC-QRY-006**: Deletion fixtures verify removal/capacity release, rejection of pending stale generation, and permitted reappearance in a later explicit generation; disabled queries remain preserved and disabled instead.

## Assumptions

Depends on approved feature 001, accepted by the user with BUG-PRJ-001 deferred on
2026-10-12; see `../../docs/known-issues.md`. Its outstanding audit evidence and
year-input nonconformance are not silently resolved by this feature. Only query
suggestion uses runtime LLM text generation.
Model and timeout choices are recorded in the separately approved plan. Failure
preservation differs from the original fallback behavior and is approved. Task
ordering and implementation still require their own gates; no live test is authorized.
