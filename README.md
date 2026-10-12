# ResearchPilot-SDD

A specification-driven rebuild of a deliberately smaller ResearchPilot MVP.
This checkout currently contains planning artifacts, not an implemented application.

## Scope

Create projects → review editable AI query suggestions → retrieve real OpenAlex
papers → deduplicate and rank by embedding similarity → save project references.
Clustering, Scopus, explanations, manual categories, reference notes, reading status,
citation numbering, authentication, exports, and PDF ingestion are excluded.

## Review before implementation

1. The [constitution amendment](docs/constitution-amendment.md) is ratified as 2.0.0;
   [scope boundaries](docs/scope.md) and feature 001's specification are approved.
   Later-slice product decisions and specifications remain drafts.
2. Feature 001's [plan](specs/001-project-management/plan.md) and
   [API contract](specs/001-project-management/contracts/api.md) are approved.
   Its tasks are approved and feature 001 implementation is authorized; the
   implementation workflow's unchecked-checklist confirmation remains pending.
3. Review later specifications in order after their prerequisites:
   - [001 Projects](specs/001-project-management/spec.md)
   - [002 Queries](specs/002-search-queries/spec.md)
   - [003 Retrieval](specs/003-paper-retrieval/spec.md)
   - [004 Ranking](specs/004-relevance-ranking/spec.md)
   - [005 References](specs/005-saved-references/spec.md)
4. Implement and verify one approved feature at a time. Generate plans for later features
   only after their prerequisites and decisions are reviewed.

Initial artifacts were derived by an AI coding agent from the original repository
without invoking Spec Kit commands. Feature 001 subsequently underwent the installed
`speckit-clarify` workflow and a `speckit-plan` review/update on 2026-10-12. Drafts
do not constitute human approval or verification; see the evidence log for actual work.

The active feature is recorded in `.specify/feature.json`. The initialized integration
uses Claude skills such as `/speckit-clarify`, `/speckit-plan`, and `/speckit-tasks`.
No branch, commit, dependency installation, or application implementation was created
as part of the initial specification preparation. The artifacts are now tracked in a
private GitHub repository; implementation remains blocked by the review gates above.

## Course evidence

See [baseline sources](docs/baseline.md), [verification strategy](docs/verification.md),
and [evidence log](docs/evidence-log.md). Do not report proposed tests as executed,
or inferred prompts as historical evidence.
