# Evidence log

## Artifact preparation — 2026-10-11

- User request (verbatim): "okay. can you create the SDD stuff from the current vibecoded version?"
- Prior steering: use a smaller subset; select GitHub Spec Kit; preserve course-report template.
- Agent: OpenCode; session-reported model `openai/gpt-6.1-sol`.
- Activity: inspect source documentation/domain rules and installed templates; derive
  five draft specs and first-slice plan/tasks/contracts; propose constitution amendment.
- This is direct artifact preparation, not recorded execution of Spec Kit commands.
- Existing constitution and original implementation were not modified.
- No runtime app or tests exist in this rebuild yet; no implementation outcome recorded.
- Installed Spec Kit version, baseline dirty-state audit, team identity and approval: pending.

### Documentation consistency check

Ran a Python check over 19 Markdown files: local Markdown links resolved, all five
specifications contained the required scenario/requirement/success/assumption headings,
43 requirement IDs were unique, and `.specify/feature.json` resolved to an existing spec.
Result: PASS. This checks artifact structure only, not semantic completeness or runtime
correctness. Application tests were not runnable because no implementation exists.

## Repository setup and SDD continuation — 2026-10-11

- User request (verbatim): "We have setup the SDD. Now setup the github repo, private repo mind you, then start continue working on the SDD"
- Initialized this rebuild as a Git repository on `main`; original repository untouched.
- Target GitHub repository: `mgustafsn/ResearchPilot-SDD`, explicitly private.
- Created and pushed the initial commit `0ef298b`. `gh repo view` confirmed
  `visibility: PRIVATE`, `isPrivate: true`, and default branch `main`.
- Added root ignore rules for local environment files, credentials, and runtime artifacts.
- Pre-publication scan of 50 staged files for common credential/private-key patterns:
  PASS, no matches. This limited pattern scan is not a comprehensive security audit.
- Began `speckit-clarify` for active feature 001. Constitution amendment and feature
  approval remain pending; this request is not recorded as their ratification.
- Ran `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` successfully;
  it resolved `specs/001-project-management/spec.md`. `.specify/feature.json` remains
  deliberately machine-local under the installed Spec Kit ignore rules.
- No application tests executed: this checkout still contains planning artifacts only.

## Decision log

| Date | Decision/proposal | Approver | Status | Affected artifacts |
|---|---|---|---|---|
| 2026-10-11 | Reduced discovery MVP | User chose smaller subset; detailed boundaries pending | Proposed | docs/scope.md; specs/001–005 |
| 2026-10-11 | Constitution amendment for reduced scope | Pending | Blocked | docs/constitution-amendment.md |

## Prompt iteration record template

| ID/date | Feature/requirement | Exact prompt and context artifact versions | Model/tool version | Expected output | Actual output/evidence | Failure | Revised prompt | Outcome |
|---|---|---|---|---|---|---|---|---|

Attach full significant prompts or link committed prompt files. Do not reconstruct
missing original prompts as quotations. Save representative responses/diffs.

## Audit record template

| ID/date | Commit/requirement | Human/AI reviewer | Issue and evidence | Severity | Fix/diff | Regression test | Remaining limitation |
|---|---|---|---|---|---|---|---|

## Test execution record template

| Run/date | Commit/env/tool versions | Test/requirement IDs | Exact command | Expected | Actual | Pass/fail | Log/artifact | Defect/fix |
|---|---|---|---|---|---|---|---|---|

Record totals/coverage from actual output only, including failures. Documentation
consistency checks are not application verification or acceptance results.

## Contribution record template

| Member | Student ID | Role | Issues/commits/reviews | Evidence-backed contribution % |
|---|---|---|---|---|

Personal identifiers and percentages remain unfilled until supplied and agreed by the team.
