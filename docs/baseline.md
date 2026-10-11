# Baseline provenance

Recorded: 2026-10-11.

- Source checkout: `../ResearchPilot` (read only during artifact preparation).
- HEAD: `8d85fce179c0d746879fdd16b640839782ef6885`.
- This identifies HEAD, not a clean-tree assertion. Working-tree differences have not
  been audited and the baseline has not yet been frozen as an experiment snapshot.
- Product intent: `../ResearchPilot/docs/requirements.md`.
- Delivery history: `../ResearchPilot/docs/roadmap.md`.
- Current behavior description: `../ResearchPilot/README.md`.
- Validation fields: `../ResearchPilot/backend/researchpilot/domain.py`.
- Metadata/provider contracts: `../ResearchPilot/backend/researchpilot/papers.py`.
- DOI/title normalization and semantic calibration:
  `../ResearchPilot/backend/researchpilot/analysis.py`.
- Stack: `../ResearchPilot/pyproject.toml`.
- Existing promptbook location: `../ResearchPilot/docs/prompts.md` (not inspected or
  evaluated in this preparation; audit it before citing historical prompts).

The roadmap says no MVP work remains planned, while the README mentions remaining
acceptance/logging work. Do not treat either status claim as independent proof.
Only the reduced specifications govern the intended rebuild after approval.

No baseline tests, live provider calls, security audit, speed measurements, or
user acceptance sessions were conducted in this preparation. No team identities,
contributions, historical model usage, or development outcomes have been inferred.
