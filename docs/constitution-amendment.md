# Constitution amendment — ratified; dependent reviews required

The amendment from 1.0.0 to 2.0.0 was approved by the user on 2026-10-11
(reply: "a"), as recorded in `.specify/memory/constitution.md`. The original proposal
below is retained as rationale; it is no longer a pending constitution-approval gate.
Ratification does not approve dependent feature specifications or designs.

## Proposed change

The proposal approved for constitution 2.0.0 was:

1. Preserve provider-owned authoritative metadata and structured validated LLM output.
2. Restrict runtime LLM usage in this MVP to query suggestions. Remove mandates for
   clustering, interpretation, explanations, summaries, and institutional-access interfaces.
3. Require PaperProvider, QuerySuggestionProvider, and EmbeddingProvider interfaces;
   business logic must not import vendor-specific implementations.
4. Replace user-categorization rules with user-query control: edits and manual queries
   survive regeneration; searches use exactly the enabled stored queries.
5. Require source provenance, search input snapshots, visible pending/failure states,
   sanitized errors, and algorithmic score disclosure; no clustering status or explanation UI.
6. Make `docs/scope.md` and approved `specs/*/spec.md` the rebuild's scope authority
   rather than parent `docs/ROADMAP.md` or requirements.
7. Keep mandatory automated testing, secret handling, and simplicity. Require stable
   requirement IDs and truthful prompt/audit/test evidence.
8. Target at most 250 papers per search. Move measurable performance budgets and
   reference hardware into reviewed feature specifications/verification plans.
9. Require preservation of prior results on failed searches and durable reference snapshots.
10. Retain human review gates: constitution → specification → clarification → plan →
    tasks → tests/implementation → verification. Record amendments and recheck affected artifacts.

## Impact

On 2026-10-12 the user approved the five-slice scope boundaries and feature 001
specification. Feature 001's plan, rationale, data model, API contract, quickstart,
and checklist were re-reviewed against constitution 2.0.0 for the plan review;
human plan/contract approval was subsequently recorded on the same date. Task
reconciliation was completed for review on the same date; task approval remains pending.
Later feature drafts must be re-reviewed before their own approval gates. Mandatory
tests override any generic template optional-test wording. No runtime compliance
or implementation acceptance is claimed by these documentation reviews.
