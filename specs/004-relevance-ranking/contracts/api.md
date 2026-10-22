# API and UI contract: local ranking

**Status**: Approved with the plan by the user on 2026-10-21 (reply: “I approve”); tasks/implementation subsequently authorized (reply: “Start”). Extends feature-003 responses; no new public route required.

## POST /api/projects/{project_id}/search

Existing explicit user action, request body and OpenAlex data disclosure unchanged.
After retrieval/deduplication, rank locally before atomic replacement. Response
keeps all existing fields and adds:

- Each `papers[]`: `embeddingScore` (number 0–1) and `rankingProvenance` (object;
  fields in [data model](../data-model.md)). On a new nonempty successful search,
  every paper has both. Ordered descending score, then case-folded title and source.
- Attempt: `rankingProvenance` (run-level object or null for empty/legacy/pending/
  failed attempt). Successful empty search never requires a local model.

No raw vectors, tokens, native exception text, local paths, or configuration secrets
in browser JSON. Hashes/model versions are audit provenance, not scientific evidence.

## GET /api/projects/{project_id}/papers

No model invocation or network access. Return persisted scores/order/provenance with
the existing current papers and latestAttempt structure. Legacy 003 papers have
`embeddingScore: null`, `rankingProvenance: null`. A latest failed attempt must not
relabel current results as belonging to it; per-paper searchRunId identifies the
successful run. Continue lazy expired-lease recovery.

Top-level `rankingProvenance` additionally identifies the successful current-result
run (null for legacy/empty results), independently of latestAttempt. This retains
the context-truncation/model disclosure even when a later attempt fails.

## Errors

Use existing `{error: {code, message, fields: []}}` envelope; retain 003 error codes.

| HTTP | Code | Meaning |
|---|---|---|
| 503 | EMBEDDING_MODEL_MISSING | Local model absent; run explicit setup; previous results kept |
| 503 | EMBEDDING_MODEL_INVALID | Installation failed integrity/config checks; previous results kept |
| 503 | EMBEDDING_BUSY | Another local ranking job is active; retry manually later |
| 504 | EMBEDDING_TIMEOUT | Local ranking exceeded deadline; previous results kept |
| 502 | EMBEDDING_INVALID_RESPONSE | Vector/provenance validation failed; previous results kept |
| 503 | EMBEDDING_UNAVAILABLE | Safe generic local inference failure; previous results kept |
| 504 | SEARCH_TIMEOUT | Overall pre-commit pipeline deadline exceeded; previous results kept |

Existing 409 active/stale, storage errors, retrieval errors and mutation guards
remain. Never blame OpenAlex for local model failures. Errors after attempt creation
persist a matching safe terminal code under current ownership; canceled/expired
workers must not change newer attempts. Error recording itself may fail during DB
outage; lazy expiry remains the recovery mechanism, not a false durability promise.

## UI

Pending lasts through retrieval and ranking, with current old results still visible
until complete success. Show new success/failure through existing status controls.
For each ranked result show `Embedding similarity: XX.X%`; retain all papers,
including 0%. Display model/revision and explanation: locally computed, provisional
calibrated cosine, not probability/quality, English focus, inputs limited to the
first 256 model tokens. Flag truncated question/paper inputs from stored provenance.
Legacy score null displays “Not ranked — search again to rank locally.”
Render all metadata/errors/model labels as text, retain safe http/https links and
keyboard/focus support, reject stale navigation callbacks. Do not add ranking
toggles, cloud fallback, history polling, filters, references, or setup-download UI.
