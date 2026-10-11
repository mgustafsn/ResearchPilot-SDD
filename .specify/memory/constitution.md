# ResearchPilot Constitution

## Core Principles

### I. Provider-Sourced Facts (NON-NEGOTIABLE)

- All authoritative scholarly metadata — titles, authors, DOIs, publication dates, journals,
  publishers, citation counts, and URLs — MUST originate from a `PaperProvider`
  implementation (e.g., OpenAlex).
- An LLM MUST NOT generate, complete, correct, or overwrite paper metadata, and MUST NOT be
  used as a source of citations.
- Runtime LLM usage in this MVP MUST be restricted to search-query suggestions.
- No paper or citation shown to the user may originate from an LLM.

Rationale: Deterministic systems supply facts; AI supplies interpretation. Invented citations
destroy the product's core value — trustworthy literature discovery.

### II. Structured, Validated LLM Output

- Every LLM call consumed by the backend MUST request structured output (e.g., JSON schema)
  rather than parsing free-form prose.
- LLM responses MUST be validated against their expected schema before being stored or used;
  invalid responses MUST be handled as recoverable errors, not silently accepted.
- Prompts MUST be stored separately from business logic.
- Relevance ranking MUST use embeddings and deterministic scoring, not per-paper LLM calls.

Rationale: Structured, validated responses make LLM behavior testable and failures explicit,
and keep cost and latency bounded.

### III. External Integrations Behind Interfaces

- Business logic MUST NOT depend directly on OpenAI, OpenAlex, or any other vendor SDK/API.
- External capabilities MUST sit behind `PaperProvider`, `QuerySuggestionProvider`, and
  `EmbeddingProvider` interfaces. Business logic MUST NOT import vendor implementations.
- Query suggestion, retrieval, normalization, deduplication, and embedding-based relevance
  MUST remain logically separate operations; separate deployment units are not required.
- Providers MUST return data through common normalized models (e.g., `Paper`).
- Provider failures MUST be surfaced and logged with sanitized errors. Failed searches
  MUST preserve the previous result set; provider failure policy belongs in reviewed specs.

Rationale: Providers, models, and algorithms will change; isolating them keeps the domain
stable without requiring speculative interfaces for excluded capabilities.

### IV. User Control Over Search Queries

- User-edited and manually created queries MUST survive suggestion regeneration.
- Query origin and user modifications MUST be tracked explicitly; AI generation MUST NOT
  silently overwrite user-controlled query text or enabled state.
- Searches MUST use exactly the enabled stored queries captured when the attempt starts.
- Failed suggestion generation MUST leave the current query list unchanged and surface
  an error; manual queries MUST remain usable.

Rationale: AI proposes search terms; the researcher controls what is actually searched.

### V. Transparency & Reproducibility

- For each paper, the provider, DOI (if available), original publication URL, and
  open-access URL (if available) MUST be retained and displayable.
- Each search attempt MUST persist an input snapshot containing the research question,
  enabled queries, filters, paper limit, providers queried, and search timestamp.
- Searches MUST expose visible pending, success, and failure states with sanitized errors.
- Embedding-based relevance scores MUST disclose their algorithmic origin and MUST NOT
  be presented as evidence of scientific quality or validated relevance accuracy.
- Failed retrieval or ranking MUST preserve prior results. Saved provider-derived reference
  snapshots MUST survive later searches and application restarts.
- Backend logs MUST record provider requests/errors, result counts, duplicates removed,
  stage durations, and LLM calls (with token usage when available).

Rationale: Researchers must be able to audit discovery without fabricated explanations
or losing previously retained work.

### VI. Test-Backed Business Logic

- New business logic MUST be accompanied by automated tests.
- Tests MUST NOT call live external services; provider interfaces MUST be exercised through
  fakes or stubs.
- The full test suite MUST pass before a task is considered complete.
- Requirements MUST have stable IDs and traceable test mappings. Prompt changes, audit
  findings, commands, environments, and actual test outcomes MUST be recorded truthfully.
