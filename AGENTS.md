# ResearchPilot-SDD development rules

- Read `.specify/memory/constitution.md`, `docs/scope.md`, and the active feature spec.
- The constitution remains authoritative. Resolve the scope conflicts documented in
  `docs/constitution-amendment.md` before implementation; do not silently bypass them.
- All supplied specifications, plans, contracts, and tasks are drafts pending review.
- Implement only the approved feature slice. No clustering or other excluded features.
- Scholarly metadata comes only from PaperProvider implementations, never an LLM.
- Use structured, validated LLM responses and separate integration interfaces.
- User-edited queries must survive suggestion regeneration.
- Failed searches preserve previous results; saved references survive later searches.
- Secrets come from environment variables and never reach browser responses or logs.
- Add business-logic tests and run tests before considering an implementation complete.
- Record requirement IDs, prompt changes, audit findings, and actual test evidence.
- Do not copy the original implementation wholesale or alter the original repository.
- Prefer simple designs and necessary dependencies only. Do not delegate unless requested.
