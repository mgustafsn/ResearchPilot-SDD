# Proposed constitution amendment — approval required

The existing `.specify/memory/constitution.md` is user work and has not been changed.
It is version 1.0.0 and references parent-project requirements rather than this
rebuild's reduced scope. A plan cannot pass its Constitution Check unchanged.

## Proposed change

After human approval, use the constitution skill to make a major amendment to 2.0.0:

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

All five feature specifications are drafts under the proposed reduced scope.
Feature 001's plan remains BLOCKED until this amendment and its product decisions
are approved. Review installed templates for consistency (especially optional-test
wording) when amending; project tests remain mandatory despite generic template text.

Approval, ratification date, approver, and final version must be recorded when the
amendment actually happens. This proposal does not itself amend the constitution.
