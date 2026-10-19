# ResearchPilot-SDD

A specification-driven rebuild of a deliberately smaller ResearchPilot MVP.
Feature 001 project creation/listing/reopening/editing/deletion is implemented.
Feature 002 manual query controls are implemented: add/edit/delete, enable/disable,
20-query limits, and durable context-change notices. Explicit AI suggestion generation
is implemented and tested only with fakes/mock HTTP; no live OpenAI call has been made.
Feature 002 is accepted; the user does not want OpenAI connected now. Latest local verification:
281 tests passed; query CRUD measured 3.75 ms p95 against the approved 500 ms
reference-host budget. See [query traceability](docs/evidence/query-traceability.md)
and [query performance evidence](docs/evidence/query-performance.json). Remote
GitLab CI has not yet run because VPN access is required.
The user accepted feature 001 with a known limitation. Detailed human-audit evidence
and final post-audit verification remain outstanding; full compliance is not claimed.
User review identified a [publication-year input issue](docs/known-issues.md),
deferred to a future iteration. Existing green tests do not cover that reported case.

## Local development

Requires uv, Python 3.12+, Docker Compose, and Node for JavaScript syntax checks.
Install with `uv sync` and `uv run playwright install chromium`.
Copy `.env.example` to ignored `.env`, set local PostgreSQL credentials and URLs,
and run `docker compose up -d --wait db`. URL-encode credentials in the URLs.
The application URL should name `researchpilot_sdd`, not the original database.
Runtime configuration rejects nonlocal hosts, non-PostgreSQL URLs, and unrelated
database names; this is not an authentication system or a public deployment.

For tests, create the separate disposable database:

```bash
docker compose exec -T db sh -c 'exec createdb -U "$POSTGRES_USER" researchpilot_sdd_test'
uv run --env-file .env pytest -q
uv run ruff check backend
```

Set `TEST_DATABASE_URL` to that database and `ALLOW_TEST_DATABASE_RESET=1` only in
your test configuration. Fixtures refuse other names and application targets.
Tests truncate **only the explicitly configured disposable database**. Keep local
credentials out of commits, browser responses, and logs. The startup script will
serve `http://127.0.0.1:8000`: run `./scripts/start-local.sh`.

Open a project's details to manage its saved queries. Manual controls require no
API key. With `OPENAI_API_KEY` set, "Generate suggestions" sends only the saved
question/keywords to OpenAI on explicit action, using the pinned model in `.env.example`.
Without a key (or with an unreviewed model), Generate is disabled and manual work continues.
`store:false` is not zero retention; provider abuse-monitoring retention may apply.
Live smoke calls need separate permission and are never part of default tests/CI.

The full suite includes the approved reference-host performance test. On other
hardware or in CI, run `uv run --env-file .env pytest -m "not performance" -q` and
do not claim reference-host performance acceptance. CI runs these repeatable tests,
PostgreSQL integration/browser checks, Ruff, and JavaScript syntax checks.
Actual test/performance evidence is under `docs/evidence/`; the evidence log
distinguishes automated results from remaining human review gates.

## Scope

Create projects → review editable AI query suggestions → retrieve real OpenAlex
papers → deduplicate and rank by embedding similarity → save project references.
Clustering, Scopus, explanations, manual categories, reference notes, reading status,
citation numbering, authentication, exports, and PDF ingestion are excluded.

## Review before implementation

1. The [constitution amendment](docs/constitution-amendment.md) is ratified as 2.0.0;
   [scope boundaries](docs/scope.md) and feature 001's specification are approved.
     Feature 002's query specification and feature 003's clarified retrieval
     specification are approved; feature 003's plan/contracts remain drafts, and
     features 004–005 remain drafts.
2. Feature 001's [plan](specs/001-project-management/plan.md) and
   [API contract](specs/001-project-management/contracts/api.md) are approved.
   Its tasks are approved and feature 001 implementation is authorized; the
    user confirmed proceeding with unchecked checklist items and subsequently
    accepted it with BUG-PRJ-001 deferred. Feature 002's specification is approved;
    its [plan](specs/002-search-queries/plan.md),
    [API contract](specs/002-search-queries/contracts/api.md), and
    [provider contract](specs/002-search-queries/contracts/provider.md).
    Plan/API/provider contracts are approved; the [task list](specs/002-search-queries/tasks.md)
     is approved for implementation. Manual control and fake-tested generation are
     implemented and feature 002 is accepted. No live OpenAI call was made; user
     prefers no OpenAI connection. Remote GitLab CI remains unverified. No live
     OpenAlex smoke call is authorized by feature 003's specification approval.
3. Review later specifications in order after their prerequisites:
   - [001 Projects](specs/001-project-management/spec.md)
   - [002 Queries](specs/002-search-queries/spec.md)
   - [003 Retrieval](specs/003-paper-retrieval/spec.md)
   - [004 Ranking](specs/004-relevance-ranking/spec.md)
   - [005 References](specs/005-saved-references/spec.md)
4. Implement and verify one approved feature at a time. Generate plans for later features
   only after their prerequisites and decisions are reviewed.

Initial artifacts were derived by an AI coding agent from the original repository
without invoking Spec Kit commands. Feature 001 subsequently underwent the installed
`speckit-clarify` workflow and a `speckit-plan` review/update on 2026-10-12. Drafts
do not constitute human approval or verification; see the evidence log for actual work.

The active feature is recorded in `.specify/feature.json`. The initialized integration
uses Claude skills such as `/speckit-clarify`, `/speckit-plan`, and `/speckit-tasks`.
No branch, commit, dependency installation, or application implementation was created
as part of the initial specification preparation. The artifacts are now tracked in a
private GitLab repository at `gitlab.abo.fi/marcgust/ResearchPilot-SDD`;
implementation remains subject to the review gates above. GitLab CI is configured
in `.gitlab-ci.yml`; remote execution has not yet been verified.

## Course evidence

See [baseline sources](docs/baseline.md), [verification strategy](docs/verification.md),
and [evidence log](docs/evidence-log.md). Do not report proposed tests as executed,
or inferred prompts as historical evidence.
