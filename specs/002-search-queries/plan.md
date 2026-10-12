# Implementation Plan: User-controlled search queries

**Feature identifier**: `002-search-queries` (actual Git branch: `main`)
**Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)
**Status**: Proposed plan and contracts, awaiting explicit human approval.
The specification is approved; no 002 implementation, dependency changes, or live
AI calls are authorized by this draft. Tasks require their own subsequent review.

## Summary

Extend the existing local application with durable manual/AI query management.
Generate only on explicit request, validate the complete structured batch, preserve
user-owned text/enabled state, and merge atomically without overwriting newer data.
Use a provider interface, one pinned OpenAI adapter, and real PostgreSQL revision
checks. No scholarly retrieval, search runs, ranking, references, suppression history,
background jobs, or new frontend framework. BUG-PRJ-001 remains deferred, not fixed.

## Technical Context

| Area | Proposed choice |
|---|---|
| Language/platform | Existing Python 3.12+, vanilla JS/HTML/CSS, local Linux, same-origin loopback server |
| Runtime dependencies | Existing FastAPI/Pydantic, SQLAlchemy, psycopg, uvicorn; promote existing HTTPX from dev-only to runtime for the adapter |
| Storage | Existing PostgreSQL 17, new ordered SQL migration; project revision columns plus `search_queries` table |
| Suggestion provider | `QuerySuggestionProvider` protocol; business logic imports only common schemas/protocol, never the vendor adapter |
| Provider model | Proposed pinned `gpt-4.1-mini-2025-04-14`, strict JSON-schema Chat Completions, `store:false`, no tools/history/streaming |
| Provider budgets | One HTTP call per explicit generation, no automatic retries, 512 completion tokens; 20 s total deadline; connect 3 s/pool 2 s/write 5 s/read 15 s; response body at most 64 KiB |
| Connection/click bounds | One shared async HTTPX client, at most two upstream connections in this single-worker local app; disable repeated Generate clicks in the same view while pending |
| Manual availability | Missing/invalid provider configuration disables generation only; project startup and manual query CRUD continue working |
| Scale | At most 20 queries per project including disabled entries; 3–6 unique normalized suggestions per validated batch |
| Tests | Existing pytest/HTTPX/Playwright/Ruff; fake providers, HTTPX MockTransport, real safeguarded PostgreSQL, real browser server with test-only dependency injection |
| Performance proposal | Query CRUD p95 below 500 ms under the protocol in `../../docs/verification.md`; keep existing project budget; live AI latency/quality is not an acceptance claim |

Model, endpoint, budget, performance, and contract choices are proposals, not inferred
approval. Official source checks and alternatives are in [research.md](research.md).
HTTPX is already locked; promoting it is necessary for production installs without
dev dependencies. No OpenAI SDK, tokenizer, task queue, cache, or new package family.

## Constitution Check

| Principle | Pre/post-design assessment | Gate |
|---|---|---|
| I. Provider facts | LLM emits query text only; no Paper model/metadata/citation output or scholarly provider in 002 | PASS at design level |
| II. Structured output | Strict JSON schema, complete-batch backend validation, separate versioned system prompt, explicit refusal/truncation failure | PASS at design level |
| III. Interfaces | Async provider protocol and common models; vendor HTTP lives only in the adapter/composition root | PASS at design level |
| IV. User control | Sticky ownership, enabled-state protection, exact stored selection, no implicit fallback or generation | PASS at design level |
| V. Transparency | Pending/success/error UI, durable context notice, sanitized provider status/durations/token usage; no raw inputs/bodies/secrets in logs | PASS at design level |
| VI. Tests | Mandatory business/fault/concurrency/browser tests, stable FR-QRY mapping, actual evidence; no paid/live test calls | PASS at design level; execution pending |
| VII. Phased simplicity | Approved 002 only; one migration/protocol/adapter, no future search/reference schema; known 001 issue remains explicit | PASS at design level |

