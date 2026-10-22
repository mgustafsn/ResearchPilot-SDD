# Local ranking design rationale

**Date**: 2026-10-21 | **Status**: Supporting rationale approved with the plan on 2026-10-21; not a benchmark or compatibility verification.

## Model and file policy

- **Decision**: Approved MiniLM model, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, CPU float32, 384 dimensions,
  max 256 tokens. Explicit setup download; local-only runtime.
- **Rationale**: Model card documents English, short-paragraph embeddings and
  truncation. Fixed revision plus file/token hashes makes provenance meaningful.
- **Alternatives**: Cloud embedding API violates user preference. Another model,
  scientific-model fine-tuning, ONNX/OpenVINO quantization and chunking are not
  necessary to implement the approved first slice. No automatic model substitution.

## Dependencies and security

- **Decision**: Sentence Transformers 6.2.0 (PyPI metadata), compatible locked
  CPU-only torch and directly declared Hub download utility. Safetensors only,
  trust_remote_code false, no implicit credentials/telemetry, standard modules only.
- **Rationale**: Reuse the model's defined tokenizer/pooling instead of maintaining
  a bespoke inference pipeline. Dependency resolution/import compatibility remains
  an implementation verification step; no packages were installed in this review.
- **Alternatives**: Handwritten torch pooling saves a wrapper but risks drifting
  from model configuration; separate local model server adds unnecessary deployment.

## Worker lifecycle

- **Decision**: One nonqueued child-process ranking slot per app process, new child
  per search, hard timeout/cancellation cleanup. Proposed budgets are in the plan.
- **Rationale**: Thread cancellation cannot interrupt native inference; stale write
  rejection alone does not prevent CPU work continuing after failure. Per-job model
  loading costs latency but keeps cleanup/lifecycle simple and measurable.
- **Alternatives**: Persistent workers or model memory caches add restart/poisoned
  worker management before performance evidence shows a need. Unbounded parallel
  CPU inference threatens local responsiveness.

## Provenance and existing data

- **Decision**: Nullable additive fields for old results, no backfill/rerank on GET;
  full-text and actual truncated-token hashes, no persistent vectors.
- **Rationale**: Preserve accepted feature-003 data honestly, while proving which
  part of long inputs the model actually consumed. Metadata remains provider-owned.
- **Alternatives**: Inventing zero scores or claiming all abstract tokens were used
  would misrepresent legacy data and input coverage. Embedding caches are excluded.

## Evidence and quality

- **Decision**: Keep approved provisional formula; separate deterministic logic
  verification, real offline model performance, and human-labeled usefulness review.
- **Rationale**: Neither model-card examples nor unit tests establish usefulness on
  the researcher's topic. Labeling before scores reduces confirmation bias.
- **Alternatives**: Universal accuracy claims, inherited threshold validation, and
  AI-generated human labels are unsupported. Recalibration needs a later reviewed
  change, not a hidden adjustment while implementing the approved spec.

## Sources inspected

Public documentation/metadata fetched on 2026-10-21; no project/paper text sent,
no model weights downloaded, no scholarly facts generated from these sources.

- [Model metadata](https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2): revision, public/ungated status, safetensors presence, Apache-2.0 metadata.
- [Model card at pinned revision](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md): the fetched main card describes 384 dimensions and 256-wordpiece truncation; verify pinned assets in setup.
- [SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html): CPU device, local_files_only, revision, trust_remote_code, encode parameters.
- Pinned revision's `sentence_bert_config.json`, `modules.json`, and `1_Pooling/config.json`: verified 256-token limit, 384-dimensional mean pooling and standard Transformer → Pooling → Normalize chain. Normalize requires no extra weights/config file. These configuration reads are not a weights download or inference test.
- [PyPI package metadata](https://pypi.org/pypi/sentence-transformers/json): version 6.2.0, Python >=3.10; torch metadata reports 2.14.1 and Hub 2.2.0. This is metadata discovery, not compatibility or supply-chain certification.
- Existing retrieval service, API, domain, schema, fixtures and constitution 2.0.0.

No unresolved product-choice placeholder remains in this design. Budgets,
contracts and execution choices were approved with the plan; actual compatibility,
performance and human quality labels are verification obligations, not assumed facts.
