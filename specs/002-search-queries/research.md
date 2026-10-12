# Feature 002 design research — approved plan rationale

**Date**: 2026-10-12. Based on approved specification, existing implementation,
read-only repository analysis, and official documentation. No live model calls,
dependency installation, application changes, or performance experiments performed.
The user approved the design choices with the plan/contracts on 2026-10-12;
implementation/task review and actual verification remain separate gates.
Two read-only research agents were used because the planning skill explicitly
requests research delegation; neither wrote files or inspected credentials.

## Decisions and alternatives

| Decision | Rationale | Alternatives considered |
|---|---|---|
| Pin `gpt-4.1-mini-2025-04-14` | Officially documented non-reasoning, low-latency model supporting strict Structured Outputs; reproducible snapshot suitable for short queries | Floating alias may change behavior; GPT-5.4 Mini supports structured output but costs more and has reasoning capabilities unnecessary for this task |
| Chat Completions over HTTPX | Small one-shot JSON envelope, no tools/history; HTTPX is already present in the project | OpenAI recommends Responses for new projects; it remains a viable alternative, but its typed output envelope adds no required capability here |
| Promote HTTPX to runtime, no SDK | Production adapter needs a maintained async HTTP client; no new package family or vendor SDK | An SDK is unnecessary for one endpoint; urllib would require more timeout/async/error plumbing |
| One call, no retries, 512 completion tokens | Bound user-triggered requests/cost without hidden repair calls | Higher caps may reduce truncation but increase allowed spend; truncation is handled atomically, not salvaged |
| 20 s total async deadline plus phase limits | HTTPX phase limits are inactivity/phase limits, not a total wall-clock bound | Synchronous requests with only a read timeout can exceed the intended deadline; jobs/leases are not needed for this slice |
| One shared mutation revision on projects | Covers stale project/list updates with fewer fields than separate counters; timestamps are not reliable concurrency identities | Separate project/query counters work but add comparison/state complexity |
| Context and generated-context revisions | A monotonic context change makes the notice sticky even when the user restores previous text; only committed generation clears it | Hash equality alone would wrongly clear the notice on context restoration |
| Parent-first short PostgreSQL transactions | Serializes capacity/key/ownership changes and prevents stale resurrection while leaving manual work available during AI calls | Holding a lock during provider work harms responsiveness; process-only locks do not protect multiple requests/restarts |
| Bounded unique slots 1–20 | Enforces capacity in PostgreSQL without a counter/trigger; deterministic slot order | COUNT under only child locks can race; a trigger/count ledger is unnecessary |
| Stored Python case-fold key | Handles Unicode such as Straße/STRASSE consistently with approved query normalization | PostgreSQL lower()/citext is not Python casefold and would weaken the uniqueness rule |
| Keep ProjectInput/Output unchanged | Existing API exact-shape tests and full PUT semantics remain valid; query state belongs to nested endpoints | Putting writable query state in full project PUT risks overwriting it and changes the 001 contract |
| Async request/view identity checks | Existing frontend applies some delayed responses without project/revision guards; generation makes that unsafe | Disabling Generate alone cannot protect navigation or concurrent manual changes |

These choices are approved design decisions, not verified facts about runtime
performance, model quality, or the original implementation.

## Verified official sources

Checked 2026-10-12 using public documentation only:

1. [GPT-4.1 Mini model](https://developers.openai.com/api/docs/models/gpt-4.1-mini):
   documented alias/snapshot, no reasoning step, Chat/Responses and Structured
   Outputs support. Listed standard text pricing: $0.40/M input, $1.60/M output.
2. [GPT-5.4 Mini model](https://developers.openai.com/api/docs/models/gpt-5.4-mini):
   documented `gpt-5.4-mini-2026-03-17`, structured outputs and reasoning effort
   none; listed $0.75/M input and $4.50/M output. No comparative quality test run.
3. [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs):
   strict schema, required object properties/additionalProperties:false, refusal
   handling and supported schema subset. Backend business validation remains needed.
4. [Chat reference](https://developers.openai.com/api/reference/resources/chat):
   `response_format.json_schema`, `max_completion_tokens`, `store`, choices,
   refusal and finish-reason fields. `max_tokens` is deprecated; output-token caps
   are not character/input-token caps.
5. [Responses migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses)
   and [Responses reference](https://developers.openai.com/api/reference/resources/responses/methods/create):
   Responses is the new-project recommendation; Chat remains supported. If changing
   endpoints later, use Responses' text.format/max_output_tokens and typed output,
   not Chat's request/envelope or an SDK-only convenience property.
6. [Data controls](https://developers.openai.com/api/docs/guides/your-data): API data
   is not used for training unless opted in; default abuse-monitoring logs may
   retain content up to 30 days, with documented longer-retention exceptions.
   Zero Data Retention/Modified Abuse Monitoring require eligibility/approval;
   `store:false` does not promise zero retention or disable every cache exception.

Prices/model availability may change. No monthly/call cost guarantee is asserted:
input tokenization and live billing were not measured. The token/timeout/byte/HTTP
connection limits are local design proposals, not OpenAI performance guarantees.

## Integration findings

- `backend/researchpilot/persistence.py` already runs sorted SQL migrations in a
  transaction, but reflects only projects. Share metadata/reflection for queries.
- `service.py` project update/delete must join parent-first locking/revision rules;
  query-only writes must not alter project timestamps or query contents via full PUT.
- `test_project_postgres.py` hard-codes one migration/count; adapt expected reviewed
  versions and compare the pre-failure count in rollback tests, not a magic one.
- `conftest.py` currently truncates projects alone. Explicitly truncate both approved
  feature tables together only after existing name/host/opt-in/target safeguards.
- Add provider-injected real browser-server fixtures entirely in test code; do not
  ship a production fake-provider environment switch or fake control endpoints.
- Keep the existing SDK-import audit meaningful while isolating the vendor adapter;
  no SDK imports may appear in domain/service modules.
- BUG-PRJ-001 is explicitly deferred. Touching frontend request logic must not claim
  that year-input defect or remaining human audit evidence has been resolved.

## Phase 0 outcome

The design has concrete approved choices for each technical unknown. Task approval
is still required; no implementation authorization is inferred from plan approval.
Runtime suggestion quality, external latency/availability, and actual final test
results remain verification work, not invented research findings.
