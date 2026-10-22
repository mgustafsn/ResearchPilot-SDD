# Saved-reference API contract

**Status**: Supporting design approved with `plan.md` by the user on 2026-10-22.

All routes are same-origin and project-scoped. The backend is the only authority
that constructs a snapshot; clients send only an existing result's `paperId`.

## `GET /api/projects/{projectId}/references`

Returns HTTP 200:

```json
{
  "projectId": "uuid",
  "references": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "provider": "openalex",
      "providerId": "W123",
      "doi": "10.1234/example",
      "title": "Provider-sourced title",
      "abstract": null,
      "authors": ["Author Name"],
      "publicationYear": 2024,
      "publicationDate": "2024-03-01",
      "venue": "Journal Name",
      "citationCount": 12,
      "sourceUrl": "https://openalex.org/W123",
      "publicationUrl": "https://publisher.example/paper",
      "fullTextUrl": null,
      "isOpenAccess": false,
      "savedAt": "2026-10-22T12:00:00Z"
    }
  ]
}
```

Fields with no provider value are `null`; authors is an array. Results are ordered
by `title.casefold()`, provider, and provider ID. Return HTTP 404 `PROJECT_NOT_FOUND`
for an unknown project. Listing is permitted while a search is pending.

## `POST /api/projects/{projectId}/references`

Request:

```json
{"paperId": "uuid"}
```

Resolve this ID only through the current project-paper association, then copy the
provider-normalized Paper snapshot. Do not accept paper metadata from the request.
Return the same flat reference shape as GET. Return HTTP 201 for the first save
and HTTP 200 for a duplicate save; both responses identify the same saved record,
and a duplicate never refreshes its snapshot.

Errors use the existing `{error: {code, message, details?}}` schema:

| HTTP | Code | Condition |
|---:|---|---|
| 404 | `PROJECT_NOT_FOUND` | Project does not exist |
| 404 | `PAPER_NOT_FOUND` | ID is absent from this project's current results, including cross-project ID |
| 409 | `SEARCH_ACTIVE` | An unexpired search owns the project |
| 500 | `STORAGE_ERROR` | Sanitized persistence failure |

A failed save leaves the current search results and saved list unchanged. On an
expired pending lease, mark the attempt failed under the project lock before
proceeding; its stale worker cannot commit.

## `DELETE /api/projects/{projectId}/references/{referenceId}`

Delete only where both IDs match. Return HTTP 204 on success, or HTTP 404
`PROJECT_NOT_FOUND` / `REFERENCE_NOT_FOUND` for an unknown project or reference
(including one owned by another project). Removal is allowed during search and
does not delete or modify the corresponding paper/search result.

## Validation, safety, and exclusions

- Route inputs are strict UUID/JSON models with extra fields forbidden.
- Snapshot output is validated by the normalized strict `Paper` model. Never trust
  or re-render unchecked JSONB values.
- Browser rendering uses text nodes. Link destinations use existing provider URL
  validation and permit only safe HTTP(S) URLs.
- No route edits references, accepts manual citation data, exports, notes, reading
  state, or citation numbering. No API response exposes local database fields,
  logs, or ranking vectors/scores as part of the saved snapshot.