Pre-design review and post-design review on 2026-10-12 found no constitutional
deviation in this proposal. This does not approve the plan or establish application
verification. Feature 001 is accepted with a known limitation; its audit evidence
and year-validation nonconformance are not silently closed by 002.

## Project Structure

Proposed paths; existing application files are extended only after task approval:

```text
backend/researchpilot/
  query_domain.py                # query schemas, normalization, merge/selection rules
  query_provider.py              # protocol, common batch/metadata, sanitized failures
  query_service.py               # persistence and generation orchestration
  integrations/
    __init__.py
    openai_queries.py            # HTTPX vendor adapter; no SDK
  prompts/query_suggestions_v1.txt
  service.py                    # existing project update/delete revision hooks
  persistence.py                # existing migrations and shared table reflection
  api.py                        # composition, nested endpoints, sanitized errors
backend/tests/
  test_queries.py
  test_query_api.py
  test_query_provider.py
  test_query_postgres.py
  test_query_browser.py
  test_query_performance.py
  conftest.py                    # safe multi-table cleanup and provider injection
frontend/index.html, app.js, styles.css
migrations/002_search_queries.sql
.env.example, pyproject.toml, uv.lock, README.md, .github/workflows/ci.yml
```

Planning artifacts: this plan, `research.md`, `data-model.md`,
`contracts/api.md`, `contracts/provider.md`, and `quickstart.md`.
`tasks.md` is produced only after plan/contract approval, not by this workflow.

## Core Design Decisions

### Storage and atomicity

- One monotonically increasing `mutation_revision` on the parent project covers
  effective project-setting changes, query mutations, and successful generation.
  Context/generation revisions derive the sticky refresh notice; see the model.
- Every writer locks the parent first. Query slot/normalized-key constraints
  enforce capacity and uniqueness. Do not use timestamps as concurrency tokens.
- A coherent query-list read uses one short transaction under the same parent
  lock. Existing ProjectInput/ProjectOutput and full PUT field semantics stay
  unchanged; query state is exposed through separate nested endpoints.
- Project updates advance context revision only for changed validated question or
  keywords. Other effective setting changes still invalidate pending generation.
  Project deletion cascades query rows and never waits for an external AI call.
- Query operations do not change existing project `updatedAt` or list ordering;
  revisions track those changes. Manual duplicate edits/additions are rejected,
  not silently merged, and stale manual writes receive a conflict.

### Generation

1. Lock/read parent and capture ID, expected mutation revision, context revision,
   question, keywords; commit/end the short read transaction.
2. Await `QuerySuggestionProvider` outside every database transaction/lock. Sync
   database phases run in worker threads (e.g. standard `asyncio.to_thread`) so
   the async route does not block the event loop during provider waits.
3. Validate the complete batch after normalization: 3–6 unique case-folded texts,
   each 1–160 characters; reject invalid output, rather than salvaging/truncating it.
4. Re-lock parent. Missing parent → 404; changed mutation revision → 409. Preserve
   every user-owned row unchanged, delete only untouched generated rows, skip
   preserved-key collisions, and fill free slots in batch order up to 20.
5. Set generated context revision and increment mutation revision even if zero
   suggestions were added. Commit all changes before returning success.

Two calls capturing the same revision use first-successful-commit-wins semantics;
the other conflicts. No latest-request ownership token, durable pending job,
lease, polling, or history table. Provider failure/cancellation before merge writes
nothing; do not promise that losing a browser response undoes a completed commit.

### Adapter, privacy, and configuration

- Proposed `OPENAI_API_KEY` is server-side only. Optional `OPENAI_QUERY_MODEL`
  defaults to the approved snapshot if/when this plan is approved; changing the
  reviewed model/prompt/budgets requires recorded regression evidence.
- Send only question/keywords as JSON-serialized user-role data under a fixed
  system prompt. No project name, years, paper count, stored query text, papers,
  notes, tools, or conversation history is sent by this adapter.
- Explicit `store:false` is not zero retention. Document OpenAI's default abuse
  monitoring retention and obtain separate permission for any live smoke test.
