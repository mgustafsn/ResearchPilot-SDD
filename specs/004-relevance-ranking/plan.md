# Implementation Plan: Local semantic relevance ranking

**Feature**: `004-relevance-ranking` | **Actual Git branch**: `main`
**Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)
**Status**: Plan and supporting design/API/embedding contracts approved by the user on 2026-10-21 (reply: “I approve”). Tasks/implementation separately authorized on 2026-10-21 (reply: “Start”).

## Summary

Extend explicit Search with local embedding generation after OpenAlex retrieval and
deduplication, before atomic result replacement. Use the approved MiniLM model and
provisional calibration. Keep all papers visible; preserve old results on failure.
Do not implement references, clustering, caches, or cloud AI integration.

## Technical Context

- **Language/platform**: Existing Python 3.12+ backend, vanilla JavaScript, local
  single-user loopback FastAPI app; PostgreSQL 17. Current project interpreter is
  Python 3.13 per prior evidence; record actual versions during implementation.
- **Dependencies**: Add `sentence-transformers==6.2.0` for the approved model's
  tokenizer/pooling/inference pipeline; CPU-only PyTorch as its necessary runtime.
  Declare `huggingface-hub` directly because the explicit setup command uses its
  snapshot download API. Lock compatible transitive versions in `uv.lock`; use an
  explicit CPU wheel source for torch, not CUDA packages. Dependency resolution and
  CPU wheel availability are implementation checks, not verified by this plan.
  If incompatible, stop and report rather than silently select a different model.
- **Storage**: Additive migration `004_local_ranking.sql`; no pgvector dependency,
  embedding table, persisted vectors, or changes to migrations 001–003.
- **Testing**: Existing pytest/HTTPX/Playwright/Ruff and guarded disposable PostgreSQL.
  Fake vectors and stub model loader in the repeatable suite; actual installed-model
  inference is a separate offline integration/benchmark run, never a live API test.
- **Scale**: 1–250 unique papers plus one context input; one CPU ranking job per app
  process. Reject simultaneous ranking work with a recoverable busy error rather
  than queue an unbounded number of CPU jobs. Other projects may still retrieve.
- **Deadlines (approved with plan)**: Retain OpenAlex limits (20 requests, two
  concurrent, 10 seconds/request, 120 seconds retrieval). Give local model loading
  plus inference 60 seconds, and the pre-commit pipeline 210 seconds overall;
  extend new search leases to 240 seconds. Final ownership checks remain mandatory.
- **Performance (approved protocol, not measured)**: On the previously approved Ryzen 7 5700X3D / 31 GiB
  Linux reference host, offline 251-input ranking including child/model startup:
  p95 <30 seconds; 3 warm-ups and 20 sequential timed jobs. Each paper input is long
  enough to reach the 256-token limit. Exclude download, HTTP, and PostgreSQL;
  separately retain existing fake-provider storage benchmarks without presenting
  them as model latency. Record peak child RSS and host load without a fabricated
  memory acceptance limit. No measured performance is claimed yet.

## Constitution Check

Pre-design and post-design assessment against constitution 2.0.0:

| Principle | Assessment |
|---|---|
| I — Provider facts | PASS: OpenAlex remains the only metadata source; embedding vectors never populate paper metadata. No generative model call added. |
| II — Validated output | PASS: validate structured vector batches, identities, coverage, finite values and dimension; no prose parsing or new LLM prompt. |
| III — Interfaces | PASS: domain/service depend on EmbeddingProvider, not sentence-transformers/torch/Hub. Integration and setup own vendor imports. |
| IV — Query control | PASS: reuse exact enabled-query snapshot; ranking uses snapshotted question/keywords, never changes saved queries. |
| V — Transparency | PASS: scores/provenance/disclaimers visible; pending/failure and ownership retained; no partial commits. |
| VI — Tests/evidence | PASS at design level: red-first business tests, full suite, traceability, offline audit and separate human quality review required. |
| VII — Scope/simplicity | PASS at design level: approved 004 only, existing stack extended; required ML dependencies justified above. Human gates retained. |

