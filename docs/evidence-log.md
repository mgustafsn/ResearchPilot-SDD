# Evidence log

## Feature 004 GitHub Actions verification — 2026-10-22

- Commit `64fe96a35b8eb8d58f7e1075a03ad4c68765f0d9` was pushed to the existing
  private GitHub repository. GitHub Actions run [39827940845](https://github.com/mgustafsn/ResearchPilot-SDD/actions/runs/39827940845)
  completed successfully on Ubuntu 24.04 with PostgreSQL 17 and Python 3.12.
- CI passed locked dependency setup, browser installation, `ruff check backend`,
  `node --check frontend/app.js`, and `uv run pytest -m "not performance" -q`:
  **423 passed, 4 deselected in 51.40s**. Performance-marked tests were
  intentionally excluded; real-model/reference-host benchmarking remains separate.
- This verifies the GitHub workflow for this commit. GitLab pipeline status is a
  separate, still-unverified check. No prompt, runtime, or requirement changes were
  made to record this result.

## Feature 005 specification and plan preparation — 2026-10-22

- The user approved the Feature 005 specification for planning (reply: “Approve
  spec for planning”). This approves the specification only. Recorded that gate in
  `specs/005-saved-references/spec.md` and `docs/scope.md`.
- Read constitution 2.0.0, the approved Feature 005 spec, current normalized Paper
  model, project/search locking, migration conventions, and prior feature plans.
  Prepared `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`, and
  `quickstart.md` for review. No task list, migration, runtime code, or new
  dependency was created; implementation remains unauthorized.
- Proposed design uses one additive JSONB snapshot table with provider identity
  uniqueness, no FK to mutable search/paper rows, current-result-only saves,
  project-row locking, active-search save rejection, project-scoped listing/removal,
  and explicit project-delete cascade. No performance budget was invented.
- No application tests, OpenAlex calls, or ranking labels were run/collected.
  Ranking review retrieval awaits the user's research question. Local app was
  started with the existing model and PostgreSQL; `GET /` returned HTTP 200. This
  is setup evidence only, not human usability/acceptance evidence.

## Feature 005 plan approval and task preparation — 2026-10-22

- User reviewed the plan/supporting design and said: “I reviewed, every thing
  looks good. I think we can start feature 005”. Recorded plan/design approval in
  `specs/005-saved-references/`; this is not inferred as approval of unseen tasks.
- Prepared a 19-task test-first implementation sequence in
  `specs/005-saved-references/tasks.md`, mapping FR-REF-001–008,
  AC-REF-001–004, and SC-REF-001–003. Tasks cover strict snapshots, migration,
  idempotent concurrent writes, current-result ownership, active search behavior,
  project isolation, safe UI, audits, and actual evidence.
- Task list is a draft for separate human review. No Feature 005 source code,
  migration, or tests were added or run; no runtime implementation is claimed.
  `git diff --check` was run for documentation whitespace only.
- Ranking usefulness review remains blocked on the user's exact research question;
  the user authorized an OpenAlex retrieval for that review but has not supplied the
  question. No OpenAlex request or human label was made.

## Feature 005 task approval and implementation start — 2026-10-22

- User reviewed and approved the 19-task Feature 005 checklist (reply: “I reviewed
  and I approve”). Implementation authorization is limited to approved Feature 005.
- Starting with T001 baseline verification against the guarded disposable test
  database. Preserve all existing uncommitted documentation/evidence changes.
- T001 completed: `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file
  .env pytest -q --tb=short` on Python 3.13.15: **426 passed, 1 skipped in
  52.52s**. The first sandboxed run failed to connect to local PostgreSQL; the
  identical guarded run with authorized local-network access passed. No code was
  changed before the baseline; application database was not reset.

## Feature 004 initial user observation — 2026-10-21

- User reported: “Yep it ranks now”. Recorded as user-observed ranking behavior
  in the local app, not independent observation, a judgment of ranking usefulness,
  blind human labels, or explicit final feature acceptance. T026/T029 remain pending.
- No code, prompts, requirements or test outcomes changed; no application tests
  rerun for this documentation-only update.

## Feature 004 implementation and local verification — 2026-10-21

- User authorization: “Start”, answering “Approve tasks and start implementation?”
  Recorded task approval and implementation permission for 004 only. Loaded
  `speckit-implement`; prerequisite command with `--json --require-tasks
  --include-tasks` passed. No feature-004 checklist directory or extension hooks
  exists. No delegates used. Actual branch `main`, starting commit
  `5c78d19302071f550a03b7ced8fb2eb4814c5f0e`; prior acceptance/planning changes
  preserved. Constitution 2.0.0 is ratified; no unresolved amendment blocker.
- Baseline: `UV_CACHE_DIR=/tmp/opencode/uv-cache uv run --env-file .env pytest -q
  --tb=short`: **358 passed, 1 existing warning in 43.26s**. Disposable PostgreSQL
  container healthy; no production/original database reset. Existing cleanup table
  allowlist/target guards retained unchanged.
- Dependency commands `uv lock` and `uv sync` (same UV_CACHE_DIR): PASS; 33 new
  packages installed. Python 3.13.15; sentence-transformers 6.2.0; torch
  2.14.1+cpu, `torch.version.cuda is None`; Hub 2.2.0; transformers 5.20.2;
  tokenizers 0.23.3. Major reported download sizes: torch 187.2 MiB, NumPy
  15.9 MiB, SciPy 33.7 MiB, transformers 12.2 MiB, scikit-learn 8.7 MiB,
  SymPy 6.0 MiB, tokenizers 3.2 MiB, HF Xet 4.0 MiB, NetworkX 2.0 MiB.
  uv fell back from hardlinks to copies across filesystems; installation succeeded.
  Offline/telemetry-disabled import check passed, without model download.

### Tests-first and implementation evidence

- RUN-RNK-RED-001: pure/schema suite (`backend/tests/test_ranking.py` and
  `backend/tests/test_ranking_postgres.py`, `-q --tb=no`): **37 failed** (30 pure
  rules raised intentional NotImplementedError; 7 schema behaviors absent). After
  implementation: same command with short tracebacks **37 passed in 0.79s**.
- RUN-RNK-RED-002: `uv run pytest backend/tests/test_local_embeddings.py -q
  --tb=no`: **14 failed** on unimplemented setup/loader/worker behavior. Adapter
  green: **14 passed in 1.24s**. Timeout/crash/busy/cancel tests use child workers;
  setup downloads are mocked and partial user files are preserved.
- RUN-RNK-RED-003: ranking API/browser files with guarded DB: **10 failed** because
  score/provenance, embedding failure handling and UI were absent. Focused initial
  integration run: **59 passed, 1 failed**; successful empty search exposed JSONB
  null versus SQL NULL and was corrected using SQL null for empty run provenance.
- AUD-RNK-IMPL-001: JSONB `None` serializes as JSON null under reflected SQLAlchemy
  types, violating the object-only provenance constraint. Fixed only empty-success
  assignment; test proves empty results succeed without invoking a missing model.
- AUD-RNK-IMPL-002: whole-search deadline was initially labeled EMBEDDING_TIMEOUT.
  Added a failing deadline test (focused run **20 passed, 1 failed**), then corrected
  it to SEARCH_TIMEOUT when the overall budget is exhausted.
- Supplemental score/tie/0%-retention, actual PostgreSQL commit rollback, ranking
  barrier/expired-owner replacement/cancellation and browser refresh/truncation
  regressions were added after initial integration. This deviates from T013's strict
  author-before-T017 order; no prior red run is claimed for behavior already present.
  Primary domain/setup/API/UI behavior tests did precede production logic.
- Intermediate broad runs: **416 passed, 3 deselected** before added regressions;
  then **420 passed, 1 failed, 4 deselected** due to a test calling asyncio.run after
  Playwright left a loop active. Reused existing `run_async` fixture helper; this
  was a test-harness fix, not a product behavior change. Focused safety rerun:
  **35 passed in 4.33s**.
- Implemented FR-RNK-001–009: NFC/versioned inputs, validated common structured
  vectors, stable cosine/calibration/order, provider-only metadata, durable score/
  input/token/model/run provenance, null legacy scores, atomic fail-preservation,
  model missing/busy/invalid/timeout errors, bounded reaped offline CPU worker,
  explicit setup and local scores/disclosures. No prompt changes or LLM calls.
- Added top-level current-result rankingProvenance to GET papers, matching the
  existing POST provenance, so old model/context-truncation disclosure survives a
  later failed attempt. Documented this additive API detail in the contract; no
  new route, external data flow, metadata source or user behavior is introduced.

### Security/architecture review and actual model setup

- Reviewer: OpenCode / GPT-6.1 Sol, static/AI review, not independent human
  certification. AST import scan found no sentence-transformers/torch/Hub imports
  outside integrations. No frontend innerHTML, model files excluded from Git/Docker,
  only additive migration 004, provider metadata stays distinct from project scores.
  Runtime model loading uses verified local safetensors, exact standard module
  chain, no remote code, CPU-only, no implicit tokens or telemetry. Child blocks
  socket connect/connect_ex and DNS; no raw inputs/vectors/paths/native exceptions
  are emitted by the worker. Source/log review and API canary tests pass.
- Ownership/failure review: no DB transaction spans inference; one nonqueued CPU
  slot per application provider; children terminated/reaped on timeout/cancel/close;
  final lease/token/deadline checks gate atomic score/provider/result writes.
  Tests cover stale commits, rollback and unchanged old scores. No broad DB/file
  deletion, references, clustering, cache, cloud embedding, hidden app retry or
  original repository change. Setup cleans only its newly owned staging directory.
- CI config now sets offline/telemetry flags and unsets provider/Hub tokens/model
  overrides/real-model benchmark opt-in. Repeatable tests mock downloads/model
  loading; actual model verification is separate. Remote CI was not invoked or
  observed this turn; last known pending/no-runner status remains unverified.
- After mocked tests and static review, explicitly executed
  `PYTHONPATH=backend UV_CACHE_DIR=/tmp/opencode/uv-cache uv run python -m
  researchpilot.integrations.setup_embeddings`: PASS. Installed **11 verified files,
  91,578,415 bytes**, pinned revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0 model-card metadata.
  No account token, project text, paper text or API key sent during setup. Weights
  remain ignored; `.env` unchanged. This is the approved public-model download,
  not a cloud inference call or a live OpenAlex search.

### Final actual verification and remaining gates

- Full application suite after fixes:
  `UV_CACHE_DIR=/tmp/opencode/uv-cache uv run --env-file .env pytest -q --tb=short`:
  **426 passed, 1 skipped in 53.26s**. The skip is the installed-model benchmark's
  explicit opt-in gate. This run includes existing project/query/retrieval timing,
  migrations/restart/concurrency and Chromium regressions, with fake provider data.
- Separate real-model command:
  `UV_CACHE_DIR=/tmp/opencode/uv-cache RUN_LOCAL_EMBEDDING_BENCHMARK=1
  PERFORMANCE_OUTPUT=docs/evidence/ranking-performance.json uv run pytest
  backend/tests/test_ranking_performance.py -m performance -q --tb=short`:
  **1 passed in 211.08s**. Three warm-ups then 20 timed jobs of 251 inputs, all
  actual 384-dimensional embeddings with 256-token truncation, in socket/DNS-denied
  CPU children. Nearest-rank p95 **9,317.18 ms**, peak child RSS **799,476 KiB**;
  raw timings/versions/load/hashes retained in that JSON. Synthetic timing text
  is not scholarly metadata or a human-labeled quality evaluation.
- Environment difference: CPU/RAM still Ryzen 7 5700X3D / ~31 GiB; kernel now
  **Linux 7.2.11-1-cachyos**, previously approved reference **7.2.9-2-cachyos**.
  Reported to user before acceptance claims. Timing is below the plan's 30-second
  target on the current host, but unchanged-reference-environment performance
  acceptance is not claimed. Current inference/domain/test/lock hashes verified
  against the raw benchmark report after subsequent documentation edits.
- Ruff check: PASS; Ruff formatting check of 12 new/formatted feature files:
  PASS (legacy shared files not mass-reformatted). `node --check frontend/app.js`
  and `git diff --check`: PASS. Limited secret/model-ignore and documentation
  checks recorded separately below; none are a comprehensive security certificate.
- Restarted only the agent-launched local Uvicorn PID after confirming exact
  repository command; graceful shutdown observed. `./scripts/start-local.sh`
  restarted successfully, local GET `/` returned **HTTP 200**, and a read-only
  application DB check confirmed schema 001/002/003/004. No project contents were
  read/copied and no live OpenAlex/OpenAI call was made. App remains on
  `http://127.0.0.1:8000/`; new ranking requires explicit user Search.
- T001–T025/T027–T028 implemented/verified (**27/29**); T026 and T029 remain
  pending human quality dataset/labels/usefulness review and final acceptance.
  `docs/evidence/ranking-quality.md` contains the honest pending protocol; no user
  project data, fabricated citations or AI-generated human labels were added.
  Feature 005 remains unauthorized; BUG-PRJ-001 remains deferred. Ranking accuracy,
  remote CI success and final user acceptance are not claimed.
- Final documentation/limited secret scan: PASS for 29 sequential task IDs with
  exactly T026/T029 unchecked, local Markdown links, ignored model directory,
  no tracked/unignored weights and no common private-key/AWS/OpenAI key patterns.
  This bounded pattern scan is not a comprehensive secret/security audit.

## Feature 004 plan approval and task preparation — 2026-10-21

- Asked the user to approve the technical plan and contracts; user answered:
  “I approve”. Recorded plan/supporting design/API/embedding contract approval
  in `specs/004-relevance-ranking/` and `docs/scope.md`, including the plan's
  deadline/performance protocols. This is not task approval or implementation
  authorization; no packages or model weights were installed/downloaded.
- Loaded `speckit-tasks`; `.specify/extensions.yml` absent, so no pre/post hooks.
  `.specify/scripts/bash/setup-tasks.sh --json`: PASS; active feature 004 resolved
  to the reviewed spec/plan and supporting artifacts, with the installed template.
  Constitution VI overrides generic optional-test wording. No delegates used.
- Generated `specs/004-relevance-ranking/tasks.md`: 29 unchecked tasks, comprising
  3 setup, 5 foundations, 13 US1 (6 tests-first, 7 implementation/regression) and
  8 audit/verification/acceptance tasks. Mapped all nine FR and four AC IDs; added
  dependencies, file-independent authoring opportunities and fake-provider
  independent journey. Actual branch remains `main`.
- Tasks preserve red-first tests, additive legacy-safe schema, CPU-only compatible
  dependencies, offline runtime, mock-tested explicit setup before weights download,
  terminated/reaped inference children, atomic ownership/failure safety, safe
  logs/paths and separate actual-model/human-quality evidence. Human labels and
  final acceptance must stay pending without evidence; no excluded scope is added.
- No runtime, prompt, secret or dependency changes; no application tests rerun.
  Documentation assertions and whitespace checks are recorded below separately
  from application verification. Task approval remains the next human gate.
- Documentation assertions: PASS for 29 sequential unchecked IDs, 13 US1 labels,
  task file paths, nine FR/four AC mappings and local Markdown links across feature
  004 artifacts. `git diff --check`: PASS. These do not verify application behavior.

## Feature 004 technical plan preparation — 2026-10-21

- User requested: “Lets go I just want to implement”. Explained the constitution's
  separate plan/task approval gates; proceeded with plan preparation, not inferred
  approval of an unseen plan/task list or implementation.
- Loaded `speckit-plan`; no `.specify/extensions.yml` exists, so pre/post hooks are
  absent. Ran `SPECIFY_FEATURE_DIRECTORY=specs/004-relevance-ranking
  .specify/scripts/bash/setup-plan.sh --json`: PASS; created the plan template and
  advanced the ignored local feature pointer to 004. Actual Git branch remains
  `main`; existing uncommitted acceptance/clarification updates were preserved.
- Read constitution, approved 004 spec, existing retrieval/API/schema/fixtures and
  template. Prepared plan, rationale, data model, API/embedding contracts and
  quickstart in `specs/004-relevance-ranking/`. No task file generated yet.
- Public model documentation/config/PyPI metadata reads identified revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 dimensions, 256-token limit and
  the standard Transformer/mean Pooling/Normalize chain. PyPI reports Sentence
  Transformers 6.2.0. No project/paper text was sent, model weights downloaded,
  inference performed or dependency installed. Resolution/CPU wheels/imports are
  still unverified implementation obligations. No OpenAlex/OpenAI request occurred.
- Proposed managed child-process inference for hard cancellation, one nonqueued
  ranking slot, 60-second local budget, 210-second pre-commit deadline, 240-second
  lease, and reference-host p95 <30 seconds over 20 offline 251-input jobs including
  model startup. These are unapproved proposals, not measured outcomes. Included
  exact normalization/token hashes, legacy null scores, atomic failure preservation,
  per-run provenance and separate human usefulness protocol.
- AUD-RNK-PLAN-001: native inference cannot be stopped by canceling a Python thread;
  plan uses a reaped child instead. AUD-RNK-PLAN-002: normalized text hashes alone
  omit truncation coverage; retain actual consumed-token hashes/counts too.
  AUD-RNK-PLAN-003: model config includes Normalize, so allow the exact three-module
  chain rather than accidentally rejecting the approved installation.
- Constitution I–VII pre/post design checks pass at design level, not verified
  runtime compliance or human plan approval. No delegates used, per repository
  instructions. No runtime/prompt/secret change; no application tests rerun.
- Documentation assertions PASS across seven ranking Markdown files: local links,
  nine unique FR-RNK requirements mapped to planned tests, no unresolved template
  placeholders. `git diff --check`: PASS. These checks are not application or
  ranking-quality verification. Plan/contracts and later tasks await human review.

## Feature 004 specification approval — 2026-10-21

- Presented the complete ranking specification for review: local MiniLM inference,
  question/keywords versus title/abstract inputs, all papers visible, deterministic
  score/title/source ordering, title-only handling for missing abstracts, provenance,
  and atomic failure preservation without silent fallback.
- Explicitly disclosed that the inherited cosine-to-percentage mapping is provisional
  and unvalidated for the local model; embedding similarity is not a correctness
  probability or scientific-quality measure. Exact model revision, dependencies,
  truncation, resource/time budgets, and usefulness evaluation remain technical-plan
  review items.
- Asked: “Do you approve this specification, including the provisional score mapping,
  or want any behavior changed?” User answered: “I apprvove”. Recorded approval in
  `specs/004-relevance-ranking/spec.md` and `docs/scope.md`. Approval permits plan
  preparation only; plan/contracts/tasks/implementation are not approved.
- Documentation-only update: no requirement IDs, prompts, runtime code, dependencies,
  model files, or active feature pointer changed; no external requests or application
  tests ran. `git diff --check` checks documentation whitespace only, not runtime
  correctness or ranking usefulness.

## Feature 004 local model/setup approval — 2026-10-21

- Proposed `sentence-transformers/all-MiniLM-L6-v2` for CPU-local English-language
  similarity ranking, noting long-input truncation and the need to evaluate model
  usefulness/calibration rather than infer accuracy from formula tests.
- Asked: “Do you approve this model and a one-time download during setup?” with
  the explicit boundary “This approves the design choice, not implementation yet.”
  User answered: “I approve”. Recorded the approved model/setup choice as
  FR-RNK-009 and in `docs/scope.md`.
- Approved setup design: explicit one-time download, pinned revision, local-files-only
  runtime without automatic downloads or telemetry, EmbeddingProvider isolation,
  and safe failures preserving prior results. Exact revision/dependencies, token
  limits, performance protocol, and ranking usefulness evaluation remain for review.
  The complete feature specification, plan, tasks, and implementation are not approved.
- No model download, installation, external request, runtime code, dependency,
  prompt, or active-feature-pointer change occurred. Documentation-only update;
  application tests were not rerun. `git diff --check` is the documentation check,
  not application verification.

## Feature 004 local-ranking clarification — 2026-10-21

- User requested: “Yeah no lets no connect to something outside. Lets keep
  everything local”. Asked whether this also prohibits OpenAlex; user clarified:
  “OpenAlex can do real searches yes”. Recorded local-only embeddings/ranking
  as FR-RNK-008 in `specs/004-relevance-ranking/spec.md` and `docs/scope.md`.
- External embedding services are not permitted; explicit OpenAlex retrieval
  remains allowed. No model download, installation, provider call, runtime change,
  prompt change, or dependency change was made. Local model/setup and evaluation
  decisions remain for review; the feature specification and subsequent gates
  are not approved by this clarification.
- Loaded `speckit-clarify`; no `.specify/extensions.yml` exists, so no hooks run.
  Prerequisite paths still resolve feature 003; edited the explicitly discussed
  feature-004 draft without changing the active feature pointer or accepted 003
  requirements. No feature-004 quality checklist exists. One scope question was
  asked and answered; integration/data-sharing ambiguity is resolved. Model/setup
  details are deferred to design review; acceptance/evaluation details remain open.
- Documentation-only update; no application tests rerun and no new runtime
  verification claimed.

## Feature 003 user acceptance — 2026-10-21

- User requested a local launch. The initial launch failed because PostgreSQL was
  stopped; `docker compose up -d --wait db` started the existing container and
  reported healthy. `./scripts/start-local.sh` then started the app; a local GET
  to `http://127.0.0.1:8000/` returned HTTP 200. No provider request was made by
  the agent.
- Presented the retrieval review journey and limitations: editable/enabled queries,
  explicit OpenAlex search, pending/results/error states, source links, count/query
  summary, refresh persistence, and keyboard usability. Ranking and saved references
  are not included. Explained that clicking Search sends queries/filters to OpenAlex.
- User reported “Yep works” and explicitly approved: “accept feature 003”. Recorded
  acceptance and completed T033. This is the user's overall review report, not
  independently observed proof of every manual check or a new automated test run.
- Prior recorded full-suite evidence remains 358 passed with one existing warning
  on 2026-10-19; no application tests rerun for this documentation-only update.
  Remote GitLab CI remains unverified (last recorded pipeline had no assigned
  runner). Deferred BUG-PRJ-001 remains open; no ranking accuracy, saved-reference
  behavior, or live-provider performance acceptance is claimed.
- No requirement IDs, prompts, runtime code, dependencies, or secrets changed.
  Feature 004 specification/clarification/plan/tasks require their own review gates;
  this acceptance does not authorize its implementation.

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
| 2026-10-11 | Constitution amendment 1.0.0 → 2.0.0 for reduced scope | User, reply "a", as recorded in constitution 2.0.0 | Ratified; dependent drafts require re-review | .specify/memory/constitution.md; docs/constitution-amendment.md; dependent drafts |
| 2026-10-12 | Five-slice discovery MVP and listed exclusions | User, reply "A" to scope walkthrough | Feature boundaries approved; product decisions and individual review gates pending | docs/scope.md; specs/001–005 |
| 2026-10-12 | Required project name/question; optional keywords/year bounds; paper limit 1–250, UI default 100 | User, reply "A" to project-fields walkthrough | Field choices approved; remaining validation, specification, and implementation gates pending | specs/001-project-management/spec.md; docs/scope.md |
| 2026-10-12 | Permanent project deletion and owned-data removal after an explicit warning/confirmation; no undo; other projects and original application untouched | User, reply "A" to deletion walkthrough | Deletion behavior approved; specification and implementation gates pending | specs/001-project-management/spec.md |
| 2026-10-12 | Proposed project validation limits, normalization, duplicate names, readable errors, preserved form input, and unchanged stored data on invalid input | User, reply "A" to validation walkthrough | Validation behavior approved; specification and implementation gates pending | specs/001-project-management/spec.md |
| 2026-10-12 | Current Linux reference host; local CRUD p95 below 500 ms, 100 requests, 100 stored projects, excluding startup/external services | User, reply "A" to performance walkthrough | Host and target approved; no performance measurement executed | specs/001-project-management/spec.md; docs/verification.md |
| 2026-10-12 | Project-management specification as a whole | User, reply "approve project specification." | Specification approved; plan, contracts, tasks, and implementation not approved | specs/001-project-management/spec.md |

## Project-management clarification — 2026-10-12

- User request: "Walk me through these decisions". Used `speckit-clarify` to guide
  five sequential decisions; the user answered "A" to each. Exact questions and
  accepted answers are retained in the active specification's Clarifications section.
- Product decisions do not approve the whole specification, plan, contract, tasks,
  or implementation. No application code or dependencies were added.
- Inspected reference host using `lscpu`, `uname -srmo`, and `free -h`:
  AMD Ryzen 7 5700X3D, 8 cores/16 threads, 31 GiB reported RAM,
  Linux 7.2.9-2-cachyos x86_64. This is an environment inventory, not a benchmark.
- Re-reviewed the specification quality checklist: 5/10 → 8/10 items passing;
  newly passing items cover count/deletion approval, performance host/budget approval,
  and constitution ratification (recorded in constitution 2.0.0 on 2026-10-11).
  Specification/design/tasks approval and reviewed test mapping/acceptance evidence
  remain unchecked. Dependent planning drafts still require constitution re-review.
- No application tests executed: no implemented application or test suite exists yet.
- Documentation-only Python assertions passed: exactly five clarification answers,
  checklist 8/10, and no duplicate level-two headings in the active specification
  or verification strategy. This is not application verification.

## Project-management specification approval — 2026-10-12

- User approval (verbatim): "approve project specification."
- Marked `specs/001-project-management/spec.md` approved without changing its
  requirements. No approval is inferred for the plan, contracts, tasks, later
  features, or implementation. The combined specification/design/task checklist
  gate remains unchecked until all its parts have been reviewed and approved.
- No application tests run: this is an approval-record update, not implementation
  or verification evidence.

## Project-management plan review preparation — 2026-10-12

- User request (verbatim): "OK lets review". This authorizes review preparation,
  not approval of the plan/contract/task list or implementation.
- Used the installed `speckit-plan` workflow. Ran
  `.specify/scripts/bash/setup-plan.sh --json`: PASS; existing plan preserved.
  It resolved feature identifier `001-project-management`; the actual Git branch
  remains `main`. No branch was created. No extension hooks were configured.
- Reviewed constitution 2.0.0, approved 001 specification, scope, plan template,
  and existing design artifacts. Updated `plan.md`, `research.md`, `data-model.md`,
  `contracts/api.md`, and `quickstart.md` in `specs/001-project-management/`.
  This is repository-based design review, not external research or experimentation.
- Proposed runtime dependencies each have a stated purpose: FastAPI, SQLAlchemy,
  psycopg, and uvicorn. Tests use pytest, HTTPX, pytest-playwright/Chromium and Ruff;
  no frontend framework, provider SDK, or dependency installation was added.
- Added proposed mappings for FR-PRJ-001–008 and NFR-PRJ-001–003 and a reproducible
  real-HTTP/PostgreSQL timing protocol. None represents executed acceptance evidence.
- AUD-PLAN-001: stale constitution blockers in planning and governance documentation
  corrected from the recorded ratification. Later-slice reviews remain pending.
- AUD-PLAN-002 (FR-PRJ-007/008): propagated retained form input and the permanent
  deletion warning/no-undo decision into the API/UI contract, model, and plan.
- AUD-PLAN-003 (NFR-PRJ-003): replaced unspecified timing method with a proposed
  100-request balanced CRUD workload, 10 warm-up reads, real PostgreSQL/loopback HTTP,
  nearest-rank p95, raw samples, and required environment evidence. Plan approval
  must cover this protocol; no benchmark was run.
- Pre/post-design constitution assessment: Principles I–VII compatible at design
  level, with PostgreSQL, secrets, local deployment and testing requirements retained.
  This is not human approval or proof of runtime compliance.
- Task list updated only to correct gate status; all 21 tasks remain unchecked and
  need reconciliation/review after plan approval. Checklist remains 8/10: combined
  specification/design/task approval and test mapping/acceptance evidence pending.
- No application tests run: there is still no implemented application/test suite.
- Documentation validation: Python assertions PASS across 18 Markdown files for
  local links and duplicate section headings, all 11 project requirement mappings,
  five retained clarification answers, checklist 8/10, and 21 unchecked tasks.
  `git diff --check`: PASS (no output). `git branch --show-current`: `main`.
  These checks do not establish application correctness or performance acceptance.

## Project-management plan and API contract approval — 2026-10-12

- User approval (verbatim): "approve plan and API contract".
- Recorded approval in `specs/001-project-management/plan.md` and
  `contracts/api.md`, including the plan's supporting design and performance
  protocol. Updated current gate descriptions without changing approved requirements.
- Task reconciliation and separate task-ordering approval remain pending. All
  implementation tasks remain unchecked. The combined specification/design/task
  checklist gate remains unchecked until task approval; no implementation permission,
  later-slice approval, or acceptance is inferred from this decision.
- No application tests run: this is approval documentation only.

## Project-management task review — 2026-10-12

- User request (verbatim): "Yes review". This is task-review authorization, not
  task approval or permission to begin implementation.
- Used `speckit-tasks`; ran `.specify/scripts/bash/setup-tasks.sh --json`
  successfully. Required spec/plan and rationale/model/contract/quickstart resolved
  under `specs/001-project-management/`. No extension hooks were configured.
- Re-reviewed the task draft against approved 001 requirements, plan/API contract,
  and constitution 2.0.0. Updated `specs/001-project-management/tasks.md` from 21
  unchecked draft tasks to 26 unchecked reconciled tasks; no implemented/completed
  task IDs were changed. Requirement/acceptance IDs are unchanged.
- Breakdown: 3 setup, 3 foundational, 8 US1 create/reopen, 5 US2 edit/delete, and
  7 verification/acceptance tasks. Suggested first demo remains US1 only; complete
  feature acceptance still requires both stories and all cross-cutting evidence.
- AUD-TASK-001 (Principle VI): moved migration/database tests before storage logic
  and separated US2 browser test authoring from UI implementation. Red-phase failures
  must demonstrate missing behavior, not broken setup. Full-suite passing evidence
  is still required before declaring implementation tasks complete.
- AUD-TASK-002 (FR-PRJ-002–008): made normalization/boundaries, server-owned fields,
  permanent deletion warning/no undo, retained failed edits, and cross-project
  isolation explicit in tasks; mapped all 11 FR/NFR requirement IDs to task IDs.
- AUD-TASK-003 (NFR-PRJ-001–003): made safe disposable-DB opt-in/name/target checks,
  loopback/configuration, versioned migrations, secret/rendering/keyboard checks,
  and the approved real-HTTP/PostgreSQL performance protocol explicit.
- Optional parallel authoring pairs: T007/T008 (US1) and T015/T016 (US2), each
  after its prerequisites. No delegation was used; shared test-database execution
  remains sequential. No query/retrieval/ranking/reference schema was introduced.
- Human task approval and actual application acceptance remain pending. Checklist
  remains 8/10; no application tests, CI jobs, benchmarks, or installation ran.
- Documentation-only Python assertions: PASS for 26 sequential unchecked task IDs,
  checklist format/file paths, US1=8 and US2=5, four parallel-authoring markers,
  all 11 requirement mappings, and headings/local links across 18 Markdown files.
  `git diff --check`: PASS (no output). No configured after-tasks hooks found.
  These checks do not verify application behavior or satisfy acceptance criteria.

## Task approval and implementation entry gate — 2026-10-12

- User approval/instruction (verbatim): "approve tasks and start project management. Remember to commit and push to github regularly".
- Approved the reconciled feature 001 tasks and authorized implementation of that
  slice only. Record small milestone commits and push to the private repository
  regularly; later features and acceptance remain unapproved.
- Loaded `speckit-implement`; ran
  `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`:
  PASS, resolving the active feature and task list. No before-implementation hooks
  were configured. Git working tree contained only the 13 planning files edited
  during this conversation; no unrelated application changes were discarded.
- `gh repo view --json nameWithOwner,visibility` confirmed
  `mgustafsn/ResearchPilot-SDD`, `PRIVATE`. Actual Git branch is `main`.
- Read-only checklist gate: `requirements.md` contains 10 items, 8 checked and
  2 unchecked. The combined approval marker is now stale relative to the recorded
  approvals; actual application acceptance evidence is still absent. Do not mark
  either checklist item passed within the implementation workflow or fabricate
  test evidence. Explicit confirmation to proceed with unchecked items is required
  by the installed workflow before coding can begin.
- No application code/dependencies/tests were added or run. All 26 tasks remain
  unchecked; this is an approval-record and planning-publication milestone.
- Pre-publication documentation assertions: PASS across 18 Markdown files for
  local links/section headings and 26 unchecked tasks; limited common credential
  pattern scan found no matches. `git diff --check`: PASS (no output). These are
  documentation checks, not application tests or a comprehensive secret audit.

## Implementation milestone 1 — local PostgreSQL foundations — 2026-10-12

- User confirmed unchecked-checklist continuation (verbatim): "yes". Checklists
  remain read-only in the implementation workflow; no acceptance evidence inferred.
- Starting commit `26927cc`, branch `main`, working tree clean. Principles I–VII
  rechecked: only approved 001, no paper/LLM/provider code, mandatory tests,
  PostgreSQL, loopback, environment secrets, and original-repository isolation.
- Observed tools: uv 0.13.0, system Python 3.14.7, project interpreter selected by
  uv CPython 3.13.15, Docker 29.9.0, Compose 5.6.0, Node v26.11.1. PostgreSQL
  container reports 17.11; exact Python dependencies are pinned in the new uv.lock.
- Created isolated Compose project `researchpilot-sdd-001`, new durable volume,
  loopback port 55432, application DB `researchpilot_sdd`, and disposable DB
  `researchpilot_sdd_test`. Generated local credentials only in ignored `.env`,
  permission 0600. No original database/repository was used or modified.
- Commands: `uv sync`, `docker compose up -d --wait db`, and dedicated `createdb`
  command from README: PASS. `uv run playwright install chromium`: PASS with an
  unsupported-OS warning; Playwright downloaded its Ubuntu 24.04 fallback Chromium
  153.0.8010.12. Browser runtime execution remains to be tested in the UI increment.
- RUN-001-RED: `uv run --env-file .env pytest backend/tests/test_project_postgres.py -q`:
  6 passed, 1 failed, 11 setup errors. Missing migration behavior intentionally
  raised NotImplementedError; safety guards passed. No absent-service/import issue
  caused the failures. Migration implementation followed this recorded red phase.
- AUD-IMPL-001: pytest's initial long traceback unexpectedly included credentialed
  fixture argument values. No credentials were committed or included in application
  browser/log output. Rotated generated local DB credentials immediately, added
  redacted URL fixture representations and short pytest tracebacks. Do not retain
  the raw red-run output in committed evidence; counts/errors above are sanitized.
- Added transactional versioned SQL migration, startup serialization, actual
  PostgreSQL constraint/reconnect/rollback tests, and test-target refusal checks.
- RUN-001-GREEN: `uv run --env-file .env pytest -q`: 18 passed in 0.54s.
  `uv run ruff check backend`: PASS after fixing two import and two line-length
  findings. `bash -n scripts/start-local.sh`: PASS. No API/browser acceptance
  results claimed yet. Full application startup smoke remains part of T003/API.
- T001/T002/T004/T005/T006 implemented with the current suite passing. T003 local
  configuration exists but stays unchecked until API/startup smoke is demonstrated.
  Real-server browser fixture is authored; it will be exercised with the API/UI.
- No prompt files changed (001 uses no runtime LLM). No features beyond 001 added.

## Implementation milestone 2 — create/list/reopen — 2026-10-12

- Milestone 1 commit `0d57390` pushed successfully to private GitHub `main`.
- RUN-002-RED: `uv run --env-file .env pytest backend/tests/test_projects.py backend/tests/test_project_api.py -q --tb=no`:
  40 failed, 20 passed. Baseline schema/HTTP scaffolds lacked normalization,
  constraints, strict numeric validation, structured errors, and create/read storage.
  Tests were present and services available before implementation.
- Implemented strict Pydantic project inputs/output, deterministic keyword
  normalization, isolated SQLAlchemy project operations, sanitized error envelopes,
  list ordering, and same-origin FastAPI routes. Pydantic is already a FastAPI
  dependency; no new external integration or LLM prompt was added.
- RUN-003-RED: `uv run --env-file .env pytest backend/tests/test_project_browser.py -q --tb=no`:
  4 failed in 98.15s against an intentionally minimal page without controls.
  Actual Chromium fallback runtime launched and local PostgreSQL/API worked;
  browser failures exposed the missing UI rather than browser installation problems.
- Implemented labeled project form/list/detail, paper count 100, keyboard focus,
  readable field errors, retained failed-save input, and text-only rendering.
- Added actual application lifespan shutdown/recreation and new PostgreSQL
  connection test; persisted API project values survive with stable ID/timestamps.
- Actual `scripts/start-local.sh` smoke: migrated the new application database,
  served UI/API on `127.0.0.1:8000`, returned an empty project list, and shut down
  cleanly. No original database was used and no application project data was created.
- RUN-003-GREEN: `uv run --env-file .env pytest -q`: 83 passed in 4.62s, with one
  Starlette/httpx test-client deprecation warning. `uv run ruff check backend`:
  PASS after correcting line-length findings. `node --check frontend/app.js` and
  `git diff --check`: PASS. Warning is retained, not hidden or treated as a failure;
  no unplanned httpx2 dependency was added.
- T003 and T007–014 completed at the create/reopen checkpoint; all currently
  implemented tests pass. These are automated/browser results, not a human keyboard
  audit, ranking evidence, or full feature acceptance. No later slice implemented.

## Implementation milestone 3 — edit/delete — 2026-10-12

- Milestone 2 commit `8b74762` pushed successfully to private GitHub `main`.
- RUN-004-RED: `uv run --env-file .env pytest backend/tests/test_project_api.py backend/tests/test_project_browser.py -q --tb=no`:
  9 failed, 13 passed in 11.95s. Expected missing PUT/DELETE routes and edit/delete
  controls; existing create/reopen workflows still passed. New tests preceded logic.
- Implemented full transactional PUT and DELETE with stable identity/createdAt,
  success-only updatedAt, strict input checks, approved status/error shapes, and
  project isolation. No future-owned tables or search locks were added.
- Implemented edit form population and a keyboard-accessible native confirmation
  dialog explicitly warning of permanent deletion/no undo. Cancel sends no DELETE;
  confirmed deletion does not remove another project's records.
- Added real PostgreSQL application restart checks for successful update/deletion
  and commit-failure rollback tests for both mutations. Raw injected exception/SQL
  strings remain absent from API responses and captured application logs.
- RUN-004-GREEN: `uv run --env-file .env pytest -q`: 93 passed in 7.25s with the
  same single test-client deprecation warning. `uv run ruff check backend`,
  `node --check frontend/app.js`, and `git diff --check`: PASS after an import-order
  correction. All T015–019 tasks completed; final verification/human gates pending.
- Tests use synthetic project inputs and explicitly disposable PostgreSQL only.
  No human audit, feature acceptance, or later-slice approval is implied.

## Implementation milestone 4 — automated verification — 2026-10-12

- Milestone 3 commit `d7c0959` pushed successfully to private GitHub `main`.
- Added execution/commit fault injection for create/update/delete with successful
  retry and no partial writes; failed multi-statement migrations leave no partial
  table/version. Added canary and generated-password response/asset/log checks,
  malicious HTML text-only rendering, Escape focus return, and failed deletion UI.
  These new regressions passed existing behavior; no fake red-phase claim is made.
- AUD-IMPL-002 (FR-PRJ-007): generic field errors did not explain how to correct
  numeric input. Added a failing correction-message regression before adding safe
  field-specific messages for numeric/text/length/year/JSON errors; no raw input,
  arbitrary unknown keys, SQL, or exception context reaches the response.
- AUD-IMPL-003 (NFR-PRJ-001): test guard could allow reset without an application
  target to compare. Added a failing regression, then required a configured
  application URL and local test host in addition to the explicit opt-in/name checks.
  Combined regression command on PostgreSQL/API tests: 2 failed, 45 passed in 2.22s.
- AUD-IMPL-004 (local scope/original isolation): runtime storage accepted unrelated
  database names and nonlocal/SQLite targets. Before fixing, `pytest ... -k
  runtime_refuses -q --tb=no`: 3 failed, 23 deselected. Added safe runtime refusal
  for non-PostgreSQL, nonloopback, or non-dedicated DB names, retaining only this
  rebuild's application/test databases. No authentication/public deployment added.
- RUN-005-GREEN: `PERFORMANCE_OUTPUT=docs/evidence/project-performance.json uv run --env-file .env pytest -q -s --junitxml=docs/evidence/project-tests.xml`:
  **110 passed in 10.39s**, one known Starlette/httpx test-client deprecation warning.
  Actual JUnit output is in `docs/evidence/project-tests.xml`; raw sanitized timing
  evidence is in `docs/evidence/project-performance.json`.
- NFR-PRJ-003: **p95 2.39 ms**, below the approved 500 ms target. Actual approved
  Ryzen 7 5700X3D host, Linux 7.2.9-2-cachyos, PostgreSQL 17.11, real loopback HTTP,
  100 seeded projects, 10 untimed reads, 20 five-operation cycles, 100 retained
  successful samples, nearest-rank 95th value. Report includes versions/load,
  baseline commit `d7c0959`, dirty-tree disclosure, timestamp, and source hashes.
  This small controlled sample does not establish load scalability or scientific
  ranking accuracy. It covers only the approved project-operation budget.
- CI-parity command `uv run --env-file .env pytest -m "not performance" -q`:
  109 passed, 1 deselected in 9.44s. Ruff, JS syntax, and diff whitespace checks:
  PASS. GitHub workflow added for PostgreSQL/browser/unit/API/lint checks with
  synthetic disposable CI-only credentials; remote execution is not yet claimed.
- Evidence verification: JUnit 110 tests/0 failures/0 errors, 100 timing samples,
  all source hashes match; actual generated credential absent from all 75 current
  publishable files. This is a bounded leak check, not a comprehensive secret audit.
- Added `docs/evidence/project-traceability.md` with actual FR/NFR test mappings.
  T020–022 complete. T023 awaits workflow publication/observation; T024 human audit,
  T025 final post-audit verification, and T026 explicit acceptance remain unchecked.
- AI static audit by OpenCode/GPT-6.1 Sol: project inputs rendered through textContent,
  DB/API errors sanitized, environment configuration isolated, no provider/LLM SDK
  paths, only 001 schema plus migration bookkeeping, loopback deployment retained.
  Remaining limitation: no human reviewer keyboard/usability findings yet. Built-in
  checklist markers were not changed by implementation; no human review fabricated.

## GitHub verification and remaining human gates — 2026-10-12

- Verification commit `077b2b1` pushed successfully. GitHub Actions run
  https://github.com/mgustafsn/ResearchPilot-SDD/actions/runs/38243969348
  completed successfully for full SHA `077b2b18ade38c6369a8279a1445fd914b828cae`.
  `gh run watch 38243969348 --exit-status` returned success; test job took 1m12s.
- Remote logs confirm CPython 3.12.15, Ruff PASS, JavaScript syntax PASS, and
  **109 passed, 1 deselected, 1 warning in 11.69s**. Real PostgreSQL 17 and Chromium
  browser tests ran; approved-host performance was deliberately deselected.
  JUnit evidence was uploaded as `project-test-results` by the workflow.
- CI annotations retained: Node 20-based action versions are forced onto Node 24
  by GitHub; ubuntu-latest has a scheduled Ubuntu 26 migration. Neither prevented
  this run. They are future maintenance considerations, not erased failures.
- T023 complete. **23/26 tasks completed**; T024 human keyboard/usability review,
  T025 final post-audit verification, and T026 explicit acceptance remain pending.
  The AI/static/browser audit cannot impersonate a human reviewer. Feature 002
  planning/implementation is still blocked by feature 001 acceptance.
- To review locally, run `./scripts/start-local.sh` and open
  `http://127.0.0.1:8000`; test creating/reopening/editing, validation, keyboard
  navigation, cancelled deletion, confirmed deletion, and persistence on restart.
  Existing ignored local configuration and dedicated PostgreSQL are ready on this
  machine. The original repository/database remain untouched.
- Final documentation assertions: PASS (23 completed/3 pending tasks, checklist
  unchanged at 8/10, local links/headings valid, measured source hashes still match).
  `git diff --check`: PASS. No configured after-implementation hooks found.

## User project-management review finding — 2026-10-12

- User feedback (verbatim): "I'vet tried all that you can do, publication years allow for characters other than numbers then default to \"Any - Any\" if letters were put in. This should be fixed in future MVPs".
- Human reviewer: user; self-reported review of available functionality. Exact
  browser/version, typing sequence, and individual keyboard/audit scenarios were
  not supplied, so no more detailed manual test evidence is inferred.
- Recorded BUG-PRJ-001 (FR-PRJ-004/007, AC-PRJ-004) in `docs/known-issues.md`:
  invalid publication-year entry may silently become unbounded. User explicitly
  deferred the fix; no application code or approved requirements were changed.
- Inspected current number controls and empty-value-to-null conversion. This is
  a possible mechanism, not an independently reproduced/confirmed root cause.
  The earlier 110-test result remains historical evidence, not verification of
  this newly reported case. No new application tests were executed.
- Explicit feature acceptance with this known limitation still needs confirmation;
  the reported defect is not marked fixed/compliant and feature 002 is not started.

## Feature 001 acceptance with limitation; feature 002 review entry — 2026-10-12

- User reply (verbatim): "Yesw", interpreted as yes to the immediately preceding
  explicit question accepting project management with the known publication-year
  issue so feature 002 can be reviewed. No claim that BUG-PRJ-001 is fixed, that
  every requirement passes, or that missing detailed human audit evidence exists.
- Feature 001 accepted with BUG-PRJ-001 deferred. T024 detailed human-audit evidence
  and T025 final post-audit verification remain outstanding. User self-reported
  trying available functionality; exact browser/keyboard cases remain unspecified.
- Feature 002 specification review may begin; approval of its spec/plan/tasks or
  implementation is not inferred. No application code, schemas, prompts, secrets,
  or dependencies changed as part of this transition.
- Machine-local `.specify/feature.json` now points to `specs/002-search-queries`;
  it remains ignored by Git. No branch was created; the working branch is `main`.
- Re-read constitution 2.0.0 and feature 002 draft. Next review focuses on editable
  query suggestions and preservation of user-controlled text/enabled state; no
  scholarly retrieval/ranking/reference implementation is authorized here.
- Re-ran `uv run --env-file .env pytest -q`: 110 passed, one known test-client
  warning in 10.41s. This does not cover or resolve the newly reported browser-year
  issue. `git diff --check`: PASS. Feature path prerequisite check resolved 002.
- T026 records user acceptance with the known limitation; 24/26 tasks checked,
  T024/T025 still outstanding. Neither their audit evidence nor full compliance
  is fabricated by this acceptance. Feature 002 clarification begins separately.

## Feature 002 clarification decisions — 2026-10-12

- User chose "A" for suggestion regeneration: replace only untouched AI queries;
  preserve manual queries and generated queries edited or enabled/disabled by the
  user, including their stored text and enabled state. Recorded the exact question
  and accepted answer in `specs/002-search-queries/spec.md`.
- Applied the decision to FR-QRY-004 and AC-QRY-003. User ownership remains tracked
  after a subsequent restoration of the original text/state; regeneration cannot
  silently reclaim user-controlled queries. This is a product-decision approval,
  not approval of the whole specification, plan, tasks, or implementation.
- No application code, runtime prompts, or dependencies changed; no application
  test outcome is claimed by this documentation update.
- User chose "A" for duplicate suggestions: validate a 3–6 unique normalized batch
  first, then skip collisions with preserved queries; allow zero new additions and
  a combined list larger than six. Updated FR-QRY-001/002 and AC-QRY-001 without
  changing the approved protection of user-owned text or enabled state.
- User chose "A" for query-list size: at most 20 saved queries per project,
  counting enabled and disabled entries together. Manual additions over the limit
  fail without writes; regeneration fills free slots without removing user-owned
  queries. Added FR-QRY-008, SC-QRY-004, and explicit capacity edge cases; batch
  order determines which suggestions fit. Whole-spec/plan/task approval is pending.
- User chose "a" for changed research context: retain all queries/enabled states,
  show a refresh notice, and make no automatic provider call or query deletion.
  Added FR-QRY-009/SC-QRY-005. The notice is durable until successful generation
  for the current question/keywords; failed/stale generation cannot clear it.
- User chose "A" for deleted suggestions: delete the stored entry without a
  text-suppression history; permit the same text in a later explicit generation.
  Disabling preserves the user-owned entry/state; pending generation is rejected
  if deletion changes the revision. Added FR-QRY-010/SC-QRY-006.
- Clarification loop complete: five questions asked/answered. Updated sections:
  Clarifications, User Scenarios & Testing, Edge Cases, Functional Requirements,
  Key Entities, and Success Criteria. No feature 002 checklist exists to toggle;
  no before/after clarification hooks are configured.
- AUD-QRY-SPEC-001: draft success criteria implied that 002 needed implemented
  scholarly searches. Clarified AC-QRY-005/SC-QRY-001/003 so 002 verifies stored-query
  selection with fixtures and actual search/provider-spy acceptance belongs to 003.
  This scope-consistency correction remains part of the draft awaiting review.
- Coverage: scope, domain/state, interaction and edge cases resolved; interface
  boundaries, terminology, completion signals and placeholders clear at spec level.
  Exact provider/model configuration, timeout/request limits, error contracts,
  safe concurrency persistence and measurable performance protocol are deferred to
  plan review, not silently approved by these five product decisions.
- Documentation assertions PASS: five recorded clarification answers, ten query
  functional requirements, 46 globally unique requirement IDs, valid local links
  and no duplicate section headings. `git diff --check`: PASS. No feature 002
  implementation, application tests, dependency installation, or live AI calls ran.

## Feature 002 specification approval — 2026-10-12

- User approval (verbatim): "approve query specification".
- Marked `specs/002-search-queries/spec.md` approved, including the five recorded
  clarification decisions, FR-QRY-001–010, and the clarified distinction between
  stored-query selection in 002 and scholarly search integration in 003.
- Updated README/scope gate status without changing approved requirements. Query
  generation failure preserves the existing list and manual entry; this is approved
  behavior, not proof of implementation or approval for live AI calls.
- Plan, provider/model configuration, timeout/request budgets, contracts, task
  ordering, and implementation still require their separate review gates. Feature
  001's publication-year issue remains open/deferred; no audit evidence was invented.
- No application code, prompts, schemas, dependencies, or tests changed. No new
  application test outcome is claimed for this approval-record update.

## Feature 002 plan preparation — 2026-10-12

- User request (verbatim): "Lets start that" after the proposed implementation-plan
  review. This authorizes drafting/review, not plan approval or feature 002 coding.
- Loaded `speckit-plan`; `.specify/scripts/bash/setup-plan.sh --json` succeeded and
  resolved 002 paths. The copied generic template was replaced with the feature
  design. Actual branch remains `main`; feature identifier is `002-search-queries`.
  No extension hooks were configured.
- Reviewed constitution 2.0.0, approved spec, scope, existing database/service/API,
  dependencies, CI, known issue and verification artifacts. No original repository
  or credential file was read as source material.
- The planning skill explicitly asks for research agents; delegated two independent
  read-only research tasks, with no implementation/dependency/secret access:
  `general` session `ses_ecfeb1312ffe7fPfbPMir0n5mN` checked official OpenAI model,
  structured-output/endpoint/privacy documentation; `explore` session
  `ses_ecfeadc7affeWbn2qfcqQzVzwT` inspected current persistence/integration risks.
  Child model versions were not separately pinned/reported. Their findings are
  research/design recommendations, not runtime tests or human approval.
- Created draft `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`,
  `contracts/provider.md`, and `quickstart.md` under `specs/002-search-queries/`.
  No `tasks.md` or application implementation was generated in this phase.
- Proposed pinned `gpt-4.1-mini-2025-04-14`, strict JSON Chat Completions over
  existing HTTPX (promoted to runtime only after implementation approval), one
  call/no retries, 512 completion tokens, actual async 20 s deadline, phase limits,
  64 KiB body bound, and two upstream connections. Model/budgets are unapproved
  proposals; no SDK/new package family or live API calls were introduced.
- PROMPT-QRY-001: candidate `query_suggestions_v1` prompt is recorded verbatim in
  the provider contract as a proposal, not a created runtime prompt or executed
  LLM call. Context is user-role JSON data, not privileged instructions; output
  permits query text only, never authoritative paper/citation metadata.
- Privacy disclosure: proposed `store:false` does not mean zero retention. Official
  docs describe default abuse-monitoring retention up to 30 days with exceptions;
  external generation sends stored question/keywords only on explicit action.
  Manual management requires no API key; live smoke testing needs separate consent.
- AUD-QRY-PLAN-001 (FR-QRY-007/008/009): proposed parent-first locks and one combined
  revision, separate context/generation counters, and bounded slots/key uniqueness.
  No external call under a DB transaction, no lease/job/history schema. First
  committed concurrent generation wins; newer edits/delete prevent stale overwrite.
- AUD-QRY-PLAN-002: existing migration-count assertions, projects-only truncation,
  project update/delete, and frontend delayed-response behavior need reviewed
  integration changes. Preserve existing project JSON shapes/timestamps/PUT rules,
  explicit test-target safeguards, and unchanged deferred year conversion.
- AUD-QRY-PLAN-003: corrected stale verification-strategy claims that no 001 tests
  or benchmark had run. Added an explicitly unapproved 002 query-CRUD timing
  protocol; no query benchmark or quality evaluation was run.
- Mapped all FR-QRY-001–010 to proposed fake-provider/mock-HTTP/unit/API/PostgreSQL/
  browser evidence. Scholarly search/provider-spy acceptance remains in 003, not 002.
- Pre/post-design Constitution Check: Principles I–VII compatible at design level;
  environment-only secrets, local PostgreSQL, source/prompt/test evidence and review
  gates retained. Not human approval, full 001 compliance, or application acceptance.
- No code, dependencies, migration, runtime prompt, CI configuration, or live API
  request changed. Plan/contract approval and separate tasks review remain pending.
- Documentation validation PASS: six 002 planning artifacts, ten requirement/test
  mappings, 26 Markdown files checked for local links/headings and limited common
  credential patterns; no unresolved template markers or prematurely generated
  tasks. `git diff --check`: PASS. No application tests ran for this documentation
  phase. No configured after-plan hooks found.

## Feature 002 plan and contract approval — 2026-10-12

- User approval (verbatim): "approve query plan and contracts".
- Recorded approval of `specs/002-search-queries/plan.md`, API/provider contracts,
  supporting design/validation guide, and the 002 verification protocol. Approved
  choices include pinned GPT-4.1 Mini, structured JSON, one call/no retries,
  512-token cap, 20 s total deadline, parent revision/lock design, and local query
  CRUD p95 below 500 ms under the documented reference-host protocol.
- Task generation/review/approval and implementation remain separate gates. No
  paid/live smoke call is authorized by this decision. No runtime code, migration,
  prompt file, dependency, or test was added or changed; no test result is claimed.
- BUG-PRJ-001 remains deferred and uncorrected. Feature 001's missing detailed
  audit evidence is not supplied by this approval; feature 003 remains unapproved.

## Feature 002 task preparation resumed — 2026-10-13

- User request (verbatim): "Ok lets continue"; after an interrupted response,
  user requested continuation and then "resume". This authorizes task drafting/
  review, not task approval, application implementation, or paid/live AI calls.
- Loaded `speckit-tasks` and read its template plus approved specification, plan,
  API/provider contracts, model, rationale, quickstart, constitution and scope.
  The setup script completed before the interruption; interrupted patch created
  no file. On resume, Git was clean on `main` before the new task draft was written.
- Generated `specs/002-search-queries/tasks.md`: 36 sequential unchecked tasks,
  comprising setup 3, foundations 5, US2 manual control 8, US1 suggestions 11, and
  verification/audits/acceptance 9. Both stories are P1; manual control comes first
  per the approved plan, so the initial demo needs no API key.
- AUD-QRY-TASK-001: explicit tests-before-logic sequence, deliberate contract
  scaffolds rather than import/setup failures as red evidence, exact model/budget/
  prompt constraints, revision/context/ownership/slot rules and legacy compatibility
  are included. Generic optional-test wording remains overridden by Principle VI.
- AUD-QRY-TASK-002: include real-PostgreSQL/barrier and browser delayed-response
  schedules, safe multi-table fixture rollout, entire batch validation, zero-add
  context acknowledgment, no-op ownership/revisions, and ordinary manual use
  without configuration. The deferred year-input bug is explicitly out of this
  implementation task list; no full 001 audit evidence is invented.
- All FR-QRY-001–010 have task mappings; task IDs are local to feature 002, and
  original US1/US2/requirement IDs are unchanged. Independent authoring pairs are
  T009/T010 and T017/T018 after their listed prerequisites; no delegation was used
  and destructive test execution remains sequential by default.
- Tasks include regular tested commit/push milestones and separate human audit/
  acceptance. No app code, migration, runtime prompt, dependency, test, or CI file
  was changed during drafting; no application/quality/performance result is claimed.
- Explicit task/implementation approval is still required. No scholarly provider,
  search route, ranking/reference work, history/lease, SDK, or live smoke is added.
- Documentation validation PASS: 36 sequential unchecked tasks with checklist
  format/file paths, US2=8/US1=11, four independent-authoring markers, all ten query
  requirement mappings, and 27 Markdown local-link/heading/limited credential-pattern
  checks. `git diff --check`: PASS. No configured after-tasks hooks found. These
  checks are not application verification, and no application tests ran.

## Feature 002 implementation authorization — 2026-10-13

- User approval (verbatim): "approve query tasks and start implementation".
- Approved all 36 reviewed tasks and implementation of feature 002 only. Start
  with manual controls, then structured suggestions. Continue regular verified
  commits/pushes. No live/paid provider smoke call or BUG-PRJ-001 fix authorized.
- Baseline commit `6d11deb`, actual branch `main`, clean worktree. Implementation
  prerequisite check resolved feature 002/tasks. No 002 checklist files or extension
  hooks exist; no unchecked checklist confirmation is required for this feature.
  Existing 001 audit/checklist limitations remain recorded, not overwritten.
- Existing ignore rules cover credentials, Python/browser/build artifacts and
  Docker context. Checked dedicated Compose service: not running at entry; startup
  is limited to this rebuild's named service/volume, never the original database.
- Promoted already-present HTTPX to runtime and added deliberate missing-behavior
  contract scaffolds. Config example contains no secret values; ignored user
  configuration is not overwritten. No live HTTP/model call is introduced.

## Feature 002 milestone 1 — manual query controls — 2026-10-13

- Restarted only the dedicated Compose PostgreSQL service successfully; preserved
  its volume and user configuration. `uv sync` promoted existing HTTPX with no new
  package family. Baseline full suite: 110 passed in 10.85s, one known test-client
  deprecation warning. No application/production data cleanup was performed.
- QRY-RED-001: `uv run --env-file .env pytest backend/tests/test_queries.py -q --tb=no`:
  36 failed, 2 passed; missing constraints/normalization/notice/selection behavior
  in intentional importable scaffolds. Added ownership/merge tests before those
  helpers: 3 failed, 38 passed. Then implemented strict common models, immutable
  context, metadata validation, batch/merge/selection rules and provider protocol.
- QRY-RED-002: PostgreSQL query-schema tests: 8 failed before migration/reflection/
  revision changes. Added migration 002, shared reflection, parent locks and
  effective/context revision hooks. Preserved existing project JSON/timestamps/PUT
  rules; tests now expect the reviewed two migration versions and real pre-failure
  rollback counts. Explicit multi-table fixture cleanup retains all safeguards.
- QRY-RED-003: manual API tests: 7 failed before query routes/service implementation.
  Added real same-revision concurrency/failed-commit tests: 2 failed, 8 passed
  before manual query logic. Implemented transactional CRUD, uniqueness/capacity/
  revision checks, typed sanitized errors, sticky ownership and exact stored selection.
- QRY-RED-004: real Chromium/injected-provider browser tests: 3 failed in 10.61s
  against the page without query controls. Implemented labeled manual controls,
  ownership/state display, retained invalid drafts, text rendering, and context
  notices. View/revision guards prevent obsolete callbacks clearing newer drafts.
- Added actual application close/recreate PostgreSQL persistence, restored generated
  ownership, no-op behavior and enabled-only service-selection regressions. Provider
  fakes/barrier helpers exist only in tests; no production fake setting or live
  adapter call is implemented. Runtime adapter and prompt creation remain pending.
- QRY-GREEN-001: `uv run --env-file .env pytest -q`: **180 passed in 15.50s**, one
  known Starlette/httpx test-client warning. Existing project/browser/performance
  regressions are included. `uv run ruff check backend`, `node --check frontend/app.js`,
  and `git diff --check`: PASS after fixing import/line-length findings.
- T001–016 completed for the manual-control milestone; T017–036 pending. Full
  feature 002 acceptance, live-model quality, external latency, query-specific
  performance protocol, and human audit are not claimed. BUG-PRJ-001 is unchanged.
- No runtime LLM prompt has changed or executed yet. Ordinary manual query actions
  never call an AI/scholarly provider. Secrets remain in ignored environment state.
- Bounded pre-publication checks: 16 completed/20 pending tasks, generated database
  credential absent from publishable files, original publication-year conversion
  unchanged. This is not a comprehensive secret audit or a reproduction/fix of
  the deferred browser issue.
- Application migration smoke applied 002 to this rebuild's application database
  and verified every original field of its one existing project unchanged; no
  application records were deleted or shown. First bare `uv run` Python import
  failed before DB access because backend is not installed as a package; retried
  successfully with `PYTHONPATH=backend`, as the launcher already configures.

## Query manual-control milestone publication — 2026-10-13

- Implementation milestone `5fd0a3f` pushed successfully to private GitHub `main`.
- GitHub Actions run https://github.com/mgustafsn/ResearchPilot-SDD/actions/runs/38373581252
  completed successfully for `5fd0a3f1bcb8ff65b67a822acf8a2bc89eba48c6`.
  Remote logs: **179 passed, 1 deselected, 1 warning in 21.68s**; Ruff and JS
  checks passed. CI intentionally excludes reference-host performance acceptance.
- Full local suite remains 180 passing, including the existing project performance
  regression. Query-specific performance, real-model evaluation, generation/UI
  integration, final audits and human acceptance are still pending (T017–036).
- To review the manual increment, restart `./scripts/start-local.sh`, open the
  existing project's details at `http://127.0.0.1:8000`, and use Search queries.
  Migration retains existing project values; no key is needed. Adding a key does
  not activate the unimplemented generator and no paid call has been made.
- No after-implementation hooks are configured. This is a verified incremental
  checkpoint, not completion of feature 002 or authorization for feature 003.

## Prompt iteration record template

| ID/date | Feature/requirement | Exact prompt and context artifact versions | Model/tool version | Expected output | Actual output/evidence | Failure | Revised prompt | Outcome |
|---|---|---|---|---|---|---|---|---|

## Feature 002 static audit — 2026-10-19

- Reviewer: OpenCode, model `openai/gpt-6-luna`; static repository review, not an
  independent human/security certification. Scope: Principles I–VII and T032.
- Scholarly metadata: 002 exposes query text only. No paper/citation fields or
  scholarly provider were added. Source scan of `backend/researchpilot` found no
  OpenAI/OpenAlex imports outside `integrations`; a Python AST scan reported
  `vendor imports outside integrations: []`. The API module imports the adapter only
  at the composition boundary; query service/domain depend on the provider protocol.
- Structured output/provider boundary: inspected `openai_queries.py`; fixed endpoint,
  pinned allowed model, strict JSON schema, whole-batch validation, 512-token cap,
  one request, no redirects/proxy environment, TLS verification, 20-second deadline,
  64 KiB incremental response cap. Provider tests cover malformed/refused/truncated
  output, timeouts, cancellation, no retries and canary redaction.
- Secrets/logging/privacy: API key is read from environment and held by the adapter;
  it is not returned to browser responses or emitted in adapter/service logs. Logged
  suggestion metadata is typed model/prompt/status/duration/token/count data only.
  Explicit generation sends stored question/keywords; no call is made on load/edit.
  `store:false` is not described as zero retention; disclosure remains in UI/docs.
- Rendering and concurrency: query data is assigned through DOM `textContent`,
  `createTextNode`, and `replaceChildren`; no `innerHTML` use was found in
  `frontend/app.js`. Parent-first locks, expected revisions, unlocked provider await,
  stale merge rejection and transaction rollback have PostgreSQL/API/browser tests.
- Test safety/schema/scope: fixture reset is guarded to the loopback, named, explicitly
  disposable `researchpilot_sdd_test` database, distinct from application DB; it
  truncates only the known `search_queries` and `projects` tables. Only migration 002
  was added for query schema; migration 001 is unchanged. Browser-server fixtures
  strip `OPENAI_API_KEY`. No production fake switch, hidden retry, unauthorized search/
  paper/ranking/reference schema or BUG-PRJ-001 fix found.
- Findings: no blocking implementation finding from this bounded static review.
  Existing Starlette/HTTPX test-client deprecation warning remains. Remote GitLab
  pipeline is unverified due VPN requirement. Manual keyboard/usability review,
  independent human audit, and explicit user acceptance remain outstanding. This
  review does not claim zero retention, live model quality, or complete feature 001
  compliance. No prompt changes or live provider calls were made.

## Feature 002 post-audit verification — 2026-10-19

- AUD-QRY-FINAL-001: added a browser schedule for editing a saved query while fake
  generation is pending. The first full run exposed a test-scheduling race: the fake
  provider was released before the asynchronous edit had committed, allowing a valid
  generation completion to win. The test now waits until the edited state is visible
  before releasing the provider, then asserts the late suggestion result is rejected.
  This matches the approved ordering; no product logic change was needed.
- A first assertion assumed one exact stale-error wording; the browser/server can
  legitimately surface either sanitized revision-conflict wording depending on which
  guard responds first. Assertion now checks the shared `changed` meaning. After adding
  a wait for the edit commit, final browser test passed and final full suite passed.
- Final full local suite after audit/test changes:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -q --tb=short`:
  **281 passed, 1 warning in 25.42s**. Warning: existing Starlette/HTTPX test-client
  deprecation. Failed intermediate run after audit: **280 passed, 1 failed** due to the
  above test scheduling race; corrected and rerun successfully.
- Project performance separately:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest
  backend/tests/test_project_performance.py -m performance -q --tb=short`:
  **1 passed, 1 warning in 1.13s**.
- Query performance separately:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache PERFORMANCE_OUTPUT=docs/evidence/query-performance.json
  uv run --env-file .env pytest backend/tests/test_query_performance.py -m performance
  -q --tb=short`: **1 passed, 1 warning in 1.24s**; 100/100 requests succeeded,
  p95 **3.746 ms** (<500 ms). Updated raw evidence includes final source hashes and
  dirty-tree disclosure.
- Final checks: `uv run ruff check backend`, `uv run ruff format --check
  backend/tests/test_query_browser.py backend/tests/test_query_performance.py`,
  `node --check frontend/app.js`, and `git diff --check`: PASS. Automated quickstart
  journeys are covered by the complete test suite; no manual human walkthrough or
  remote GitLab pipeline was performed.
- T034 complete. T033 human usability review and T036 explicit user acceptance remain
  pending; feature 003 remains unauthorized. No live OpenAI request was made.
- FR-QRY-001–010 automated mapping and remaining limitations are in
  `docs/evidence/query-traceability.md`; README and `docs/verification.md` link the
  current verified status and query performance artifact.

## Feature 002 human review and acceptance — 2026-10-19

- Reviewer: user; browser/version not provided. After being asked to review query
  add/edit/enable/disable/delete, keyboard/focus behavior, validation retention,
  context refresh notice, ownership labels, and suggestion privacy disclosure, the
  user reported (verbatim): **“All works. Lets proceed.”** This is recorded as the
  requested human usability review and explicit acceptance of feature 002. No
  individual accessibility claim beyond the user's reported review is inferred.
- The user affirmed the privacy disclosure and stated they do not want the app
  connected to OpenAI now. No live calls were made. A non-secret configuration check
  found `OPENAI_API_KEY` absent and `OPENAI_QUERY_MODEL` absent from local `.env`;
  suggestion generation is therefore unavailable in this local run while manual
  query management remains usable. The integration remains explicit-action/optional
  per the approved feature; no permanent removal was requested.
- Feature 002 accepted. Remote GitLab CI remains unverified because VPN access is
  required. BUG-PRJ-001 remains deferred and unfixed. Features 003–005 remain separate
  approval gates; this acceptance does not approve their specs/plans/tasks or code.

## Feature 002 publication attempt — 2026-10-19

- Created local commits `9ded61b` (verification/performance) and `4443779`
  (acceptance record) on `main`. User indicated VPN access should be available.
- `git push origin main` still failed before authentication with
  `could not read Username for 'https://gitlab.abo.fi': No such device or address`.
  No credentials were requested or disclosed. The commits remain local and remote
  GitLab CI remains unverified.
- User subsequently clarified VPN is currently down; no further push attempt is made
  until the user says it is available.

## Feature 003 clarification — 2026-10-19

- User accepted feature 002 (“All works. Lets proceed.”); the active local Spec Kit
  feature was switched to `specs/003-paper-retrieval/spec.md`. The prerequisite
  script resolved feature 003 paths. No implementation plan or tasks were created.
- Clarification workflow asked five questions, one at a time; the user selected the
  recommended A option each time. Recorded in the draft spec and `docs/scope.md`:
  (1) explicit Search may send enabled query text/applied filters to OpenAlex (not
  OpenAI), with disclosure; (2) any failed enabled-query request fails the whole
  attempt and preserves previous results; (3) search each saved query as-is, without
  appending question/keywords; apply inclusive year filters and enforce the paper limit
  through allocations, with question and
  keywords retained in the attempt snapshot; (4) a fully successful empty search
  replaces current search results, while saved references remain unchanged; (5)
  supplied publication-year bounds are inclusive.
- These clarify product behavior but do not approve the whole specification, plan,
  contracts, tasks, implementation, external live smoke, or any future features.
  Remaining timeout/lease/provider budgets and performance protocol belong in plan
  review. No OpenAlex/OpenAI calls or application changes occurred.
- `.specify/feature.json` now points locally to feature 003; actual Git branch is
  still `main`. The file remains machine-local/ignored.

## Feature 003 specification approval — 2026-10-19

- User approval (verbatim): “Yes its approved.” Recorded approval of the clarified
  `specs/003-paper-retrieval/spec.md`, including the five clarification decisions.
- Plan/design, contracts, tasks, and implementation were not approved by the spec
  approval. Planning may begin; implementation remains gated on its own reviewed
  plan/contracts/tasks and explicit authorization. No OpenAlex or OpenAI call was
  made. User clarified VPN is currently down; no GitLab push is attempted.

## Feature 003 plan and design preparation — 2026-10-19

- User approved the clarified 003 specification and requested continuation. Ran
  `.specify/scripts/bash/setup-plan.sh --json`; it copied the plan template to
  `specs/003-paper-retrieval/plan.md`, resolving feature 003 while the actual Git
  branch remains `main`. No feature branch was created. No extension hooks file is
  present. No tasks or implementation were generated.
- Re-read constitution 2.0.0, approved 003 spec, approved 001/002 implementation
  patterns, PostgreSQL migration model, local dependencies, scope and verification
  requirements. No code or dependency changes were made.
- Directly reviewed OpenAlex official documentation on 2026-10-19 (no research
  delegation and no API requests): Works Search, Works Filters, Work Object, API
  Rate Limits/Authentication and API response envelope. Findings include `search`
  fields/default provider relevance ordering, inclusive publication-date filters,
  maximum `per_page` 100, no-key basic access/rate limits, current key/usage changes,
  `meta.cost_usd`, and abstract inverted-index/authorship/location/OA field shapes.
  Source links and design decisions are in `specs/003-paper-retrieval/research.md`.
- Drafted plan, research, provider/API contracts, data model and quickstart under
  `specs/003-paper-retrieval/`. All are proposals pending review; plan proposes no
  OpenAlex key/paid account, at most 20 requests per search, no automatic retries,
  2 concurrent requests, 10/120-second request/attempt deadlines, 150-second lease,
  2 MiB response cap, and local mock-provider p95 <2 seconds over the proposed
  reference-host protocol. These budgets have not been approved or measured.
- The plan Constitution Check finds no proposed deviation from Principles I–VII at
  design level. No live OpenAlex/OpenAI calls, benchmark, migration, task list, CI
  change, or implementation occurred. Plan/contracts/tasks/implementation approval
  remain separate gates.

## Feature 003 implementation plan approval — 2026-10-19

- User approval (verbatim): “I approve the plan. Lets go”. Recorded approval of
  `specs/003-paper-retrieval/plan.md`, including the proposed budgets/verification
  approach as written. At this point the API/provider contracts still awaited separate
  review; they were approved in the following entry. Task generation and implementation
  had not begun. No live OpenAlex/OpenAI call was made. VPN is down; no push attempted.

## Feature 003 API/provider contract approval — 2026-10-19

- User approved both draft contracts (reply: “Approve both (Recommended)”) for
  `specs/003-paper-retrieval/contracts/api.md` and
  `specs/003-paper-retrieval/contracts/provider.md`. Task generation is authorized;
  generated tasks and implementation still require separate review/approval.
- No live provider call was made. OpenAI remains unconfigured per user preference;
  OpenAlex usage is restricted to explicit user-triggered searches in the future.

## Feature 003 task draft — 2026-10-19

- User separately approved the implementation plan and API/provider contracts.
  `.specify/scripts/bash/setup-tasks.sh --json` resolved `specs/003-paper-retrieval/`
  and the available research/data-model/contracts/quickstart artifacts. No extension
  hooks file is present. Task generation did not authorize implementation.
- Created `specs/003-paper-retrieval/tasks.md` with 33 sequential unchecked tasks:
  setup 3, foundation 5, US1 retrieval 8, US2 safe recovery 8, cross-cutting/polish 9.
  MVP candidate is US1 successful retrieval using fakes; full acceptance requires US2
  failure/ownership behavior as well. Independent test authorship opportunities are
  marked [P]; no agents or delegated work were used.
- Requirement-to-task mapping covers FR-RET-001–010. Tasks sequence tests before
  logic and preserve disposable-DB safeguards, no-live-provider testing, no OpenAI
  requests, no API key/paid plan, and excluded ranking/references/PDF work. All task
  IDs are unchecked pending user task review/approval.
- Format validation: **33/33** lines have checkbox, sequential ID, valid optional
  labels, description and file path. `git diff --check`: PASS. No application code,
  tests, migrations, CI, API requests or dependencies changed.

## Feature 003 implementation authorization — 2026-10-19

- User approval (verbatim): “yes i reviewed go ahead”. Recorded approval of all
  33 tasks in `specs/003-paper-retrieval/tasks.md` and authorization to implement
  feature 003 only. No future ranking/references work or live provider smoke call is
  authorized. OpenAI remains unconfigured; automated tests must not call OpenAlex.
- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  resolved feature 003 and its approved task list. No feature-003 checklist directory
  exists. Extension hook file is absent. Actual Git branch remains `main`.

## Feature 003 setup baseline — 2026-10-19

- Baseline commit `c5f2274`, actual branch `main`; active ignored Spec Kit feature is
  `specs/003-paper-retrieval`. PostgreSQL 17 Compose service is healthy on the
  rebuild's loopback test port. Environment: uv 0.13.1, project Python 3.13.15,
  HTTPX 0.28.1. `pyproject.toml` and `uv.lock` already include HTTPX at runtime; no
  new dependency or credential was added. In the project environment, no
  `OPENAI_API_KEY`, `OPENAI_QUERY_MODEL`, or `OPENALEX_API_KEY` is configured.
- Baseline command `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file
  .env pytest -m 'not performance' -q --tb=short`: **279 passed, 2 deselected, 1
  existing Starlette/HTTPX deprecation warning in 24.16s**. Performance tests were
  deliberately deselected for baseline.
- A preliminary system-Python 3.14 metadata probe could not find project HTTPX; reran
  in the locked uv project environment successfully (0.28.1). No application test
  failure or source change resulted.
- T001–T003 complete. No provider calls, code, schema, or dependencies changed.

## Feature 003 foundational implementation — 2026-10-19

- T004/T005 red tests were authored before behavior/schema: domain suite
  `backend/tests/test_papers.py` **18 failed** on unimplemented domain behavior;
  PostgreSQL/schema suite `backend/tests/test_retrieval_postgres.py` **4 failed** on
  absent migration/reflection/schema. Failures were test assertions/setup at the
  feature behavior boundary, not live-service errors. A system-Python diagnostic
  earlier lacked the project HTTPX install; test runs use the locked uv environment.
- Implemented normalized `Paper`, strict provider model validation, inclusive year
  filters, exact query-budget allocation, DOI/title normalization, abstract-index
  reconstruction, safe URL checks and deterministic DOI/provider/title dedup in
  `backend/researchpilot/paper_domain.py`; added vendor-free `PaperProvider` protocol
  and result/error contracts in `paper_provider.py`.
- Added additive migration `003_paper_retrieval.sql` for `papers`, `project_papers`
  and `search_runs`, status/count/identity/ownership constraints, one-pending-run
  partial unique index and project-scoped result/run keys. Extended reflection in
  `persistence.py`; migrations 001/002 were not edited. Updated only the explicitly
  configured disposable-test cleanup and injection scaffolding; subprocess tests
  strip OpenAI/OpenAlex keys.
- Green results: `backend/tests/test_papers.py`: **25 passed**; focused migration and
  existing project PostgreSQL tests:
  `uv run --env-file .env pytest backend/tests/test_retrieval_postgres.py
  backend/tests/test_project_postgres.py -q --tb=short`: **30 passed**, 1 existing
  Starlette/HTTPX deprecation warning. All DB work used the guarded disposable DB.
- T001–T008 complete. No live OpenAlex/OpenAI calls, dependencies, ranking/reference
  schema, or application-database migration were introduced.

## Feature 003 US1 red-phase tests — 2026-10-19

- Added the OpenAlex `MockTransport` suite before adapter logic:
  `uv run --env-file .env pytest backend/tests/test_openalex_provider.py -q --tb=no`:
  **15 failed** against importable `NotImplementedError` scaffolds. Tests cover exact
  request/data flow, mapping, bounds, malformed responses, status failures and logs.
- Added fake-provider route tests before service/API logic:
  `uv run --env-file .env pytest backend/tests/test_retrieval_api.py
  backend/tests/test_retrieval_postgres.py -q --tb=no`: **6 failed, 4 passed**. All
  failures were missing success-path routes/persistence; foundational schema tests
  passed.
- Added Chromium workflow tests before UI logic:
  `uv run --env-file .env pytest backend/tests/test_retrieval_browser.py -q --tb=no`:
  **2 failed** because Search/results controls are absent. No test called a live
  provider. Failures are recorded red-phase evidence, not regressions in earlier slices.

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

## GitLab repository migration — 2026-10-14

- User supplied the new private repository URL:
  `https://gitlab.abo.fi/marcgust/ResearchPilot-SDD`.
- Changed local `origin` fetch/push URL to the corresponding `.git` URL. Added
  `.gitlab-ci.yml` with loopback PostgreSQL, repeatable non-performance tests,
  Ruff, JavaScript syntax, and JUnit artifacts. Updated forward-looking 002
  plan/task references (T031) and README; retained historical GitHub run evidence.
- No application prompt or business logic changed. Requirement mapping: the
  existing T031 CI work and constitution VI test evidence.
- `git diff --check`: PASS. `uv run ruff check backend`: PASS.
  `node --check frontend/app.js`: PASS.
- Initial `uv run pytest -m 'not performance' -q` lacked the guarded test
  database settings: 109 passed, 70 setup errors, 1 deselected. Retried with
  `.env`; the isolated PostgreSQL container was stopped, so that run had
  connection errors. After `docker compose up -d --wait`,
  `uv run --env-file .env pytest -m 'not performance' -q --tb=short`:
  **179 passed, 1 deselected, 1 warning in 13.88s**. The warning is a
  Starlette/HTTPX test-client deprecation notice.
- `git ls-remote origin HEAD` reached GitLab but could not authenticate to
  the private repository (`could not read Username`). GitLab CI has not run
  remotely, and no push or remote pipeline result is claimed.
- User clarified that pushing requires their VPN; push is deferred to the user.
  The migration is committed locally only. The legacy
  `.github/workflows/ci.yml` is retained unchanged pending a decision to remove it.

## Query generation milestone (T017–T027) — 2026-10-14

- Scope: feature 002 US1 only. No live OpenAI call, no real API key used, no
  scholarly provider/search route, no BUG-PRJ-001 change. Base commit `92804b6`.
- Environment: Python 3.13.15 (uv venv), HTTPX 0.28.1, FastAPI 0.143.0,
  Pydantic 2.14.1, Node v26.11.1, local loopback PostgreSQL via `docker compose`.
- Red phase (T017–T019, before T020–T022):
  `uv run --env-file .env pytest backend/tests/test_query_provider.py
  backend/tests/test_query_api.py backend/tests/test_query_postgres.py -q`:
  **88 failed, 20 passed**. Causes were missing behavior only: adapter takes no
  arguments / no `from_environment` (54), generate route 405 (31), no
  `QueryService.generate` (2), plus barrier waits. Browser red phase (T023):
  **7 failed, 3 passed** (no Generate control).
- Prompt (T020): `backend/researchpilot/prompts/query_suggestions_v1.txt`,
  version `query_suggestions_v1`, SHA-256
  `0cc54399eb157d45cb5a6f76b82ffad8007d1c5f02fbcc68e6efa0b526de571e`. Text is the
  approved contract prompt verbatim (contract line breaks retained). Mock-request
  evidence: `test_FR_QRY_001_exact_request_shape_and_prompt` asserts the exact
  endpoint, bearer header, model `gpt-4.1-mini-2025-04-14`, `store:false`,
  `stream:false`, `n:1`, `max_completion_tokens:512`, strict schema, two messages
  (system prompt file, user JSON `{researchQuestion, keywords}`) and no tools.
- Adapter limits verified by tests: 20 s total async deadline over headers and
  body (slow-body test times out while per-chunk progress continues), 3/2/5/15 s
  phase timeouts, 2 connections, no redirects, `trust_env=False`, TLS verify,
  64 KiB incremental body cap (stops reading; exact-limit body accepted, +1 byte
  rejected), single attempt for HTTP/transport errors, cancellation propagation,
  sanitized errors with suppressed exception context, canary key/context absent
  from all captured logs.
- Service/API (T021/T022): snapshot transaction released before the provider
  await; re-lock, stale check, merge, context acknowledgment and revision bump in
  one transaction; batch re-validated in the service; provider exceptions mapped
  to 503/504/502 fixed messages; missing parent 404 with no resurrection. Logs:
  project UUID, status, duration, model/prompt version, token counts, merge counts.
  Production composition reads `OPENAI_API_KEY`/`OPENAI_QUERY_MODEL`; missing key or
  unreviewed model disables generation only. The adapter client closes at shutdown.
  The subprocess browser fixture strips `OPENAI_API_KEY` from its environment.
- Audit-test change: `test_NFR_PRJ_001_credentials_absent_from_assets_api_and_logs`
  matched the substring `import openai`, which falsely flagged the composition
  import `from researchpilot.integrations import openai_queries`. Replaced with an
  AST check that is stricter: recursive over `backend/researchpilot`, rejects any
  `openai`/`openalex` module import, and rejects `researchpilot.integrations`
  imports from business modules. Verified by injecting such an import into
  `query_service.py`: the audit failed; the probe was removed.
- Test-harness fix: Playwright leaves an event loop on the main thread, so async
  tests run via `conftest.run_async` (fresh thread). Before that fix the full suite
  had 52 `asyncio.run() cannot be called from a running event loop` failures.
- Mutation checks (temporarily applied, then reverted): disabling the stale-revision
  check → 6 PostgreSQL failures; deleting owned rows during merge → 3 failures;
  removing the browser view guard → navigation test failed.
- UI (T024): explicit "Generate suggestions" button, OpenAI disclosure, disabled
  with readable text when unconfigured, per-project pending state (duplicate
  clicks blocked; manual work, navigation and deletion stay available), merge-count
  status, text-only rendering, epoch/revision-bound responses, saved-state reload on
  error without clearing unsaved input.
- Quickstart (T027): journeys 1–10 are covered by automated tests with fake and
  disabled providers, including restart into a manual-only profile and deleted-query
  reappearance. No manual browser walkthrough or human review was performed.
- Final runs: `git diff --check` PASS; `uv run ruff check backend` PASS;
  `node --check frontend/app.js` PASS;
  `uv run --env-file .env pytest -m 'not performance' -q`:
  **277 passed, 1 deselected, 1 warning** (Starlette/HTTPX test-client
  deprecation notice). Per file: provider 56, query API 29, query PostgreSQL 26,
  query browser 10, query domain 47. `pytest -m performance`: 1 passed (existing
  project budget; not query performance, T030 pending).
- Requirement mapping: FR-QRY-001 (provider/API/browser generation tests),
  FR-QRY-002 (batch/Unicode validation), FR-QRY-004 (preservation/restoration),
  FR-QRY-005 (failure categories, unchanged state, manual still works),
  FR-QRY-007 (stale/concurrency schedules), FR-QRY-008 (zero-slot/capacity),
  FR-QRY-009 (atomic notice acknowledgment), FR-QRY-010 (deletion/no resurrection).
- Not claimed: live model quality, cost, latency, or zero retention. Fake-provider
  results are not live evidence. Committed locally only; push deferred to the user
  (VPN required). T028–T036 (fault/security expansion, browser safety, query
  performance, CI run, audits, human review, acceptance) remain pending.

## Local verification continuation — 2026-10-19

- Current base checkout is the existing `5dd81a4` query-generation milestone.
  Added `backend/tests/test_query_performance.py` to implement the approved
  PostgreSQL/loopback protocol, but could not execute it because Docker is
  unavailable here; this test is unverified and remains a draft. Environment:
  Python 3.13.15, pytest from the project `.venv`, Linux
  `7.2.9-2-cachyos x86_64`, AMD Ryzen 7 5700X3D, 31 GiB RAM. No live provider
  credentials were used.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest
  backend/tests/test_query_provider.py backend/tests/test_queries.py -q --tb=short`:
  **103 passed, 1 warning in 0.41s**. The warning is the existing
  Starlette/httpx test-client deprecation notice.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -m
  'not performance' -q --tb=short`: **165 passed, 1 failed, 111 errors, 1
  deselected in 20.18s**. The environment denied access to Docker's Unix socket;
  PostgreSQL could not be started or reached. Database-backed project, query,
  browser, and migration fixtures consequently errored at setup. The lone failure
  was the PostgreSQL migration test failing on the same unavailable connection.
  This is an infrastructure failure, not evidence of an application regression;
  PostgreSQL and browser acceptance remain unverified in this run.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run ruff check backend`:
  PASS. `node --check frontend/app.js`: PASS.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run ruff format --check backend`:
  FAIL because 17 existing backend files do not match the current formatter; the
  new performance test itself passes `ruff format --check`. Existing files were
  not reformatted as part of this task.
- Docker access check `docker compose ps` was denied by the sandbox. The full
  repeatable suite, query performance protocol, PostgreSQL migration/concurrency
  checks, and CI result still require an environment with the configured disposable
  PostgreSQL service. No task is marked complete on the basis of this partial run.

### Continuation check — 2026-10-19

- Re-ran the provider/domain subset:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest
  backend/tests/test_query_provider.py backend/tests/test_queries.py -q --tb=short`:
  **103 passed, 1 warning in 0.41s** (existing Starlette/HTTPX test-client warning).
- Attempted API/provider/domain checks including `backend/tests/test_query_api.py`.
  Provider/domain tests passed; all 29 API tests errored during fixture setup because
  PostgreSQL at `127.0.0.1:55432` refused the connection. This does not verify API
  behavior. No application tests were changed and no task status was advanced.
- `uv run ruff check backend`, `node --check frontend/app.js`, and `git diff --check`:
  PASS. The working tree still contains the pre-existing uncommitted query benchmark
  test and evidence draft; neither was rewritten or marked verified.

### PostgreSQL-backed verification and query performance — 2026-10-19

- Started only this rebuild's dedicated Compose `db` service with
  `docker compose up -d --wait db`: PASS; service reported healthy. No application
  or original-repository database was targeted.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -m
  'not performance' -q --tb=short`: **277 passed, 2 deselected, 1 warning in
  22.23s**. The warning is the existing Starlette/HTTPX test-client deprecation.
- Existing project performance regression, separately:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest
  backend/tests/test_project_performance.py -m performance -q --tb=short`:
  **1 passed, 1 warning in 1.19s**.
- Query CRUD performance protocol:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache PERFORMANCE_OUTPUT=docs/evidence/query-performance.json
  uv run --env-file .env pytest backend/tests/test_query_performance.py -m performance
  -q --tb=short`: **1 passed, 1 warning in 1.23s**. On the approved Ryzen 7 5700X3D /
  Linux 7.2.9-2-cachyos reference host with PostgreSQL 17.11, all 100 loopback HTTP
  requests succeeded across 100 projects/1,999 queries. Nearest-rank p95 was **3.78 ms**,
  below the approved 500 ms budget. Raw samples, statuses, versions, load, commit,
  dirty-tree state and source hashes are retained in `docs/evidence/query-performance.json`.
- Full suite, including both performance tests:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -q --tb=short`:
  **281 passed, 1 warning in 25.33s** (existing Starlette/HTTPX test-client warning).
- Added browser regressions for inert hostile query text/keyboard focus and editing
  a saved query during an in-flight generation. The latter exposed two valid stale
  error messages depending on whether the browser revision guard or server conflict
  arrived first; the assertion now checks their common sanitized meaning. A full
  run before this assertion correction had **280 passed, 1 failed**; after correction
  the full suite passed. Browser suite: **12 passed**.
- T030 is now complete. `ruff check backend`, `node --check frontend/app.js`, and
  `git diff --check`: PASS. This does not complete remaining audits, remote CI,
  human review, final acceptance or feature 002 as a whole. No live model calls ran.

## Feature 003 security and data-flow audit — 2026-10-19

- Reviewer: OpenCode/GPT-6 Luna, static source/config/test audit after implementation
  increments; not an independent human security certification. AST scan found no
  OpenAI/OpenAlex vendor imports outside `integrations`; API imports adapters only
  at the composition root. Frontend `innerHTML` occurrence count is zero; result
  metadata is built with text nodes and links pass `http`/`https`+credential checks.
- AUD-RET-001: the initial mocked HTTP test captured HTTPX's INFO access log, which
  included the full search URL and therefore the user query. Changed the adapter to
  suppress HTTPX/HTTPCore access-level logs and emit only typed request/status/count/
  duration/cost metadata. `test_FR_RET_007_only_safe_typed_metadata_is_logged` now
  passes; application code never logs the raw query or body.
- Only additive `migrations/003_paper_retrieval.sql` was added; migrations 001/002
  remain unchanged. Test cleanup explicitly truncates only feature tables plus the
  existing project/query tables in the guarded disposable database. No ranking,
  reference schema, full-text download, OpenAI call/key, live OpenAlex call, or new
  dependency was introduced. CI explicitly unsets all provider key/model variables.
- Project and query writes lock the project first and reject active search leases;
  provider calls occur outside DB transactions; stale workers cannot commit; failures
  leave current associations unchanged. No blocking finding remains from this static
  review. Human usability review and user acceptance remain pending.

## Feature 003 final local verification — 2026-10-19

- Full suite after implementation/audit:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -q --tb=short`:
  **358 passed, 1 existing Starlette/HTTPX deprecation warning in 44.72s**. This
  includes existing 001/002 regressions and all feature-003 fake-provider/PostgreSQL/
  Chromium tests; no OpenAlex or OpenAI call occurred.
- Final retrieval benchmark after code freeze:
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache PERFORMANCE_OUTPUT=docs/evidence/retrieval-performance.json
  uv run --env-file .env pytest backend/tests/test_retrieval_performance.py -m performance
  -q --tb=short`: **1 passed, 1 warning in 6.09s**, 20/20 complete searches and 250
  fixture papers/attempt. Nearest-rank p95 **207.47 ms** (<2,000 ms). Raw samples,
  statuses, versions, host/load, commit/dirty state and source hashes are retained in
  `docs/evidence/retrieval-performance.json`.
- Final quality checks: `uv run ruff check backend`, `uv run ruff format --check` on
  the ten new feature-003 Python/test files, `node --check frontend/app.js`, and
  `git diff --check`: PASS. Existing shared legacy files were not mass-reformatted.
- Browser test authoring initially used an exact label not present in the project form
  and an incorrect link locator; corrected test selectors to the actual accessible
  labels. Application behavior was unchanged; final browser/full suites pass.
- Feature 003 T001–T032 complete. T033 requires the user's hands-on keyboard/usability
  review and explicit acceptance. Remote GitLab CI remains unverified while VPN is
  down. No live OpenAlex smoke or OpenAI call was made.
- Restarted the user's local app with `./scripts/start-local.sh` detached after
  implementation. It applied migrations 001–003 and Uvicorn reported startup complete;
  `curl http://127.0.0.1:8000/` returned HTTP 200. A read-only local DB check reported
  schema versions 001/002/003 and one project row (no project contents were read).
  The first version-check command omitted `PYTHONPATH=backend` and failed before DB
  access; rerun with the launcher-equivalent `PYTHONPATH` succeeded. `.env` still has
  no OpenAI key/model or OpenAlex key; no external call was made.

## GitLab push retry — 2026-10-19

- User indicated VPN should be up; retried `git push origin main` once. It still failed
  before authentication with `could not read Username for 'https://gitlab.abo.fi': No
  such device or address`. No credentials were requested or disclosed. All verified
  feature-003 commits remain local; remote GitLab CI remains unverified. No retry or
  alternate authentication method was attempted.

## GitLab publication and CI status — 2026-10-19

- The user reported `glab` should be configured. `glab auth status --hostname
  gitlab.abo.fi` confirmed authenticated without displaying credential contents; Git's
  repository-local credential helper was absent. Configured only this repository's
  helper as `!glab auth git-credential` (not global), then `git push origin main`
  succeeded: remote advanced from `5fd0a3f` through `9f8e5cb` (including accepted 002,
  003 spec/plan/contracts/tasks and implementation checkpoints). No token was printed.
- GitLab pipeline **6874** for `9f8e5cb05fb0ad37cfa2c047a81fb115f1e40a62` was created.
  `glab ci status --wait` ran for 120s but pipeline remained pending. `glab ci get
  --pipeline-id 6874 --output json` reports status `pending`, job `test` not started,
  runner id `0`, inactive, with no runner assigned. CI result is therefore unverified;
  no retry or runner setup was attempted.

## Feature 005 implementation and automated verification — 2026-10-22

- Feature 005 spec, plan/supporting design and tasks were reviewed and approved by
  the user before runtime implementation. The implementation added only the saved
  reference slice: migration 005, normalized snapshot domain/service, scoped API,
  and save/list/remove browser controls. It adds no dependency or provider/LLM
  metadata path and does not edit earlier migrations.
- `migrations/005_saved_references.sql` stores provider-owned Paper fields as a JSONB
  snapshot, checks provider/source identity and required title/source fields, and
  cascades only from its owning project. It has no FK to replaceable search results.
  Save locks the project row first, resolves a paper from current project results,
  checks/expires leases through existing search ownership code, and uses a unique
  provider identity plus `ON CONFLICT DO NOTHING` for idempotency. List and delete
  are project-scoped and do not require an inactive search.
- API accepts only `paperId` on save, returns sanitized reference errors, and strips
  ranking state by constructing responses from the strict normalized `Paper` model.
  First save returns 201; an idempotent repeat returns 200 with the stored snapshot.
  Browser content uses `textContent` and links pass the existing HTTP(S),
  credential-free URL validator. No `innerHTML`, manual citation fields, or LLM call
  was added to this flow.
- Test-first evidence: initial new reference suite had 16 expected implementation
  failures; after implementation, focused domain/PostgreSQL/API tests passed **20/20**.
  Browser regression passed **1/1** with Chromium. The full command
  `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run --env-file .env pytest -x -q --tb=short`
  completed with **447 passed, 1 skipped in 58.31s** on Python 3.13.15 using the
  guarded disposable PostgreSQL database and Chromium. One earlier full-suite run
  caught the existing project test's expected migration list missing version 005;
  the assertion was corrected, then the full suite passed. A separate full run had
  a transient PostgreSQL DDL lock conflict; it did not recur after isolation.
- `UV_CACHE_DIR=/tmp/researchpilot-sdd-uv-cache uv run ruff check .`: PASS.
  `uv run ruff format --check` over the 12 changed Python files: PASS.
  `node --check frontend/app.js`: PASS. `git diff --check`: PASS. Secret-pattern
  scan of backend/frontend/migrations found no token-shaped credential literals.
  No live OpenAlex/OpenAI calls were used.
- Coverage includes concurrent duplicate saves, migration repeat/reopen, project
  deletion cascade, result deletion/provider refresh independence, active-search save
  rejection with list/remove available, stale lease expiry, cross-project isolation,
  and inert hostile text/safe links. Gaps: no separately injected migration rollback
  failure; failed-search preservation is supported by independent snapshot storage
  rather than an explicit failure-after-save test; no multi-item browser sort journey.
  Sorting itself has a Unicode case-fold domain test. These are documented limits.
- Static audit found project-first row locks in saved-reference reads/writes, no
  scholarly metadata source besides normalized provider Papers, no ranking metadata
  in saved output, project-scoped reference IDs, and project cascade. No automated
  implementation blocker remains. Human keyboard/usability review and explicit
  feature acceptance are pending; automated results do not claim user acceptance.
- Local review startup: `./scripts/start-local.sh` applied repository migrations but
  could not bind port 8000 because another app already held it. Left that app
  untouched and started this checkout on `http://127.0.0.1:8001/`; homepage and
  OpenAPI returned HTTP 200 and OpenAPI includes the three reference routes. The
  local review server remains running for the user's keyboard/usability review.
- Human review and acceptance: on 2026-10-22 the user confirmed satisfaction,
  approved Feature 005, and authorized pushing it to GitHub. No requested UI fixes
  or limitations were reported. This completes the Feature 005 human acceptance
  gate; implementation/test coverage limitations above remain part of the evidence.
