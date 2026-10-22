# Ranking usefulness review — pending human input

**Status**: Protocol prepared; no frozen dataset or human labels collected yet.
No ranking accuracy/usefulness acceptance is claimed by automated test success.

## Required review

1. User chooses one research question and at least 20 existing provider-derived
   papers spanning potentially relevant, unrelated and title-only records. Use
   available provider snapshots or separately authorized OpenAlex retrieval; never
   invent metadata or call a provider silently to fill the dataset.
2. Freeze question/keywords, ordered provider Paper snapshots, original retrieval
   order and SHA-256 hashes. Record provider/DOI/URL provenance and model/revision,
   input/truncation/scoring versions. Keep any private research content local unless
   the user explicitly approves including it in repository evidence.
3. Before inspecting scores, the user labels each paper 0 (unrelated), 1 (partially
   relevant) or 2 (directly relevant). No AI-generated labels reported as human.
4. Run local ranking on frozen inputs; retain ranked IDs/scores, top-five label
   distribution, nDCG@10 (gain `2**label - 1`, logarithmic rank discount) where ideal
   DCG is nonzero, tied/saturated scores and concrete misorderings compared with
   retrieval order. If ideal DCG is zero, report nDCG undefined, not perfect/zero.
5. Ask whether ordering helps the user's discovery work. Report negative findings
   and truncation/English limitations; do not change approved calibration to improve
   the example without a reviewed requirement/prompt/version change.

## Outstanding

- User-selected question and provider-derived frozen dataset.
- Blind human 0/1/2 labels and actual metrics/findings.
- Explicit human usefulness judgement, keyboard/usability review and final acceptance.

The synthetic benchmark inputs and deterministic fake vectors are not substitutes
for this review. No project data has been copied into this evidence file.
