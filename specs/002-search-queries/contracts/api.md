# Query API/UI contract — approved

**Status**: Approved by the user on 2026-10-12 (reply: "approve query plan and contracts").
Not an implemented API or task/implementation authorization. Same-origin JSON under `/api`;
loopback/local single-user only. Existing project input/output/PUT/DELETE contract
is unchanged. Query state is never writable through project PUT.

## Models

QueryOutput: `{id, projectId, text, enabled, origin, userOwned}`. IDs are UUIDs,
text is normalized to 1–160 characters, enabled/userOwned are JSON booleans, origin
is manual/generated. Display order is ascending internal slot; no reorder endpoint.

QueryListOutput:

```json
{
  "projectId": "11111111-1111-4111-8111-111111111111",
  "revision": 7,
  "refreshRequired": false,
  "generationAvailable": false,
  "queries": []
}
```

revision is the parent's combined nonnegative mutation revision, not a timestamp.
generationAvailable exposes configuration availability only, never a key or raw
config/error. Availability does not guarantee successful provider authentication.

ManualAddInput: `{text, expectedRevision}` with optional enabled (default true).
ManualPatchInput: `{expectedRevision, text?, enabled?}`; require text or enabled,
reject unknown fields, accept only actual integers/booleans and nonblank normalized
text. origin/userOwned/projectId/id/slot/context/revisions are server-owned.

GenerateInput: `{expectedRevision}` only; the server captures current stored
question/keywords, not caller-supplied context or an LLM-generated paper list.

GenerationOutput extends QueryListOutput with:

```json
{
  "generationSummary": {
    "validatedCount": 6,
    "addedCount": 2,
    "replacedCount": 3,
    "duplicateSkippedCount": 3,
    "capacitySkippedCount": 1
  }
}
```

Summary counts describe the current validated batch/atomic merge, not quality or
scholarly metadata. Zero additions is still success. No raw provider payload/input
snapshot/API key or token-usage billing data is returned to the browser.

## Routes

| Route | Success | Behavior |
|---|---|---|
| GET /api/projects/{project_id}/queries | 200 QueryListOutput | Coherent saved list/revision/notice, never triggers generation |
| POST /api/projects/{project_id}/queries | 201 QueryListOutput | Add owned manual query, enabled by default |
| PATCH /api/projects/{project_id}/queries/{query_id} | 200 QueryListOutput | Edit/toggle, sticky ownership after actual changes |
| DELETE /api/projects/{project_id}/queries/{query_id}?expectedRevision=N | 200 QueryListOutput | Scoped deletion/capacity release; no suppression history |
| POST /api/projects/{project_id}/queries/generate | 200 GenerationOutput | One explicit bounded generation, validated atomic merge |

No search/retrieval or enabled-query export route is added in 002. The domain
selection operation for future 003 returns exactly enabled stored texts in slot
order, raises a typed empty-selection error, and never substitutes the description.

## Errors and precedence

Reuse `{error:{code,message,fields:[]}}` with fixed readable text. Field entries
name only known schema fields; never echo arbitrary keys/input, SQL, exception
strings, research context, credentials, or upstream response bodies.

| Status/code | Meaning |
|---|---|
| 422 VALIDATION_ERROR | Invalid UUID/text/types/missing revision, unknown fields, or PATCH with no changes supplied |
| 404 NOT_FOUND | Missing parent or scoped query; never disclose a query belonging to another project |
| 409 QUERY_REVISION_CHANGED | Expected revision is stale before a manual/generation operation |
| 409 GENERATION_STALE | Parent revision changed while provider was pending; reload current saved state |
| 409 QUERY_DUPLICATE | Manual addition/edit collides after casefold; no silent merge |
| 409 QUERY_LIMIT_REACHED | Manual addition exceeds 20 including disabled entries |
| 503 SUGGESTIONS_UNAVAILABLE | Missing/invalid configuration, upstream rate limit/busy/unavailable/auth failure; manual management still works |
| 504 SUGGESTIONS_TIMEOUT | Provider phase/total deadline exceeded before merge |
| 502 SUGGESTIONS_INVALID_OUTPUT | Refusal, truncation, malformed/oversized response, schema or normalized-batch failure |
| 503 STORAGE_UNAVAILABLE | Database/read/write/commit failure; no success before commit |

Validation occurs before application work. Under the parent lock: missing parent
first, then revision comparison, then scoped-query existence/uniqueness/capacity.
A deleted parent found after provider return is 404; no resurrection. Never
automatically retry 409/502/503/504 or issue a repair/fallback model call.

## UI contract

- Query controls and Generate are labeled/keyboard accessible. Show origin,
  ownership, text, enabled state, pending/result/error and durable refresh notice.
- Explain that Generate sends the saved question/keywords to OpenAI; no automatic
  call on load/project edit. Missing config disables Generate with readable text,
  not the manual controls. Never ask for or store the API key in the browser.
- While generation is pending, avoid duplicate clicks but allow manual edits/toggles,
  project navigation and deletion. Those changes can intentionally stale the response.
- Preserve failed/unsaved manual input, render every value as text, and retain
  user-owned states after success. Show duplicate/capacity skip counts clearly.
- Bind every response/error to its project/view epoch and revision. Ignore obsolete
  view responses; do not overwrite newer query state or reopen a deleted project.
  On conflict refresh saved state without clearing unsaved text.
- A context change retains all queries, makes no call, and shows a notice that
  persists until successful generation for the current context.
- Publication-year conversion remains unchanged; BUG-PRJ-001 stays deferred.
