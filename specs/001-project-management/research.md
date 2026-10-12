# Design rationale — approved for slice 001

This is repository-based analysis, not external research or executed experimentation.
Source provenance is in `../../docs/baseline.md`.
Re-reviewed on 2026-10-12 against constitution 2.0.0 and the approved 001 spec.
The implementation choices below were approved with the plan on 2026-10-12;
no dependencies were installed.

| Topic | Proposed decision | Rationale / alternative |
|---|---|---|
| Stack | Keep Python/FastAPI/PostgreSQL/vanilla JS | Focus comparison on workflow, not rewriting in a new framework |
| Validation | Retain name/question/keyword/year rules | Existing domain model provides concrete testable boundaries |
| Paper cap | 1–250, required, UI default 100 | Smaller course workload; differs from baseline nullable 1–1000 |
| Storage | PostgreSQL plus lightweight SQLite tests | SQLite-only tests cannot establish PostgreSQL migration/concurrency correctness |
| Frontend | Same-origin and no bundler | Minimal setup for a small application |
| Domain structure | Small modules with explicit boundaries | Avoid premature general-purpose architecture |
| Local database | PostgreSQL 17, Compose, durable volume | Reproducible local setup without touching the original database; existing host DB is an alternative but less isolated |
| Migrations | Ordered SQL files with applied-version tracking | Fits the small schema; automatic table creation alone lacks migration evidence, while a migration framework is unnecessary now |
| Browser testing | pytest-playwright with Chromium, real local server and disposable PostgreSQL | Exercise actual UI/storage together; API-only tests cannot prove keyboard interaction or preserved form input |
| Performance | 100-request balanced CRUD mix over loopback HTTP and real PostgreSQL; nearest-rank p95 | Measures the approved local request budget; an in-process or SQLite-only timing is not acceptance evidence |
| Deletion | UI warning/confirmation, transactional API deletion, no undo | Approved behavior; soft-delete/archive would add unapproved lifecycle complexity |

The constitution amendment, project fields/validation/deletion, paper-limit change,
and performance host/budget are approved. No unresolved technical question blocks
this 001 design. The plan/API contract/tasks are approved and implemented;
human audit and acceptance remain pending.
Team ownership remains a course-evidence item, not an invented implementation decision.
Later plans must decide query/embedding models, timeout/lease values, provider request
budgets, and paper/query normalization. No runtime AI model is needed for project CRUD.
