# Feature Specification: Semantic relevance ranking

**Feature Branch**: Proposed `004-relevance-ranking` (not created)
**Created**: 2026-10-11
**Status**: Specification approved by the user on 2026-10-21 (reply: “I apprvove”), including provisional score mapping. Plan/supporting design/contracts separately approved on 2026-10-21 (reply: “I approve”). Tasks/implementation authorized on 2026-10-21 (reply: “Start”).
**Input**: Retain embedding ranking without clustering or automatic result filtering.

## Clarifications

### Session 2026-10-21

- Q: Does “everything local” mean ranking only, or also stopping OpenAlex searches? → A: Ranking must run locally without an external embedding service; OpenAlex may continue making real searches (user: “OpenAlex can do real searches yes”).
- Q: Do you approve `sentence-transformers/all-MiniLM-L6-v2` and a one-time download during explicit setup? → A: “I approve”. Model/setup design approved: CPU-local inference, pinned model revision, local-files-only runtime loading, no automatic downloads or telemetry, and explicit errors preserving previous results if the model is unavailable or ranking fails. Implementation remains a separate gate.
- Q: Do you approve this specification, including the provisional score mapping? → A: “I apprvove”. Specification approved; technical planning may proceed, but implementation requires separate approval.

## User Scenarios & Testing

### User Story 1 — Browse ranked results (Priority: P1)

**Why this priority**: Users need a reproducible way to prioritize papers.
**Independent Test**: Seed normalized papers and fixed embedding vectors, then inspect ranking.
**Acceptance Scenarios**:
1. **Given** fixed vectors, **When** scoring runs, **Then** scores match the specified formula and results descend by score (AC-RNK-001).
2. **Given** a paper without an abstract, **When** scoring runs, **Then** its title is used without invented text (AC-RNK-002).
3. **Given** low-scoring papers, **When** viewing results, **Then** they remain visible and their score is labeled as similarity, not correctness probability (AC-RNK-003).
4. **Given** previous results, **When** embedding fails, **Then** the attempt fails and old results remain (AC-RNK-004).

### Edge Cases

Zero-norm vectors; mismatched dimensions; nonfinite values; missing vectors; identical
scores/titles; empty result set; provider model change between attempts.

## Requirements

### Functional Requirements

- **FR-RNK-001**: Obtain vectors through EmbeddingProvider for normalized question plus keywords and each paper's title plus available abstract. Document exact normalization in the plan.
- **FR-RNK-002**: Require finite vectors of a common nonzero dimension and complete output coverage; reject malformed output before committing results.
- **FR-RNK-003**: Compute cosine similarity. A zero-norm vector yields cosine 0. Score = round(clamp((cosine − 0.25) / 0.35, 0, 1), 6). This retains baseline calibration provisionally, as approved on 2026-10-21; it is not validated for the selected local model or as a universal relevance measure.
- **FR-RNK-004**: Sort descending score, then case-folded title, then stable source identity. This approved behavior simplifies baseline lexical tie-breaking.
- **FR-RNK-005**: Show every retrieved unique paper and its score as a percentage labeled embedding similarity; MUST NOT automatically remove papers below 40%.
- **FR-RNK-006**: Persist scores with the successful attempt plus model identity, vector dimension, scoring version, and exact normalized input hashes. Embedding caching is out of scope.
- **FR-RNK-007**: Ranking MUST finish before atomic result replacement. On provider failure/invalid vectors, fail without silent fallback or loss of previous results.
- **FR-RNK-008**: Generate embeddings and compute ranking locally. Do not send research questions, keywords, paper titles, or abstracts to an external embedding service or require a cloud embedding API key. Explicit OpenAlex retrieval remains permitted under feature 003; this does not authorize external AI services.
- **FR-RNK-009**: Use `sentence-transformers/all-MiniLM-L6-v2` behind EmbeddingProvider with CPU-local inference. Permit a one-time model download during explicit setup; pin the exact model revision in the reviewed plan. Runtime loading MUST use local files only, without automatic downloads or telemetry. Missing model files MUST produce a readable error and preserve previous results, with no cloud fallback. Disclose the model's English-language focus and truncation of long inputs; define the exact input/token-limit policy in the plan.

### Key Entities

ProjectPaper gains score and input/model provenance. SearchRun gains scoring version.
Vectors may remain transient; provenance is persisted for audit, not a promise of
reproducing future live-provider outputs.

## Success Criteria

- **SC-RNK-001**: AC-RNK-001–004 pass with deterministic vector fixtures.
- **SC-RNK-002**: Cosine values 0.25, 0.425, and 0.60 map to scores 0, 0.5, and 1; clipping and invalid-vector tests pass.
- **SC-RNK-003**: Evaluate a frozen, human-labeled paper set separately from correctness tests; report ranking usefulness without a fabricated accuracy target.

## Assumptions

Depends on 003. Calibration inherits baseline constants, not evidence of scientific
validity. The user approved `sentence-transformers/all-MiniLM-L6-v2` and a one-time
download during explicit setup on 2026-10-21. This approves the model/setup design,
not implementation or immediate installation/download. Exact revision, dependencies,
input truncation policy, performance budget, and ranking-quality evaluation criteria
need review in the technical plan. Existing score calibration is approved only
provisionally and is not validated for this model. The specification as a whole
was approved on 2026-10-21; plan, contracts, tasks, and implementation remain
separate gates; plan/supporting design/contracts approved on 2026-10-21, tasks
and implementation subsequently authorized on 2026-10-21 (reply: “Start”). Human
usefulness evaluation and final acceptance remain pending; approval of provisional
calibration is not validation of ranking accuracy.
