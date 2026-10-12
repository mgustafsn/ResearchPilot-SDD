# Project API contract — approved

Re-reviewed on 2026-10-12 against the approved 001 specification and constitution
2.0.0. Approved by the user on 2026-10-12 (reply: "approve plan and API contract");
approval alone does not establish implementation or acceptance. This API is now
implemented for slice 001; actual evidence and remaining review gates are recorded
in `../../../docs/evidence-log.md`.

Same origin, prefix `/api`, JSON requests/responses. No authentication in local scope.
Bind server to loopback; this is not a secure public-deployment contract.

## Schemas

ProjectInput:

```json
{
  "title": "LLMs in software engineering",
  "researchQuestion": "How are LLMs used in software testing?",
  "keywords": ["LLM", "software testing"],
  "yearFrom": 2022,
  "yearTo": 2026,
  "maxPaperCount": 100
}
```

Required: title, researchQuestion, maxPaperCount. keywords defaults to [], years to
null. Rules are in spec FR-PRJ-002–005. Unknown keys rejected. JSON booleans MUST NOT
be accepted where an integer is required. PUT uses the complete input schema.

ProjectOutput: all normalized ProjectInput fields plus id (UUID), createdAt and
updatedAt (ISO-8601 UTC). No credentials or status fields.

Error envelope: `{ "error": { "code": "...", "message": "...", "fields": [] } }`.
Validation fields contain `{ "field": "title", "message": "..." }` entries.
Messages are sanitized; never include raw input, SQL, exception strings, or secrets.
Handle framework validation errors consistently with this envelope.

## Operations

| Method / path | Success | Errors |
|---|---|---|
| GET /api/projects | 200, ProjectOutput array; empty [] | 503 STORAGE_UNAVAILABLE |
| POST /api/projects | 201, ProjectOutput | 422 VALIDATION_ERROR; 503 STORAGE_UNAVAILABLE |
| GET /api/projects/{id} | 200, ProjectOutput | 422 invalid UUID; 404 NOT_FOUND; 503 |
| PUT /api/projects/{id} | 200, ProjectOutput | 422; 404; 503 |
| DELETE /api/projects/{id} | 204, no body | 422; 404; 503 |

GET list order: updatedAt descending, UUID ascending for ties. Mutations are atomic;
failed writes do not alter persisted data. Deleting an absent project returns 404.
UI confirmation is not an additional server flag.

The UI calls `title` "Project name", offers paper count 100 initially, and provides
labeled keyboard-accessible controls for all project operations. Failed saves keep
form values visible alongside text errors. Before DELETE, warn that the project and
its contents will be permanently removed with no undo; cancellation sends no request.
Browser assets/API responses contain no environment secrets. User text is rendered
as text rather than HTML. Backend error logging excludes raw database exceptions,
SQL parameters, database URLs, and credentials.

Feature 003 will amend PUT/DELETE to return 409 SEARCH_ACTIVE during an owned active
attempt. This future behavior is not required in the first implementation slice.

Tests must cover each route, response shape, boundary validation, empty collections,
unknown IDs, sanitized database failures, persistence and rollback. Link those tests
to FR-PRJ IDs rather than relying on the original application's schemas.