PostgreSQL, environment-only configuration/secrets, same-origin local deployment,
and sanitized errors/logs remain mandatory. Ranking is a deterministic embedding
operation, not new runtime generative LLM use. No constitutional amendment needed.
These are design assessments, not runtime verification. Human plan/contract approval
was recorded on 2026-10-21; implementation still requires task approval.

## Project Structure

```text
specs/004-relevance-ranking/
  spec.md, plan.md, research.md, data-model.md, quickstart.md
  contracts/api.md, contracts/embedding.md
backend/researchpilot/
  ranking_domain.py                 # normalization, validation, cosine, ordering
  embedding_provider.py             # vendor-free protocol/results/errors
  integrations/local_embeddings.py  # offline loader + bounded child worker
  integrations/setup_embeddings.py  # explicit one-time network setup only
  retrieval_service.py, paper_domain.py, api.py, persistence.py
backend/tests/
  test_ranking.py, test_local_embeddings.py, test_ranking_api.py
  test_ranking_postgres.py, test_ranking_browser.py, test_ranking_performance.py
migrations/004_local_ranking.sql
frontend/{index.html,app.js,styles.css}
```

Reuse existing fixtures and fake-provider test patterns; introduce no production
fake mode or new standalone server. `tasks.md` is a later, separate gate.

## Design decisions

### Model and offline setup

Pin model `sentence-transformers/all-MiniLM-L6-v2` to revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (public model metadata inspected
2026-10-21). Expected vector dimension: 384. Maximum sequence length: 256 tokens
including special tokens; right-side truncation, no chunking or hidden summarization.

Implement an explicit setup CLI under the integration module. Download only model
safetensors, tokenizer/config files and the declared standard pooling configuration;
no pickle weights, remote Python, alternative backends, or training assets. Retain
Apache-2.0 license/model-card information. Use a staging directory and write the
completion manifest last; refuse to overwrite an existing incomplete/different
installation without an explicit repair decision. The manifest records revision and
SHA-256 of each accepted file; validate it before loading. This is integrity against
accidental changes, not protection from an attacker controlling the local machine.

Use ignored `.models/all-MiniLM-L6-v2/<revision>/` by default; allow a server-only
`EMBEDDING_MODEL_DIR` environment override for that same pinned installation, not an
arbitrary model ID/URL. Never return the filesystem path to the browser. Setup is the
only embedding-related network path; it sends no project/paper text, uses no account
token (`token=False`), and disables telemetry/implicit token use.

Runtime forces offline flags before any ML imports, uses local absolute paths,
`local_files_only=True`, `trust_remote_code=False`, safetensors-only loading,
`device='cpu'`, float32 inference, model evaluation mode, no gradients, batch size 32,
at most four PyTorch CPU threads and one interop thread. Disable progress bars,
telemetry and implicit Hub credentials. A missing installation does not prevent the
app opening/reading old results; a new search fails safely when ranking is required.

### Bounded execution

The adapter spawns a short-lived local child process for each nonempty ranking
batch, loads only verified files, and returns structured vectors/token hashes. This
keeps native CPU work off the event loop and permits actual terminate/join/kill on
timeout or cancellation. A timed-out `asyncio.to_thread` alone cannot stop PyTorch.
Acquire one process-local ranking slot without waiting; busy attempts fail safely.
Always release the slot and reap the child, including shutdown/error paths. No DB
transaction spans ranking; no child may commit data or emit raw input/tracebacks.
No model/vector cache, process pool, daemon service, or background retry is needed.

### Normalized inputs and provenance

Use `NFC` then whitespace collapse (`' '.join(text.split())`) on each supplied text;
do not remove punctuation or case-fold the input. Context is normalized research
question, followed, if present, by `\nKeywords: ` plus normalized nonblank keywords
joined by `; ` in stored order. Paper input is normalized title, followed by `\n`
and normalized abstract only if nonblank. Do not add query text or other metadata.
These separators form part of versioned input format `ranking-input-v1`.

Hash the exact joined UTF-8 string with SHA-256 before tokenization. Also retain a
SHA-256 of canonical JSON encoding of the actual unpadded truncated token-ID list
(including special tokens), the token count, and whether truncation occurred.
The adapter must encode those same tokens, not tokenize under a different policy.
This distinguishes the complete normalized input from the actual model input;
tokenizer/model revision and input version make the policy auditable.

