# Feature 003 data model — proposal

All scholarly facts are mapped from OpenAlex by `PaperProvider`. None of these
models may accept LLM-generated metadata. PostgreSQL migration 003 is additive;
migrations 001/002 remain immutable. Proposed fields and relationships are from the
approved plan; implementation and database tests remain pending.

## Entities

### Paper — provider-owned normalized work

| Field | Proposed type | Rules/source |
|---|---|---|
| `id` | UUID | Local primary key |
| `provider` | text | `openalex` for this slice |
| `provider_id` | text | Required OpenAlex work ID; unique with provider |
| `doi` | text nullable | Normalized DOI from provider; indexed, not globally unique |
| `title` | text | Required, trimmed; missing/blank provider titles are skipped |
| `abstract` | text nullable | Reconstructed from OpenAlex inverted index; optional and bounded |
| `authors` | JSONB array of strings | Provider authors in byline order; optional; OpenAlex list responses expose up to 100 |
| `publication_year` | integer nullable | Provider year, if valid |
| `publication_date` | date nullable | Provider ISO date, if valid |
| `venue` | text nullable | Primary source display name |
| `citation_count` | nonnegative integer nullable | OpenAlex `cited_by_count` |
| `source_url` | text | Canonical OpenAlex work URL, http/https only |
| `publication_url` | text nullable | Provider's primary location landing URL, http/https only |
| `full_text_url` | text nullable | Provider's best OA landing/PDF URL, http/https only; URL only, no download |
| `is_open_access` | boolean nullable | OpenAlex status; null stays unknown |
| `updated_at` | timestamptz | Last successful provider refresh |

Store normalized provider facts only; do not persist raw response envelopes or
publisher full-text bytes. On successful later retrieval, a richer normalized record
may update the shared provider-owned row. Project ranking/relevance and attempt state
do not live on `Paper`.
After successful result replacement, provider rows with no current project association
may be removed; future saved references are independent immutable snapshots.

### ProjectPaper — current results association

| Field | Proposed type | Rules |
|---|---|---|
| `project_id` | UUID FK | Required; cascade with project deletion |
| `paper_id` | UUID FK | Required; points to provider-owned `Paper` |
| `search_run_id` | UUID FK | Successful attempt that last established the association |
| `ordinal` | integer | Stable output order for the current result set; unique within project |

Primary key is `(project_id, paper_id)`. Replace all rows for one project in one
transaction only after all enabled-query requests succeed and ownership is current.
An empty successful attempt removes all current associations. Future saved references
must not depend on this association and are not implemented in feature 003.

### SearchRun — durable attempt and ownership record

| Field | Proposed type | Rules |
|---|---|---|
| `id` | UUID | Attempt identity |
| `project_id` | UUID FK | Required; project owner |
| `input_snapshot` | JSONB | Question/keywords, ordered enabled queries and allocations, year bounds, raw limit, provider, timestamp; no secret |
| `status` | text enum/check | `pending`, `succeeded`, `failed` |
| `ownership_token` | UUID | Random token captured by this worker |
| `lease_expires_at` | timestamptz | Proposed 150 seconds after start; expired owner cannot commit |
| `started_at`, `finished_at` | timestamptz | UTC lifecycle timestamps |
| `raw_fetched_count` | nonnegative integer | Provider records actually returned within allocation |
| `skipped_count` | nonnegative integer | Invalid/missing-title provider records skipped |
| `duplicate_count` | nonnegative integer | Valid duplicate records removed |
| `queries_used`, `queries_unused` | JSONB arrays | Texts/allocations used or zero-allocation entries; avoid secret/config data |
| `error_code` | text nullable | Fixed safe category only, no raw error/body/query |

At most one `pending` row per project (partial unique index). All operations lock the
project row first. An expired pending attempt is marked failed/interrupted before a
new owner starts or current-results status is returned. A late worker must match both
token and unexpired lease before it
can persist papers, replace associations, or mark its run successful.

## Relationships and state transitions

```text
Project 1 ── * SearchRun
Project 1 ── * ProjectPaper * ── 1 Paper
```

```text
pending ──all requests + validation + atomic commit──> succeeded
pending ──provider/validation/storage/lease failure────> failed
```

`SearchRun` history remains separate from current `ProjectPaper` results. Failed
attempts are auditable but never change previous result associations or independent
saved-reference snapshots. Repeated provider IDs update one `Paper`; duplicate
records are merged deterministically before any database writes.
