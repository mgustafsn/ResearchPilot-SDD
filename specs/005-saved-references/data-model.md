# Data model: saved references

**Status**: Supporting design approved with `plan.md` by the user on 2026-10-22.

## SavedReference

One immutable provider-derived metadata snapshot saved to one project.

| Field | Storage | Rule |
|---|---|---|
| id | UUID primary key | Stable reference identifier |
| project_id | UUID FK to projects, cascade delete | Owning project |
| provider | TEXT | Must match the normalized Paper snapshot; currently `openalex` |
| provider_id | TEXT | Nonblank, bounded provider identity; must match snapshot |
| paper_snapshot | JSONB object | Strictly validated `Paper` provider facts |
| title_sort_key | TEXT | Python case-folded title used to reproduce list ordering |
| saved_at | TIMESTAMPTZ | Save time, assigned by the server |

Unique constraint: `(project_id, provider, provider_id)`. There is deliberately
no FK to `papers` or `project_papers`; those rows are mutable/current-search state,
while the saved JSON object is an independent snapshot. Deleting a project cascades
to its references.

`paper_snapshot` contains the normalized `Paper` fields: provider, provider ID,
DOI, title, abstract, authors, publication year/date, venue, citation count, source
URL, publication URL, full-text URL, and open-access state. No query text, raw
OpenAlex response, ranking score/provenance, vector, or user-authored citation
metadata is included. Application reads parse the JSON through the strict `Paper`
model before returning it.

## State transitions

```text
Current project result --explicit save--> SavedReference snapshot
SavedReference --later search/provider refresh--> unchanged
SavedReference --explicit remove--> deleted
Project --explicit project deletion--> SavedReference cascade deletion
```

The database row is not updated in place. Saving an already-saved source returns
the existing row without refreshing its snapshot. Provider refresh and search
result replacement never write the saved table.

## Transaction and concurrency rules

- Every operation locks/verifies the owning project before accessing its rows.
- Save checks an unexpired pending search and returns `SEARCH_ACTIVE` if one exists.
- A stale pending search lease is marked failed while holding the project lock;
  stale search completion remains rejected by the existing ownership token.
- Save resolves `paperId` only through the requested project's current
  `project_papers` association. Cross-project IDs and unknown IDs return the same
  not-found response.
- Project-row locking serializes concurrent same-project changes; the unique
  constraint is the final defense against duplicate snapshots.
- List and removal remain allowed during active search. Removal is scoped by both
  project ID and reference ID.

## Migration

Add `migrations/005_saved_references.sql`; do not edit migrations 001–004. The
migration creates the table, JSON-object/provider-identity consistency checks,
unique constraint and project/list index. It has no backfill: existing current
papers are not automatically saved. Migration tests must cover fresh setup,
upgrade from 004, repeated startup, transactional rollback, uniqueness, project
cascade and restart durability.
