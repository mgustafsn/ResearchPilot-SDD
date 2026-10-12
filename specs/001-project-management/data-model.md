# Data model: Projects — draft

Re-reviewed on 2026-10-12 against the approved specification and constitution 2.0.0;
this design was approved with the plan on the same date. Only the Project table
is created in slice 001; task review and implementation remain pending.

| Field | Storage / meaning | Rule |
|---|---|---|
| id | UUID primary key | Server generated; stable across edits |
| title | Text; displayed as "Project name" | Trimmed, 1–200 characters |
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

Use PostgreSQL UUID, timezone-aware timestamps, nullable integer years, and JSON
keywords through SQLAlchemy. Enforce basic nonempty/length, count-range, and ordered
year constraints in the database as well as validated application inputs. Keyword
normalization remains application logic. Migrations track versions without clearing
project data; failed mutations roll back as a whole.

Lifecycle: absent → created → updated → permanently deleted. UI confirmation warns
that the project and its contents will be lost with no undo. Cancellation sends no
DELETE request. Failure leaves the project unchanged; deletion cannot affect another
project or the original application's data. No archive, restore, or future-owned table
is implemented in this slice.
