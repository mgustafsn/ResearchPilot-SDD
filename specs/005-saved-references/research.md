# Feature 005 research and decisions

**Status**: Supporting design approved with `plan.md` by the user on 2026-10-22.

## Existing implementation findings

- OpenAlex papers are normalized into the strict `Paper` model in
  `backend/researchpilot/paper_domain.py`. It retains provider/provider ID, DOI,
  title, abstract, authors, publication date/year, venue, citation count, source
  URL, publication URL, full-text URL, and open-access state. URL and text
  normalization already occurs at the provider boundary.
- `papers` holds shared provider facts. `project_papers` links current results to a
  project and is replaced on a successful search. A saved reference therefore
  needs its own copied snapshot and must not depend on either row remaining linked.
- Retrieval and query services lock the `projects` row before checking pending
  attempts or changing project-scoped state. Reuse this lock order for saves so a
  save and search start cannot pass each other unnoticed.
- API errors use structured codes/messages and project services raise typed
  not-found errors. Static UI data is rendered using text nodes; provider links
  already use safe URL normalization.
- PostgreSQL migrations are additive, versioned SQL files. Existing tests protect
  cleanup targets and use a guarded disposable database; the new table can join
  that approved test cleanup list.

## Decisions

### Snapshot storage

Copy the normalized provider facts into a JSONB object in a new `saved_references`
table. Keep provider and provider ID in indexed columns for uniqueness and lookup;
the JSON snapshot repeats those values and SQL checks their agreement and object
shape. Validate the whole snapshot through strict `Paper` parsing on write and
read. Omit project-specific `embeddingScore` and ranking provenance: they describe
a particular result set and are not scholarly metadata. Do not store vectors.

The saved row has no FK to `papers` or `project_papers`. Its only parent FK is the
owning project with `ON DELETE CASCADE`. Thus result replacement and provider-row
refresh have no path to rewrite or delete the saved snapshot, while explicit
project deletion removes its list.

### Idempotency and locking

Use `UNIQUE(project_id, provider, provider_id)` as the durable duplicate rule.
For save, lock the project row first, verify it exists, check for a live pending
search, then read the requested current project-paper association and its normalized
provider row. Insert the copied snapshot. On a duplicate, return the existing
unchanged reference. A unique constraint protects against races even if a future
write path does not acquire the project lock.

When a pending attempt's lease has expired, mark it failed under the project lock
before deciding whether save may proceed, following retrieval's existing stale
ownership behavior. The old worker will fail its ownership check. An unexpired
pending attempt rejects the save with `SEARCH_ACTIVE`.

List and removal also verify the project under the project-row lock but do not
reject an active search. Removal is a project-scoped delete; a reference ID owned
by another project is indistinguishable from an unknown ID and returns not found.

### Ordering and response behavior

Return references sorted by Python `str.casefold()` of snapshot title, then provider
and provider ID. The list is short for the intended single-user reading-list
journey; no arbitrary cap/pagination is introduced. A first save returns HTTP 201;
an idempotent repeat returns HTTP 200 with the same immutable reference body. A
successful removal returns 204. Unknown projects/references and papers not in the
current project result set return sanitized 404 responses.

### UI

Add a saved-references section to the selected project. Current result cards expose
one Save action; already-saved results show a saved state. The saved list presents
provider metadata and safe source/publication links with a Remove action. Use text
rendering and the existing same-origin JSON client. No free-form citation field,
metadata editor, notes, reading state, citation numbering, or export action.

### Performance and dependencies

Reuse current dependencies. No approved Feature 005 performance budget exists;
functional, migration, concurrency, and browser acceptance are sufficient for this
plan. Do not claim a latency target from a different feature's measurements.

## Alternatives considered

- **Keep only a foreign key to `papers`**: rejected because it does not preserve a
  self-contained metadata snapshot if provider data changes or provider records
  are later cleaned up.
- **Tie references to `project_papers`**: rejected because successful searches
  replace that association and would remove the reading list.
- **Reuse JSON fields from current API results without strict validation**:
  rejected because browser/API input must not be allowed to invent provider facts.
- **Add a generic library/repository abstraction or a new provider protocol**:
  rejected because the existing Paper model and service/SQLAlchemy patterns already
  cover this single-provider slice.
- **Store ranking score with the saved reference**: rejected because ranking is
  project/search-specific algorithmic state, not provider-derived metadata.