- Fixed HTTPS endpoint, TLS verification, no redirects or environment proxies.
  Bound streamed response bytes and apply an actual async total deadline, not
  merely per-phase HTTPX inactivity timeouts.
- Failures map to fixed safe categories; never log raw response bodies, request
  context, headers, API keys, database URLs, or exception strings. Record project
  UUID, model/prompt version, status/category, duration, counts, and token usage
  when available. No hidden retry or repaired/fallback suggestion batch.

### UI and asynchronous responses

- Labeled query list and explicit Generate action; origin/ownership/enabled state
  are visible. Manual controls remain available during generation or without a key.
- Notice after context change persists across reopen/restart and clears only after
  successful generation for the current context, including a zero-add merge.
- Capture project/view identity and mutation revision for each request. Ignore
  late responses/errors after navigation/editing/deletion and older revisions;
  a slow response must not repaint a different project or discard unsaved input.
- A stale-generation error reloads current saved state without clearing unsaved
  manual text. Show added/duplicate/capacity counts; do not imply disabled or
  user-owned queries were refreshed. Text-only rendering and keyboard focus remain.
- Do not change the deferred publication-year conversion while touching this UI.

## Requirement-to-Test Mapping

| Requirement | Proposed evidence |
|---|---|
| FR-QRY-001 | Mock request schema, complete valid/invalid/refused/truncated batches, normalized uniqueness, persisted generation/restart |
| FR-QRY-002 | Unicode whitespace/case-fold normalization, 0/1/160/161 lengths, per-project uniqueness, preserved collisions and zero-add merges |
| FR-QRY-003 | Manual CRUD/toggle, strict booleans/unknown fields, default enabled, persistence, missing-key operation and keyboard controls |
| FR-QRY-004 | Edited/toggled/manual ownership, restoration staying owned, no-op rules, unchanged IDs/text/state/slots through regeneration |
| FR-QRY-005 | Timeouts/HTTP failures/missing configuration/refusal/bad JSON/failed commits; complete previous list and notice retained; no fallback/retries |
| FR-QRY-006 | Pure enabled-stored-query selection, empty selection rejection, no description substitution or scholarly calls/routes |
| FR-QRY-007 | Barriers for edit/toggle/add/delete/project update/project delete during generation, two simultaneous generations and SQL commit rollback |
| FR-QRY-008 | 19/20/21 capacity and concurrent additions, disabled entries counted, free-slot batch order, no ownership evictions |
| FR-QRY-009 | Context vs noncontext changes, sticky notice even after reverting context, reload/restart, no automatic calls, failed/stale/zero-add outcomes |
| FR-QRY-010 | Deletion slot release/no tombstones, permitted later reappearance, preserved disabled entries, stale deletion rejection |

Always run existing 001 regressions. Update migration-count/version and fixture
cleanup expectations for both reviewed tables without weakening safeguards. Do not
modify the original repository or rewrite old 001 evidence as new verification.
Record tests and prompt changes with FR-QRY IDs; human audit/acceptance remains real.

## Review and Delivery Sequence

1. Review this plan, model/privacy/budget proposals, API/provider contracts, and
   proposed verification protocol. Obtain explicit approval; no coding yet.
2. Generate/review/approve tasks separately. Write and review behavior tests before
   each implementation increment; normal tests/CI must use fakes, not paid APIs.
3. Implement reviewed schema/manual management, then generation adapter/atomic merge,
   then browser integration, fault/concurrency/performance tests and audits.
4. Run the full suite/lint/syntax and approved-host measurements; record actual
   outcomes. Obtain human acceptance before feature 003 planning/implementation.

## Complexity Tracking

No constitutional deviations are proposed. The provider protocol is required,
revision/context columns are necessary for FR-QRY-007/009, and bounded slots enforce
FR-QRY-008 without a trigger/count ledger. Async HTTPX is necessary for an enforceable
total timeout while retaining manual access; no SDK, job system, registry, tombstones,
embedding cache, or speculative search/reference schema is introduced.
