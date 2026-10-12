# Verification quickstart — planned, not runnable yet

There is currently no application, pyproject, launcher, database, or test suite here.
These are intended acceptance steps after implementation, not successful-run evidence.
Re-reviewed on 2026-10-12. Commands below are proposed interfaces for the approved
implementation tasks, not commands executed during plan review.

## Prerequisites and local startup

- Linux, Python 3.12+, uv, Docker with Compose, and Node for syntax checks.
- After implementation, configure the environment from the credential-free
  `.env.example`: `DATABASE_URL` points only to this rebuild's PostgreSQL database.
  Keep actual local credentials in ignored environment configuration. No OpenAI or
  OpenAlex configuration is needed for slice 001.
- Configure a distinct `TEST_DATABASE_URL` with database name
  `researchpilot_sdd_test`, plus `ALLOW_TEST_DATABASE_RESET=1` only in the disposable
  test environment. Test fixtures must refuse other names, missing opt-in, or a
  target equal to `DATABASE_URL`. Never use the original database.

Planned commands from the repository root:

```bash
uv sync
uv run playwright install chromium
docker compose up -d db
./scripts/start-local.sh
```

The launcher reads local environment configuration without printing credentials,
applies versioned migrations, and serves `http://127.0.0.1:8000`. Do not bind the
application or database to all network interfaces. Document the implemented launcher
behavior and versions before treating this guide as runnable.

## Acceptance journey

1. Verify the empty state and labeled keyboard-accessible create action (AC-PRJ-001).
2. Create a project with name/question, optional filters and count 100; verify it
   appears in the list, and reopen it with identical values (AC-PRJ-002).
3. Submit blank/overlong names, reversed years, invalid counts, and duplicate
   keywords; verify readable errors or approved normalization without losing form
   input or changing saved data (AC-PRJ-004, FR-PRJ-002–005/007).
4. Edit and reopen; verify stable ID and updated values (AC-PRJ-005).
5. Stop and restart the application, recreating PostgreSQL connections without
   deleting its volume; reopen the project and verify persisted values (AC-PRJ-003).
6. Create another project. Cancel deletion and verify no change; confirm the
   permanent-deletion warning and verify only the selected project disappears,
   including after restart (AC-PRJ-006). Unknown IDs return not-found (AC-PRJ-007).

## Automated checks and evidence

Once the implemented, safeguarded disposable test environment is configured:

```bash
uv run pytest backend/tests
uv run ruff check backend
node --check frontend/app.js
```

The full suite must include actual PostgreSQL migration/reconnect/rollback tests,
browser journeys, injected storage failures, and the approved-host performance
fixture. Browser tests use their own local server and disposable PostgreSQL data.
Timing protocol and host inventory are in `../../docs/verification.md`; route and
data details are in `contracts/api.md` and `data-model.md`.

Run a human keyboard audit and inspect browser assets, responses, rendering and logs
for secret leakage. Record commands, software/host versions, expected/actual outcomes,
raw latency samples, failures, and fixes in `../../docs/evidence-log.md`. Passing
documentation checks is not application acceptance. CI runs repeatable tests/lint;
latency results from other hardware do not satisfy the approved reference-host gate.

Use a dedicated test database and fixture safeguards. Never reuse the original
ResearchPilot database. Before running migrations or cleanup, verify the target database.
