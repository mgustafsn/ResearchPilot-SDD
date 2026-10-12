# Feature 002 data model — approved design

**Status**: Approved with the plan on 2026-10-12; task review remains pending.
Implement only via the reviewed new
`migrations/002_search_queries.sql`; never edit an already-applied 001 migration.
No tables for papers, search runs, ranking, references, or deleted-text history.

## Project revision/context columns

Existing project fields, timestamp behavior, and ProjectInput/Output stay unchanged.

| Column | Type / initial value | Meaning and invariant |
|---|---|---|
| mutation_revision | BIGINT NOT NULL, 0 | Nonnegative combined project/query concurrency identity; never decreases |
| query_context_revision | BIGINT NOT NULL, 0 | Nonnegative; advances when validated question/keywords actually change |
| generated_context_revision | Nullable BIGINT, null | Last successfully committed generation's context; nonnegative when present and ≤ current context revision |

Derive `refreshRequired` durably as: context revision > 0 AND generated context
revision is distinct from the current context revision. A new untouched project
does not claim its context changed; changing context before the first generation
does create the notice. Restoring old text advances context again, so it cannot
silently clear the notice. Successful current-context generation clears it even
if capacity/duplicates cause zero new additions (FR-QRY-009).

Every effective project-setting change advances mutation revision, including a
title/year/paper-count change. Only question/keyword changes advance context revision.
No-op project PUT preserves revisions while retaining existing timestamp behavior.
No full PUT may write/reset query fields or context acknowledgments.

## SearchQuery table

| Column | Type | Rule |
|---|---|---|
| id | UUID primary key | Server generated; stable across text/state edits |
| project_id | UUID FK projects(id) | NOT NULL; ON DELETE CASCADE; all operations scoped to parent |
| text | TEXT NOT NULL | Collapse all Unicode whitespace, then validate 1–160 characters |
| normalized_key | TEXT COLLATE "C" NOT NULL | Application-computed text.casefold(); UNIQUE(project_id, normalized_key) |
| enabled | BOOLEAN NOT NULL, default TRUE | Accept only JSON booleans at API boundary; disabled entries still consume slots |
| origin | TEXT NOT NULL | CHECK manual/generated; server-owned and never changes on user edits |
| user_owned | BOOLEAN NOT NULL | Manual origin implies TRUE; sticky TRUE after effective user text/state changes |
| slot | SMALLINT NOT NULL | CHECK 1–20; UNIQUE(project_id, slot); ascending slot is stable display/selection order |

PostgreSQL checks validate text length, origin/manual ownership, slot range, and
revision ranges. Python supplies whitespace normalization and Unicode casefold;
PostgreSQL lower()/citext is not a substitute. Do not cap normalized_key at 160:
casefold can expand characters. Slot uniqueness/range enforces the total cap of 20
without a separate count ledger. Query timestamps are unnecessary in this design.

Origin, ownership, slot and revisions are never client-writable. Manual addition
is owned and enabled by default, occupies the lowest free slot, and increments
mutation revision. Duplicate/capacity/validation errors perform no writes.

Effective normalized text or enabled-state changes make a generated entry owned
forever and increment mutation revision. A PATCH that changes neither value leaves
ownership/revision unchanged; text restoration after a real edit still retains
ownership. No-op PATCH may not bypass expected-revision validation.

## Transitions and ordering

- Manual: absent → owned entry → edited/toggled owned entry → deleted.
- Generated: absent → untouched generated entry → user-owned after a real edit/toggle.
- Deleted entries release slots, retain no tombstone/key history, and may reappear
  in later explicit generation. Disabled owned entries persist through regeneration.
- Existing owned IDs/text/state/slots remain unchanged during merge. Remove all and
  only untouched generated rows, skip preserved-key collisions, fill remaining
  slots in batch order, and cap the final list at 20.
- Every successful generation advances mutation revision, even a zero-add merge,
  and atomically sets generated_context_revision. Invalid/refused/truncated output,
  timeout, stale snapshot and failed transaction leave stored state unchanged.

## Snapshot and lock protocol

All writers use parent-first locking: lock `projects` row with SELECT FOR UPDATE,
then access child rows. Query reads return a coherent list/revision/context notice
within one short transaction using the parent lock. Do not hold locks across HTTP.

1. Compare client expectedRevision under parent lock; capture question/keywords,
   mutation revision and context revision. Release the read transaction.
2. Await provider and validate the whole batch outside any DB lock/transaction.
3. Re-lock parent; missing parent is 404, changed mutation revision is 409. Never
   recreate a deleted project or overwrite a newer query/context state.
4. Merge, acknowledge current context, increment revision, and commit atomically.

Manual mutation/revision increment uses one transaction under the same parent
lock. Concurrent same-revision mutations/generations have one successful winner;
others conflict. Failed generation reserves no durable ownership. Effective
project changes during generation also cause conflict; project deletion can finish
while the provider is pending, with FK cascading handled by PostgreSQL.

## Nonpersistent state

Pending generation and browser request/view identity live only in the current
request/view; no job history, lease or polling schema. Common suggestion metadata
(model/prompt version, optional token usage, duration/status) is sanitized for logs,
not exposed as scholarly facts. No raw provider body or secret is persisted.
