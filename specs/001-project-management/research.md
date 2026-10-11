# Design rationale — draft

This is repository-based analysis, not external research or executed experimentation.
Source provenance is in `../../docs/baseline.md`.

| Topic | Proposed decision | Rationale / alternative |
|---|---|---|
| Stack | Keep Python/FastAPI/PostgreSQL/vanilla JS | Focus comparison on workflow, not rewriting in a new framework |
| Validation | Retain name/question/keyword/year rules | Existing domain model provides concrete testable boundaries |
| Paper cap | 1–250, required, UI default 100 | Smaller course workload; differs from baseline nullable 1–1000 |
| Storage | PostgreSQL plus lightweight SQLite tests | SQLite-only tests cannot establish PostgreSQL migration/concurrency correctness |
| Frontend | Same-origin and no bundler | Minimal setup for a small application |
| Domain structure | Small modules with explicit boundaries | Avoid premature general-purpose architecture |

Open decisions before implementation: constitution amendment, paper-limit change,
performance host/budget, and team ownership. Later plans must decide query model,
embedding model, timeout/lease values, API request budgets, and exact text normalization.
No runtime model configuration is required for project CRUD.