Accept exactly one vector for each ordered input ID, with no duplicates/extras,
all finite numeric components (not booleans), common dimension >0 (384 for this
adapter), and validated provenance. Use numerically stable cosine computation;
zero norms yield 0. Apply the approved clamp/round formula and sort descending
rounded score, then `title.casefold()`, then `(provider, provider_id)`.
Hashing/score algorithms belong in domain helpers, not vendor code. No vector is
persisted or logged; no raw input, model path, or native exception text is logged.

### Search integration and legacy results

Capture research question/keywords in the service's in-memory attempt snapshot as
well as existing persisted snapshot. Retrieve → normalize/deduplicate → rank →
validate ownership → commit provider metadata, ordered associations, score/provenance
and run success in one transaction. Any failure leaves old metadata/associations/
scores untouched. Existing parent-first locks and lazy expiry continue to apply.
Do not translate ranking errors into misleading OpenAlex errors.

An empty successful retrieval skips the model entirely and commits empty results,
even if the model is absent; no fabricated dimension or model-used provenance.
Older 003 results survive migration with null score/provenance, retain their old
order, and show “Not ranked — search again to rank locally.” A GET, startup or
migration must never automatically rerank or download a model. After an explicitly
successful new nonempty search, every current paper has score and provenance.

See [data model](data-model.md), [API contract](contracts/api.md), and
[embedding contract](contracts/embedding.md) for fields and error semantics.

### UI and verification

Show percentage `score * 100` to one decimal, label “Embedding similarity”, and
explain provisional calibrated cosine—not probability or scientific quality. Show
local model/revision, English focus, 256-token truncation policy and per-input
truncation indication. Keep safe provider metadata/links and all low-score results.
Pending includes retrieval plus local ranking; do not invent stage polling/history.

SC-RNK-003 protocol: freeze at least 20 provider-derived papers for one user-chosen
question, mixed potentially relevant/unrelated/title-only records. Record snapshot
hashes/provenance. The human labels 0/1/2 (unrelated/partial/direct) before inspecting
scores; never use AI labels as human evidence. Report top-five label distribution,
nDCG@10 where defined, ties/saturation and concrete misorderings versus original
retrieval order. No numerical accuracy pass threshold is invented. Human judgement
of usefulness and explicit feature acceptance remain required; without labels report
the evaluation pending. Synthetic fixtures test logic only, never supply real papers.

## Requirement-to-Test Mapping

| ID | Required evidence (proposed, not executed) |
|---|---|
| FR-RNK-001 | `test_ranking.py`: exact NFC/whitespace/separators/order/missing abstract; API snapshot uses initial question/keywords |
| FR-RNK-002 | Domain/adapter tests for missing/extra/reordered IDs, invalid numeric types, NaN/Inf, dimension mismatch and overflow-safe cosine |
| FR-RNK-003 | Formula boundary/clipping/zero-norm fixtures; AC-RNK-001; no accuracy inference |
| FR-RNK-004 | Score/title/source tie tests, API/postgres/browser persisted ordering |
| FR-RNK-005 | Browser retains all papers, 0% and clear algorithmic disclosure; AC-RNK-003 |
| FR-RNK-006 | Migration/restart and API provenance tests; exact text/token hashes, no stored vectors |
| FR-RNK-007 | Provider/invalid-output/commit/timeout/cancellation/busy/stale-ownership rollback tests; AC-RNK-004 |
| FR-RNK-008 | Adapter child with outbound sockets blocked; no text/credential canaries in logs/HTTP; OpenAlex mock path unchanged |
| FR-RNK-009 | Setup mock tests, revision/file validation, missing/corrupt files, local-only loader flags, safe child cleanup; browser English/truncation disclosure |

Full 001–004 suite must pass; update migration-count assertions and fake injection
without disabling new ranking behavior. Keep guardrails on disposable DB cleanup.
Run local real-model inference with outbound network denied after explicit setup;
record actual results separately from fake-vector tests and the human evaluation.

## Complexity Tracking

No constitutional deviations. A short-lived managed child process is the minimum
extra execution boundary needed to terminate native inference on timeout; it is
not a separate service. CPU-only ML packages are necessary for the approved local
model; no speculative storage/backend dependencies are proposed.
