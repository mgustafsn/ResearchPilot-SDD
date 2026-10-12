# Verification and validation strategy — proposed

## Requirement traceability

| Requirement group | Planned evidence |
|---|---|
| FR-PRJ-001/006/008 | API, browser and PostgreSQL CRUD/restart/deletion tests |
| FR-PRJ-002–005/007 | Boundary normalization, strict input validation and rollback tests |
| NFR-PRJ-001–003 | Secret audit, keyboard inspection, controlled p95 latency measurement |
| FR-QRY-001/002/005 | Structured-output/normalization and failure-preservation tests |
| FR-QRY-003/004/006/007 | User-ownership, provider-spy and stale-generation concurrency tests |
| FR-RET-001–006/009 | Mock OpenAlex responses, budgets, metadata, deduplication and UI tests |
| FR-RET-007/008 | PostgreSQL atomicity, active ownership, lease expiry and stale-worker tests |
| FR-RET-010 | Malicious metadata and URL-scheme browser/security tests |
| FR-RNK-001–007 | Exact-vector fixtures, malformed-output injection, score/order/provenance tests |
| FR-REF-001–008 | Snapshot durability, concurrent save uniqueness and cross-project tests |

Use stable test IDs in test names or metadata and record the specific requirement
IDs each test verifies. Acceptance scenario IDs supplement, not replace, requirements.

## Layers

1. Human review of specifications and acceptance tests before production code.
2. Unit tests of pure validation, normalization, deduplication and scoring.
3. API contract tests including error shapes and ownership boundaries.
4. Integration tests with fake domain providers and HTTPX mock transports for adapters.
5. Actual PostgreSQL migration, transaction and concurrency tests on disposable data.
6. Playwright end-to-end acceptance journey with fake providers.
7. Human keyboard/usability, secret-flow, unsafe-rendering and code-boundary audits.
8. Optional explicit live-provider smoke tests recorded separately from repeatable CI;
   never make paid/live calls part of the default suite.

All tests, results and metrics are currently planned. Do not claim code coverage,
test pass counts, security compliance or ranking accuracy before measurement.

## Project-management performance reference

Approved by the user on 2026-10-12: measure local CRUD p95 below 500 ms over
100 requests with 100 stored projects, excluding startup and external services.
Reference host observed via `lscpu`, `uname -srmo`, and `free -h`:
AMD Ryzen 7 5700X3D (8 cores/16 threads), 31 GiB reported RAM,
Linux 7.2.9-2-cachyos x86_64.

Protocol approved with the 001 plan on 2026-10-12; execution remains pending:

- Run a real local HTTP server with PostgreSQL 17 on this host, using an explicitly
  disposable test database, not the application or original database.
- Seed 100 projects. Warm up the process/connection pool with 10 untimed read
  requests. Send 20 cycles of POST, GET list, GET detail, PUT, DELETE sequentially,
  using the newly created project in each cycle. Each cycle ends with 100 projects;
  POST temporarily raises the count to 101. Do not time fixture setup or startup.
- Time from immediately before sending the request until its full response body is
  received using a monotonic clock and one persistent HTTP client. Include server
  validation, database work/commit, serialization, and loopback transport. Record
  failed requests and fail the run rather than omit them from the sample.
- Retain all 100 raw durations and operation labels. Sort durations ascending and
  take the 95th value (nearest-rank p95); require it below 500 ms. Report per-operation
  timings separately without claiming a per-operation acceptance budget.
- Record commit, commands, Python/dependency/PostgreSQL/browser versions, database
  configuration without credentials, machine load, OS, and CPU/RAM. Use the same
  protocol for any comparison; report deviations rather than silently changing it.

No benchmark has been run; the approved budget is not acceptance evidence.

## Comparing vibe coding with SDD

- Freeze baseline working-tree state and rebuild commit before comparison.
- Evaluate only overlapping functionality with the same frozen provider responses,
  vectors, input data and hardware; document intended differences separately.
- Record effort prospectively, prompt revisions, defects, rework and review effort.
  Avoid claiming a fair historical timing comparison when original timing is missing.
- Human-rate a small frozen paper set to evaluate ranking usefulness separately
  from deterministic formula correctness; define criteria before reviewing rankings.
- Threats to validity: prior knowledge from rebuilding, reduced scope, model/version
  differences, live-provider variability, same AI writing code/tests, incomplete
  historical evidence and small-team/sample size.
- Human review and mutation/fault tests help prevent AI-generated tests merely
  restating mistakes in AI-generated code.

## Course report

Follow the supplied title, team table, 200–300-word executive summary, and sections
1–7 including all subsections. Write outcomes only when evidence exists. Identify
tools/models with exact observed versions; do not invent team contribution percentages.
Include prompt iteration/audit/test tables and a reusable process diagram in §7.4.
No final experience report has been generated at this planning stage.