- Proposed tests and documentation checks MUST NOT be reported as application verification.
- Generic template wording that calls tests optional MUST NOT weaken these requirements.

Rationale: Interface-isolated, deterministic tests are what make providers safely replaceable
and keep pipeline regressions visible.

### VII. Simplicity & Phased Scope

- Scope MUST be determined by this rebuild's `docs/scope.md` and approved
  `specs/*/spec.md`, not the parent project's requirements or roadmap. Only the currently
  approved feature slice MAY be implemented; draft artifacts are not approval.
- The reduced MVP covers projects, editable query suggestions, OpenAlex retrieval and
  deduplication, embedding-based ranking, and saved references, delivered in reviewed slices.
- Clustering/subtopics, categorization explanations, manual paper organization, Scopus,
  multi-provider retrieval, manual citations, reference notes, reading status, citation
  numbering, authentication, public deployment, collaboration, exports/Zotero,
  institutional access, PDF ingestion, and embedding caches MUST NOT be implemented.
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
- Persistence MUST use PostgreSQL. Provider-owned paper metadata MUST remain separate
  from project-specific relevance and search state; saved references MUST be durable
  provider-derived snapshots, not LLM-generated or manually fabricated metadata.
- Deployment MUST remain local, single-user, and same-origin; no public deployment or
  account system is authorized by this MVP.
- The system MUST NOT assume institutional authentication permits permanently downloading,
  storing, or redistributing licensed publisher content.
- Searches MUST be bounded to at most 250 papers. Measurable performance budgets and
  reference hardware MUST be approved in feature specs or verification plans before
  performance acceptance is claimed.

## Development Workflow & Quality Gates

- Work MUST follow human review gates: constitution → specification → clarification →
  plan → tasks → tests/implementation → verification. Approval at one gate MUST NOT be
  inferred as approval of later gates.
- Every `plan.md` MUST include a Constitution Check confirming compliance with Principles
  I–VII; any deviation MUST be recorded in Complexity Tracking with justification.
- A task is complete only when: tests for new business logic exist, the full suite passes,
  no secrets are committed, and no out-of-scope features were introduced.
- Reviews MUST verify that no LLM output flows into authoritative metadata fields and that
  vendor SDKs are only referenced inside provider implementations.
- Constitution amendments MUST trigger re-review of dependent specs, plans, contracts,
  tasks, and checklists before their prior compliance claims are reused.

## Governance

- This constitution supersedes other practices for ResearchPilot-SDD. Where `AGENTS.md`,
  generic templates, draft artifacts, or parent-project documents conflict with it, this
  constitution MUST prevail until amended.
- Amendments MUST use `/speckit-constitution`, receive explicit human approval, record
  the approver and date, and undergo impact review of dependent artifacts. A temporary
  Sync Impact Report MUST be produced for review and removed before commit; the durable
  amendment record MUST preserve the version change, approval, and follow-up obligations.
- Versioning follows semantic versioning: MAJOR for removed or redefined principles; MINOR
  for new principles/sections or materially expanded guidance; PATCH for clarifications.
- Compliance is checked at plan time (Constitution Check), at task completion, and during
  code review. Unjustified complexity or violations block completion.
- Runtime development guidance lives in `AGENTS.md`.

Amendment record: **1.0.0 → 2.0.0**, approved by the user on **2026-10-11** by
selecting option A (reply: "a") for `docs/constitution-amendment.md`. This major
amendment removes clustering/interpretation mandates, replaces categorization control
with query control, and makes the rebuild's reduced scope authoritative. Provider facts,
validated structured output, PostgreSQL, secrets protection, and mandatory testing remain.
Dependent drafts MUST be re-reviewed; no feature specification, product decision, plan,
contract, or task is approved by this amendment. Generic optional-test wording remains
overridden by Principle VI.

**Version**: 2.0.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
