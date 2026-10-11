# Verification quickstart — planned, not runnable yet

There is currently no application, pyproject, launcher, database, or test suite here.
These are intended acceptance steps after implementation, not successful-run evidence.

1. Install reviewed dependencies with uv and browser runtime with Playwright.
2. Start the local application/database using the implemented launcher; open loopback URL.
3. Verify empty state, create a project, reopen, edit, cancel deletion, then confirm deletion.
4. Restart/reconnect and verify retained projects persist.
5. Run unit/API/browser tests and a separately configured disposable PostgreSQL suite.
6. Run Ruff and `node --check frontend/app.js` once those files exist.
7. Run performance fixture on the agreed host; audit keyboard controls and secret leakage.
8. Save actual commands, versions, expected/actual outcomes, logs and defects in the evidence log.

Use a dedicated test database and fixture safeguards. Never reuse the original
ResearchPilot database. Before running migrations or cleanup, verify the target database.
