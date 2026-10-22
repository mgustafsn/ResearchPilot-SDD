# Data model: local ranking

**Status**: Approved supporting design with the plan on 2026-10-21; tasks/implementation subsequently authorized (reply: “Start”). Additive migration 004 only.

## Provider facts

`papers` stays unchanged. Model-generated scores/provenance MUST NOT be written
to title, abstract, authors, DOI, dates, citation counts or URLs.

## ProjectPaper

Keep existing project/paper/run keys and ordinal; add:

| Column | Type | Rule |
|---|---|---|
| embedding_score | NUMERIC(7,6), nullable | Between 0 and 1 inclusive; null only for legacy unranked rows |
| ranking_provenance | JSONB object, nullable | Present iff score present; validated structured schema below |

Per-paper provenance includes `modelId`, `modelRevision`, `dimension`,
`scoringVersion` (`calibrated-cosine-v1`), `inputVersion` (`ranking-input-v1`),
`inputHash`, `tokenHash`, `tokenCount`, `truncated`, `maxTokens` (256), and
`searchRunId`. Hashes are lowercase SHA-256 hex; dimension positive, tokens 1–256.
Versioned service validation enforces all fields, 384 dimensions for local adapter,
finite bounded score and correct association/run identity. SQL enforces paired
nullability, JSON object shape and numeric bounds. No vector storage.

`ordinal` records approved score/title/source ordering; it remains the GET order.
Existing rows migrate as null/null, never as fabricated 0% similarity.

## SearchRun

Add nullable `ranking_provenance` JSONB object. On new nonempty successful attempts:
model identity/revision, dimension, scoring/input version, maxTokens, runtime package
versions, context text/token hashes/count/truncation, rankedPaperCount and durationMs.
All per-paper provenance agrees with this run. Persist no model path or raw tokens.
Pending/failed/legacy/empty-success attempts may have null ranking provenance; never
claim a model ran on an empty successful search. Existing input snapshot retains
question/keywords unchanged. No lifecycle enum change.

Current result provenance belongs to the successful associations, not the latest
failed attempt. API must not imply new failed-search context produced old scores.

## Transient entities

- `EmbeddingInput`: stable input ID and exact normalized text; context first, then
  deduplicated papers. Request-bound only, never logged.
- `EmbeddingBatch`: model identity/revision/dimension/versions and ordered items
  containing ID, vector, token hash/count/truncation. Vendor-free validated schema.
- `RankedPaper`: provider Paper plus score/input hashes/provenance. No mutation of
  the original normalized metadata; associations own project-specific ranking.

## Transitions and invariants

Pending retrieval → local ranking (no new persisted stage) → atomic success; errors
mark failed and leave old associations/metadata/scores untouched. The lease and
ownership token gate every final write. Successful empty retrieval skips inference
and replaces results with empty. No DB lock is held over local child execution.

Migration remains transactional/repeatable, with fresh-schema, upgrade from 003,
legacy-result preservation, rollback-on-error and restart tests. Existing guarded
test cleanup table list suffices; no new table is needed. Never run destructive
fixtures against the application DB.
