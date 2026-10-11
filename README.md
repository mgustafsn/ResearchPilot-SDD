# ResearchPilot-SDD

A specification-driven rebuild of a deliberately smaller ResearchPilot MVP.
This checkout currently contains planning artifacts, not an implemented application.

## Scope

Create projects → review editable AI query suggestions → retrieve real OpenAlex
papers → deduplicate and rank by embedding similarity → save project references.
Clustering, Scopus, explanations, manual categories, reference notes, reading status,
citation numbering, authentication, exports, and PDF ingestion are excluded.

## Review before implementation

1. Review [scope and proposed decisions](docs/scope.md).
2. Approve the [constitution amendment](docs/constitution-amendment.md). The existing
   constitution is preserved and currently conflicts with the reduced scope.
3. Review specifications in order:
   - [001 Projects](specs/001-project-management/spec.md)
   - [002 Queries](specs/002-search-queries/spec.md)
   - [003 Retrieval](specs/003-paper-retrieval/spec.md)
   - [004 Ranking](specs/004-relevance-ranking/spec.md)
   - [005 References](specs/005-saved-references/spec.md)
4. Clarify and approve feature 001, then review its draft plan, contracts, and tasks.
5. Implement and verify one feature at a time. Generate plans for later features
   only after their prerequisites and decisions are reviewed.

These artifacts were derived by an AI coding agent from the original repository;
they were not produced by invoking Spec Kit slash commands. They follow the installed
Spec Kit artifact structure. Drafts do not constitute human approval or verification.

The active feature is recorded in `.specify/feature.json`. The initialized integration
uses Claude skills such as `/speckit-clarify`, `/speckit-plan`, and `/speckit-tasks`.
No branch, commit, dependency installation, or application implementation was created
as part of the initial specification preparation. The artifacts are now tracked in a
private GitHub repository; implementation remains blocked by the review gates above.

## Course evidence

See [baseline sources](docs/baseline.md), [verification strategy](docs/verification.md),
and [evidence log](docs/evidence-log.md). Do not report proposed tests as executed,
or inferred prompts as historical evidence.
