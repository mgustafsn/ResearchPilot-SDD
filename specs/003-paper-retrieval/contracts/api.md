# Retrieval API/UI contract — proposal

**Status**: Approved by the user on 2026-10-19. Same-origin, local, single-user
JSON API. Existing project and query routes remain compatible except that project/query
mutations return a conflict while that project's retrieval attempt is active.

## Models

`PaperOutput` contains only provider-derived metadata:
`{id, provider, providerId, doi?, title, abstract?, authors?, publicationYear?,
publicationDate?, venue?, citationCount?, sourceUrl, publicationUrl?, fullTextUrl?,
isOpenAccess?}`. Missing optionals are absent/null; access `null` means unknown.

`SearchOutput` contains `{searchRunId, status, provider, startedAt, finishedAt?,
rawFetchedCount, skippedCount, duplicateCount, queriesUsed, queriesUnused, papers}`.
No raw OpenAlex object, request URL, API credential, project secret, or project question/
keywords are returned in provider diagnostics.

## Routes

| Route | Success | Behavior |
|---|---|---|
| `POST /api/projects/{project_id}/search` | 200 `SearchOutput` | Capture project/query/filter snapshot; begin one bounded explicit search; atomically replace results after complete success |
| `GET /api/projects/{project_id}/papers` | 200 current-results output | Return current papers in stable display order and latest attempt status; never triggers retrieval |

No public generic provider route, polling/history UI, export, PDF/full-text route,
ranking/score field, reference mutation, or multi-provider selection is added. POST
may remain pending while the bounded provider operation runs; browser shows pending
state and discards stale view responses.

## Errors

Use `{error:{code,message,fields:[]}}` with fixed safe messages. Proposed outcomes:

| Status/code | Meaning |
|---|---|
| 404 `NOT_FOUND` | Project does not exist |
| 409 `SEARCH_ACTIVE` | Another nonexpired attempt is active; edits/deletion/search are blocked |
| 409 `SEARCH_STALE` | Attempt ownership/lease was superseded; no result write accepted |
| 422 `NO_ENABLED_QUERIES` | No stored enabled query at snapshot time |
| 502 `PROVIDER_INVALID_RESPONSE` | Invalid/incomplete OpenAlex envelope or unusable provider response |
| 503 `PROVIDER_UNAVAILABLE` | OpenAlex rate-limit/HTTP/transport failure |
| 504 `PROVIDER_TIMEOUT` | Per-request or whole-attempt deadline elapsed |
| 503 `STORAGE_UNAVAILABLE` | Database operation/commit failed; old associations remain |

Exact codes/status mapping, retry behavior (proposed none), and precedence are pending
plan/contract approval. Do not leak upstream body, URL/query, exception, SQL, or key.

## UI behavior

- Search is an explicit user action. Disclose immediately beside the control that
  enabled query text and applied year filters are sent to OpenAlex (not OpenAI); the
  project question/keywords are not sent. No request on page load or edit.
- Display visible pending/success/failure, actual queries used/unused, returned,
  skipped and duplicate counts, source metadata and safe links. State that access
  status may be unknown. Render text with text nodes only and permit only `http` and
  `https` links.
- While a search is active, project/query edit/delete and another search show a clear
  conflict. A navigation away/back cannot let an older response repaint a different
  project. On failed retrieval, current results remain visible and unchanged.
- A successful empty result shows an empty state and removes prior current-result
  associations; future saved references remain separate and unchanged.
