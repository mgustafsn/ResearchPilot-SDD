# Feature Specification: Semantic relevance ranking

**Feature Branch**: Proposed `004-relevance-ranking` (not created)
**Created**: 2026-10-11
**Status**: Draft — human approval required
**Input**: Retain embedding ranking without clustering or automatic result filtering.

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
- **FR-RNK-003**: Compute cosine similarity. A zero-norm vector yields cosine 0. Score = round(clamp((cosine − 0.25) / 0.35, 0, 1), 6). This retains baseline calibration; it is not a validated universal relevance measure.
- **FR-RNK-004**: Sort descending score, then case-folded title, then stable source identity. This simplifies baseline lexical tie-breaking and is a proposed change.
- **FR-RNK-005**: Show every retrieved unique paper and its score as a percentage labeled embedding similarity; MUST NOT automatically remove papers below 40%.
- **FR-RNK-006**: Persist scores with the successful attempt plus model identity, vector dimension, scoring version, and exact normalized input hashes. Embedding caching is out of scope.
- **FR-RNK-007**: Ranking MUST finish before atomic result replacement. On provider failure/invalid vectors, fail without silent fallback or loss of previous results.

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
validity. Model choice and ranking-quality evaluation criteria need review.
