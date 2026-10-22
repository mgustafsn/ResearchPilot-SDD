# Feature 005 verification quickstart

**Status**: Draft for implementation planning; commands are proposed and have not
been run for Feature 005.

## Local startup

Use the existing `.env`, local PostgreSQL service, and startup script:

```bash
docker compose up -d --wait db
./scripts/start-local.sh
```

Open `http://127.0.0.1:8000/`, select a project with current search results, save a
paper, save it again, replace search results, and confirm the saved snapshot is
unchanged. Restart the app and reopen the project. Remove the saved item and verify
the search result remains. No external call is needed for this UI journey after
provider-derived results already exist.

## Automated verification (after implementation authorization)

Proposed focused suite:

```bash
uv run --env-file .env pytest backend/tests/test_references.py backend/tests/test_references_api.py backend/tests/test_references_postgres.py backend/tests/test_references_browser.py -q
```

Then run the complete application suite, Ruff, JS syntax, migration/restart/
concurrency tests, and `git diff --check`. Tests must use fakes/stubs for external
providers and the guarded disposable PostgreSQL database. Never run reset/cleanup
against `researchpilot_sdd` or the original repository database.

## Manual acceptance

1. Save one current result and save it again; exactly one entry is listed.
2. Search again and restart the app; the original provider snapshot is unchanged.
3. Remove it; the current search result still appears.
4. Attempt cross-project save/list/remove; no other project's data is disclosed or
   mutated.
5. Start a search and attempt a save; the save is rejected while the search is
   active. Verify list and removal remain available.

This protocol is not evidence until performed and recorded. No Feature 005 code,
migration, or task list is authorized by this quickstart.
