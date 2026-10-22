# Local ranking traceability — 2026-10-21

Feature 004 is implemented under the approved spec/plan/contracts/tasks. Full local
suite: **426 passed, 1 skipped**; the skipped opt-in model benchmark separately
passed. No live OpenAlex/OpenAI request in implementation/tests. Public package/model
setup downloads are separate from application data processing.

| Requirement | Actual tests/evidence |
|---|---|
| FR-RNK-001 | `test_ranking.py::test_FR_RNK_001_exact_inputs`, `test_ranking_api.py::test_FR_RNK_001_004_006_ranked_search_and_restart`, adapter exact consumed-token test |
| FR-RNK-002 | Pure vector/batch failure parametrizations, malformed-vector preservation API test, adapter dimension/token validation; real 384-dimensional inference benchmark |
| FR-RNK-003 | Pure calibration boundaries -1/0/.25/.425/.6/1, clipping, zero/large/tiny norm tests; no relevance-accuracy inference |
| FR-RNK-004 | Pure title/source tie test, API explicit `[1,0,0]` ordering and GET persistence |
| FR-RNK-005 | Browser similarity/disclosure/failure journey and 0%/truncation/refresh journey; API retains all low-score papers |
| FR-RNK-006 | Migration upgrade/repeat/reopen/constraint/rollback tests, legacy null API test, hash/model/run provenance and restart tests |
| FR-RNK-007 | Six typed model/worker failure categories preserve scores, malformed output, real-DB final-insert rollback, no-lock/expiry/replacement barrier, cancellation and overall deadline tests; child timeout/crash/busy/cancel cleanup |
| FR-RNK-008 | Loader flags/no-token setup mocks, integration boundary audit, no-context-text logging API test; real inference completed with child socket/DNS calls denied |
| FR-RNK-009 | Pinned revision/file/module/manifest corruption/missing/symlink/extra file tests, partial setup preservation/idempotence, CPU/token limit tests; explicit setup installed verified files; offline model benchmark |

AC-RNK-001: formula/order fixtures and API; AC-RNK-002: exact title-only pure/API
inputs; AC-RNK-003: retained 0% and browser disclosures; AC-RNK-004: injected
embedding/storage/stale/cancellation failure preservation. SC-RNK-001/002 have
automated evidence; **SC-RNK-003 human-labeled usefulness evaluation is pending**.

## Limits

- Formula provisional/unvalidated for this model. Scores are calibrated similarity,
  not correctness probability or scientific quality. English focus and long-input
  truncation remain product limitations, not bugs to silently mask with an LLM.
- Model benchmark uses synthetic text for timing, never scholarly metadata/quality
  labels. Raw samples/hashes/versions/RSS at `ranking-performance.json`; current
  kernel changed from the original reference environment, so formal unchanged-host
  performance acceptance is not claimed.
- Static/AI audit is not independent human security certification. Offline controls
  cover this app's known ML libraries and Python socket/DNS access, not a hostile
  native binary controlling the user's machine. No model pickle/remote Python used.
- Remote CI was not rerun/verified. BUG-PRJ-001 remains deferred. Feature 005 not
  implemented. Human keyboard/usability review and explicit 004 acceptance pending.
