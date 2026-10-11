<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: Initial ratification — all placeholders replaced with project-specific governance.

Modified principles (template slot → new title):
  - [PRINCIPLE_1_NAME] → I. Provider-Sourced Facts (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. Structured, Validated LLM Output
  - [PRINCIPLE_3_NAME] → III. External Integrations Behind Interfaces
  - [PRINCIPLE_4_NAME] → IV. User Control Over AI Organization
  - [PRINCIPLE_5_NAME] → V. Transparency & Reproducibility
Added principles:
  - VI. Test-Backed Business Logic
  - VII. Simplicity & Phased Scope
Added sections:
  - Security & Configuration Constraints (template SECTION_2)
  - Development Workflow & Quality Gates (template SECTION_3)
Removed sections: none

Sources: ../AGENTS.md, ../ARCHITECTURE.md, ../docs/requirements.md,
../docs/ROADMAP.md, ../docs/DATA_MODEL.md

Follow-up TODOs: none. Ratification date set to first adoption (2026-10-11).
-->

# ResearchPilot Constitution

## Core Principles

### I. Provider-Sourced Facts (NON-NEGOTIABLE)

- All authoritative scholarly metadata — titles, authors, DOIs, publication dates, journals,
  publishers, citation counts, and URLs — MUST originate from a `PaperProvider`
  implementation (e.g., OpenAlex).
- An LLM MUST NOT generate, complete, correct, or overwrite paper metadata, and MUST NOT be
  used as a source of citations.
- LLM output is restricted to interpretation: search query expansion, cluster naming and
  description, classification explanations, summaries, and analysis.
- Classification explanations and any analysis MUST be grounded only in metadata and
  abstracts supplied by the application.
- No paper or citation shown to the user may originate from an LLM.

Rationale: Deterministic systems supply facts; AI supplies interpretation. Invented citations
destroy the product's core value — trustworthy literature discovery.

### II. Structured, Validated LLM Output

- Every LLM call consumed by the backend MUST request structured output (e.g., JSON schema)
  rather than parsing free-form prose.
- LLM responses MUST be validated against their expected schema before being stored or used;
  invalid responses MUST be handled as recoverable errors, not silently accepted.
- Prompts MUST be stored separately from business logic.
- The pipeline MUST NOT send every paper through an individual LLM call where embeddings or
  algorithms can do the work; embeddings are preferred for relevance ranking and clustering.

Rationale: Structured, validated responses make LLM behavior testable and failures explicit,
and keep cost and latency bounded.

### III. External Integrations Behind Interfaces

- Business logic MUST NOT depend directly on OpenAI, OpenAlex, or any other vendor SDK/API.
- Each external capability MUST sit behind an interface: `PaperProvider`, `LlmProvider`,
  `EmbeddingProvider`, a replaceable clustering strategy, and (future)
  `InstitutionalAccessProvider`.
- Each pipeline step (query expansion, retrieval, normalization, deduplication, relevance,
  embedding, clustering, cluster interpretation) MUST be a logically separate service.
- Providers MUST return data through common normalized models (e.g., `Paper`).
- A failure in one provider SHOULD NOT fail the entire search; failures MUST be surfaced
  and logged.

Rationale: Providers, models, and algorithms will change; isolating them keeps the domain
stable and allows future institutional access, extra providers, and exports without redesign.

### IV. User Control Over AI Organization

- User edits (renaming, moving papers, creating/deleting/merging subtopics, marking papers
  irrelevant) MUST take precedence over AI-generated categorization.
- AI processes MUST NOT silently overwrite user modifications; user-modified state MUST be
  tracked explicitly (e.g., `userModified`, `generatedByAi`).
- Papers that do not clearly fit a cluster MUST be placed in "Uncategorized" rather than
  forced into an inaccurate subtopic.

Rationale: The user has final control. AI organization is a starting point, not a verdict.

### V. Transparency & Reproducibility

- For each paper, the provider, DOI (if available), original publication URL, and
  open-access URL (if available) MUST be retained and displayable.
- For each project, the original research question, generated search queries, search
  filters, providers queried, and search timestamp MUST be persisted.
- Users MUST be able to see why a paper was considered relevant and why it belongs to its
  subtopic.
- Long-running searches MUST expose status (`CREATED` → `SEARCHING` → `PROCESSING` →
  `CLUSTERING` → `ANALYZING` → `COMPLETED` / `FAILED`).
- Backend logs MUST record provider requests/errors, result counts, duplicates removed,
  stage durations, and LLM calls (with token usage when available).

Rationale: Researchers must be able to trust and audit how a research map was produced.

### VI. Test-Backed Business Logic

- New business logic MUST be accompanied by automated tests.
- Tests MUST NOT call live external services; provider interfaces MUST be exercised through
  fakes or stubs.
- The full test suite MUST pass before a task is considered complete.

Rationale: Interface-isolated, deterministic tests are what make providers safely replaceable
and keep pipeline regressions visible.

### VII. Simplicity & Phased Scope

- Only the currently requested roadmap phase (see `docs/ROADMAP.md`) MAY be implemented.
- Features marked future or out-of-scope (e.g., institutional SSO, EZproxy, Scopus,
  paywalled PDF download, PDF vector stores, research-gap analysis, citation graphs,
  collaboration, Zotero sync, multiple LLM providers) MUST NOT be implemented; interfaces
  MAY be shaped so they can be added later.
- Prefer simple implementations over premature abstractions; abstractions beyond those
  required by Principle III MUST be justified in the plan.
- New dependencies MUST NOT be added unless necessary, and their need MUST be stated.
- Follow the existing project structure.

Rationale: Phased delivery keeps the MVP shippable; speculative design adds cost without value.

## Security & Configuration Constraints

- Secrets and API keys (e.g., `OPENAI_API_KEY`, `OPENALEX_EMAIL`, `DATABASE_URL`) MUST come
  from environment variables and MUST NOT be committed.
- API keys MUST NEVER be exposed to the frontend or written to logs.
- Provider-specific configuration MUST live outside business logic.
- Persistence uses a relational database (PostgreSQL); `Paper` holds globally reusable
  scholarly metadata, while project-specific data (relevance, explanations, relevance flags)
  lives on `ProjectPaper`.
- The system MUST NOT assume institutional authentication permits permanently downloading,
  storing, or redistributing licensed publisher content.
- The system MUST support 100–250 papers per project without significant UI slowdown.

## Development Workflow & Quality Gates

- Work follows the Spec Kit flow: specify → (clarify) → plan → tasks → implement.
- Every `plan.md` MUST include a Constitution Check confirming compliance with Principles
  I–VII; any deviation MUST be recorded in Complexity Tracking with justification.
- A task is complete only when: tests for new business logic exist, the full suite passes,
  no secrets are committed, and no out-of-scope features were introduced.
- Reviews MUST verify that no LLM output flows into authoritative metadata fields and that
  vendor SDKs are only referenced inside provider implementations.

## Governance

- This constitution supersedes other practices for ResearchPilot. Where `AGENTS.md`,
  `docs/requirements.md`, or `docs/ROADMAP.md` conflict with it, the constitution prevails
  until amended.
- Amendments are made via `/speckit-constitution`, MUST document the change in a Sync Impact
  Report, and MUST be reviewed for impact on dependent templates and active specs/plans.
- Versioning follows semantic versioning: MAJOR for removed or redefined principles; MINOR
  for new principles/sections or materially expanded guidance; PATCH for clarifications.
- Compliance is checked at plan time (Constitution Check), at task completion, and during
  code review. Unjustified complexity or violations block completion.
- Runtime development guidance lives in `AGENTS.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
