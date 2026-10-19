# PaperProvider / OpenAlex adapter contract — proposal

**Status**: Draft; requires plan/contract approval. No live request is authorized or
performed by this contract.

## Domain interface

```text
PaperProvider.search(query, year_from, year_to, limit) -> PaperSearchResult
```

- `query`: exact stored enabled query text, immutable for the attempt.
- `year_from`, `year_to`: optional inclusive year bounds captured at start.
- `limit`: allocated raw-record budget for this one query; integer 0–250. A zero
  allocation is not sent to the provider.
- `PaperSearchResult`: normalized `Paper` tuple, raw record count, request/page count.
- `PaperProviderError`: safe fixed categories `rate_limited`, `timeout`,
  `unavailable`, `invalid_response`.

The service/domain imports only these common types and protocol. The adapter alone
knows OpenAlex field names, URL, query parameters, and response envelope. No vendor
SDK is proposed.

## OpenAlex request proposal

- HTTPS GET to `https://api.openalex.org/works`.
- `search` contains the exact saved query. Do not send project question, keywords,
  project name, API key, or unused query text.
- For each supplied year bound, apply the corresponding inclusive date filter:
  `from_publication_date:YYYY-01-01` and/or
  `to_publication_date:YYYY-12-31`.
- Set `per_page` no higher than 100 and page only until the query allocation is
  satisfied. Use `select` for only the fields in `data-model.md`. Do not request
  `rerank`, semantic search, full-text content, or cursor paging.
- No API key by default, no paid plan/account setup, TLS verification enabled,
  redirects disabled, `trust_env=False`, at most two concurrent calls, at most 20
  actual requests per attempt, proposed 10-second request / 120-second attempt
  deadline, and no retry. All numeric values are proposals requiring approval.

## Mapping/validation

Map OpenAlex work IDs, DOI, title, abstract inverted index, author bylines, year/date,
primary source, locations, OA status and citation count into `Paper`. Rebuild abstract
tokens by ascending nonnegative integer positions; omit invalid optional abstracts.
Require an OpenAlex identity and nonblank title for a displayed work. Count and skip
missing-title/malformed individual records only where the envelope remains structurally
valid; malformed/incomplete envelopes fail the attempt. Preserve missing optionals.
Never infer OA status from URL presence. Validate all provider URLs as absolute
`http`/`https` URLs without credentials. Never download a linked resource.

## Failure and observability

- 429, timeout, transport error, non-success response, malformed envelope, oversized
  response or invalid required data fail the whole attempt. No partial commit or retry.
- Sanitize to a fixed error code/message. Never log raw query strings, full request
  URLs, response body, headers, exception text, or credentials. Log provider name,
  page/request count, status category, duration, returned/skipped/duplicate counts,
  and any typed usage metadata supplied by the response.
- Tests use HTTPX `MockTransport` and fake providers; no OpenAlex network calls in CI.
