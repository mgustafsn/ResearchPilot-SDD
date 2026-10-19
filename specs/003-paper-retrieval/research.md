# Feature 003 research — OpenAlex retrieval

**Status**: Research supporting the approved implementation plan.
**Research date**: 2026-10-19. Official documentation was read; no OpenAlex API
request, provider smoke test, or other live data access was performed.

## Decisions and rationale

### Use the OpenAlex Works search endpoint through HTTPX

- **Decision**: Implement the approved `PaperProvider` with the existing HTTPX
  dependency, calling `GET https://api.openalex.org/works` only after explicit Search.
  Send the enabled query text and inclusive publication-date filters. Do not send
  question/keywords; retain those only in the saved attempt snapshot. No OpenAI call.
- **Rationale**: OpenAlex documents `search` across work title, abstract, full text,
  and keywords, plus inclusive `from_publication_date` and `to_publication_date`
  filters. These match the clarified product behavior without extra query rewriting.
  Existing HTTPX avoids a new dependency family and keeps the external service behind
  the provider boundary.
- **Alternatives considered**: A vendor SDK (unnecessary dependency); semantic/rerank
  endpoint (out of scope and can add model-derived relevance); appending project
  question/keywords (rejected by approved clarification); full-text downloads
  (explicitly excluded and create licensing/storage risks).

### Bound requests to the user-approved raw-result limit

- **Decision**: Follow FR-RET-002 allocation in stored query order; page only until
  each query's allocation is met, use `per_page` no greater than 100, and cap total
  requests at 20 per search attempt. No automatic retries. At most two concurrent
  HTTP requests; approved timeout/lease values are specified in the plan.
- **Rationale**: OpenAlex currently documents `per_page` max 100, basic pagination up
  to the first 10,000 results, and no-key request rate of 10/second. The MVP limit is
  250 records with at most 20 saved queries, so bounded basic paging can satisfy this
  without cursor paging or an API key. A hard request cap and no retries make costs
  and load auditable. A 429 or timeout fails the all-query attempt and preserves old
  results per the approved spec.
- **Alternatives considered**: Cursor paging (requires a key beyond the first page
  and is unnecessary under 250); unbounded pagination (violates project limit);
  automatic retry (can exceed request/cost bounds and complicates all-or-nothing
  semantics); higher concurrency (unnecessary for single-user local deployment).

### Map OpenAlex records into normalized provider-owned metadata

- **Decision**: Use OpenAlex work ID as provider identity; map DOI, title, abstract,
  authors, date/year, venue, citation count, source/publication/open-access links,
  and access status into common `Paper`. Reconstruct plaintext abstract from
  `abstract_inverted_index` positions. Do not persist raw provider envelopes.
- **Rationale**: OpenAlex work list records provide the required metadata, but abstracts
  are distributed as an inverted index rather than plaintext. `best_oa_location`,
  `primary_location` and `open_access` supply separate link/status fields. Missing
  data must remain missing; source data is untrusted and should render as text.
  Work-list records include at most 100 authors; no per-work follow-up request is
  proposed because it would multiply calls and exceed this slice's bounded design.
- **Alternatives considered**: Fetch full work separately for every result (adds
  requests, cost and complexity); assume a plaintext abstract exists (incorrect);
  infer access status from a missing URL (incorrect); download full text (out of scope).

### Respect provider identity and conflicting DOI constraints

- **Decision**: Deduplicate by canonical DOI, then OpenAlex ID, then normalized title.
  Never merge two distinct nonempty DOIs through title matching. Select the richest
  normalized record deterministically and fill gaps only.
- **Rationale**: DOI is the canonical external work identifier; OpenAlex ID is the
  stable provider identity. Conservative conflict handling prevents false merges.
  The spec assigns richness scoring/tie-breaking and transitive-bridge details to the
  plan; exact algorithm remains a plan proposal awaiting review.
- **Alternatives considered**: Merge all same-title records (violates DOI conflict
  rule); choose whichever response arrives last (nondeterministic); overwrite all
  provider fields on every response (loses richer records).

## Current official references

1. OpenAlex, [Works search](https://docs.openalex.org/api-entities/works/search-works),
   last updated 2026-10-03. Documents search fields, defaults, relevance score, and
   the per-call price for search requests.
2. OpenAlex, [Work filters](https://docs.openalex.org/api-entities/works/filter-works),
   last updated 2026-10-03. Documents inclusive publication-date filters and filter
   composition.
3. OpenAlex, [Rate limits and authentication](https://docs.openalex.org/api-reference/authentication/),
   last updated 2026-10-15. Documents no-key basic usage, 10 requests/second without
   a key, key/paid quota distinctions, per-page limits and usage metadata.
4. OpenAlex, [Work object attributes](https://docs.openalex.org/api-entities/works/work-object),
   last updated 2026-10-17. Documents DOI, title, abstract inverted index, authorships,
   publication fields, locations and open-access shape.
5. OpenAlex, [API reference/rate limits](https://docs.openalex.org/api-reference/rate-limits).
   Documents endpoint base URL, response envelope, `meta.cost_usd`, and safe treatment
   of untrusted data.
6. Repository source review: existing `pyproject.toml` includes runtime HTTPX;
   `Database` uses local PostgreSQL and versioned SQL migrations; feature 002 already
   supplies parent-first project/query revision locks and guarded PostgreSQL/browser
   testing patterns.

## Open questions intentionally left for plan approval

- The approved request/body/deadline limits, two-request concurrency, 150-second
  lease, and local pipeline p95 budget require implementation evidence, not reapproval.
- Richness scoring/tie handling and the identity-bridge algorithm are stated in the
  approved plan and require regression tests.
- No live OpenAlex smoke test, API key creation, usage-account setup, or paid call is
  included. Search calls in the running app remain an explicit user action.
