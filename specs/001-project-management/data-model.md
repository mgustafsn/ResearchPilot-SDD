# Data model: Projects — draft

| Field | Storage / meaning | Rule |
|---|---|---|
| id | UUID primary key | Server generated; stable across edits |
| title | Text | Trimmed, 1–200 characters |
| researchQuestion | Text | Trimmed, 1–5000 characters |
| keywords | JSON string list | At most 30 inputs; trim, validate length 1–100, case-fold deduplicate |
| yearFrom / yearTo | Nullable integer | 1–9999, start ≤ end if both supplied |
| maxPaperCount | Integer | 1–250, required input |
| createdAt / updatedAt | UTC timestamps | Server owned; createdAt unchanged on update |

Input accepts camelCase API fields; internal database column names may use snake_case.
Reject extra request keys. Reject numeric booleans and coercible noninteger strings
for year/count fields. Omitted keywords default to []; omitted year bounds default
to null. Required fields remain required for both POST and full PUT.

No project status is needed for this slice; feature 003 owns search lifecycle.
No unique title constraint. Sort newest updatedAt first, then ascending UUID for ties.
Successful update changes updatedAt; failed validation/storage does not change state.

Future ownership relationships (not tables to create now): Project → SearchQuery,
SearchRun, ProjectPaper, Reference. Project deletion will cascade owned records.
References will store independent metadata snapshots rather than depend on current
search associations. Do not introduce those schemas before their plans are approved.
