"""Bounded HTTPX adapter for OpenAlex Work search; never calls an LLM."""

import asyncio
import json
import logging
import math
import time
from datetime import date

import httpx
from pydantic import ValidationError

from researchpilot.paper_domain import (
    Paper,
    publication_year_filters,
    reconstruct_abstract,
    safe_provider_url,
)
from researchpilot.paper_provider import PaperProviderError, PaperSearchResult

ENDPOINT = "https://api.openalex.org/works"
MAX_PER_PAGE = 100
MAX_REQUESTS_PER_ATTEMPT = 20
MAX_BODY_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 10
PHASE_TIMEOUT = httpx.Timeout(connect=2, pool=1, write=2, read=8)
LIMITS = httpx.Limits(max_connections=2, max_keepalive_connections=2)
SELECT = ",".join(
    (
        "id",
        "doi",
        "title",
        "abstract_inverted_index",
        "authorships",
        "publication_year",
        "publication_date",
        "primary_location",
        "best_oa_location",
        "open_access",
        "cited_by_count",
    )
)

logger = logging.getLogger("researchpilot.openalex")


def build_client():
    return httpx.AsyncClient(
        timeout=PHASE_TIMEOUT, limits=LIMITS, verify=True, follow_redirects=False, trust_env=False
    )


class OpenAlexPaperProvider:
    def __init__(
        self, client=None, request_timeout=REQUEST_TIMEOUT_SECONDS, max_body_bytes=MAX_BODY_BYTES
    ):
        self._client = client or build_client()
        # HTTPX's INFO access message contains the full query-bearing URL. This
        # adapter emits only typed, URL-free metadata through `logger` below.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._request_timeout = request_timeout
        self._max_body_bytes = max_body_bytes
        self._semaphore = asyncio.Semaphore(2)

    async def aclose(self):
        await self._client.aclose()

    async def search(self, query, year_from, year_to, limit):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("A nonblank stored query is required")
        if type(limit) is not int or not 0 <= limit <= 250:
            raise ValueError("Query allocation must be an integer from 0 to 250")
        filters = publication_year_filters(year_from, year_to)
        if limit == 0:
            return PaperSearchResult(papers=[], raw_count=0, skipped_count=0, request_count=0)

        started = time.monotonic()
        raw_count = skipped_count = request_count = 0
        provider_cost_usd = 0.0
        has_provider_cost = False
        papers = []
        page = 1
        try:
            while len(papers) + skipped_count < limit:
                remaining = limit - len(papers) - skipped_count
                per_page = min(MAX_PER_PAGE, remaining)
                params = {
                    "search": query,
                    "per_page": per_page,
                    "page": page,
                    "select": SELECT,
                }
                if filters:
                    params["filter"] = ",".join(
                        f"{name}:{value}" for name, value in filters.items()
                    )
                request_count += 1
                if request_count > MAX_REQUESTS_PER_ATTEMPT:
                    raise PaperProviderError("invalid_response") from None
                body = await self._fetch(params)
                records, reported_count, page_cost = self._decode(body, per_page)
                if page_cost is not None:
                    provider_cost_usd += page_cost
                    has_provider_cost = True
                if reported_count < 0 or len(records) > per_page:
                    raise PaperProviderError("invalid_response") from None
                if not records:
                    break
                raw_count += len(records)
                for record in records:
                    normalized = self._normalize(record)
                    if normalized is None:
                        skipped_count += 1
                    else:
                        papers.append(normalized)
                if len(records) < per_page:
                    break
                page += 1
            logger.info(
                "OpenAlex search status=success requests=%s raw=%s skipped=%s "
                "cost_usd=%s duration=%.3fs",
                request_count,
                raw_count,
                skipped_count,
                provider_cost_usd if has_provider_cost else None,
                time.monotonic() - started,
            )
            return PaperSearchResult(
                papers=papers,
                raw_count=raw_count,
                skipped_count=skipped_count,
                request_count=request_count,
                provider_cost_usd=provider_cost_usd if has_provider_cost else None,
            )
        except PaperProviderError as error:
            error.raw_count = raw_count
            error.skipped_count = skipped_count
            error.request_count = request_count
            error.provider_cost_usd = provider_cost_usd if has_provider_cost else None
            logger.info(
                "OpenAlex search status=%s requests=%s cost_usd=%s duration=%.3fs",
                error.category,
                request_count,
                error.provider_cost_usd,
                time.monotonic() - started,
            )
            raise

    async def _fetch(self, params):
        try:
            async with asyncio.timeout(self._request_timeout):
                async with self._semaphore:
                    async with self._client.stream("GET", ENDPOINT, params=params) as response:
                        if response.status_code == 429:
                            raise PaperProviderError("rate_limited") from None
                        if response.status_code in {408, 504}:
                            raise PaperProviderError("timeout") from None
                        if response.status_code != 200:
                            raise PaperProviderError("unavailable") from None
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > self._max_body_bytes:
                                raise PaperProviderError("invalid_response") from None
                        return bytes(body)
        except PaperProviderError:
            raise
        except (TimeoutError, httpx.TimeoutException):
            raise PaperProviderError("timeout") from None
        except httpx.HTTPError:
            raise PaperProviderError("unavailable") from None

    @staticmethod
    def _decode(body, per_page):
        try:
            envelope = json.loads(body)
            meta = envelope["meta"]
            records = envelope["results"]
            count = meta["count"]
            if (
                not isinstance(envelope, dict)
                or not isinstance(meta, dict)
                or type(count) is not int
                or not isinstance(records, list)
                or len(records) > per_page
                or any(not isinstance(row, dict) for row in records)
            ):
                raise ValueError
        except (ValueError, TypeError, KeyError):
            raise PaperProviderError("invalid_response") from None
        cost = meta.get("cost_usd")
        if type(cost) not in {int, float} or not math.isfinite(cost) or cost < 0:
            cost = None
        else:
            cost = float(cost)
        return records, count, cost

    @staticmethod
    def _normalize(record):
        provider_id = record.get("id")
        title = record.get("title")
        if not isinstance(title, str) or not title.strip():
            title = record.get("display_name")
        source_url = safe_provider_url(provider_id)
        if not isinstance(provider_id, str) or not provider_id.strip() or source_url is None:
            return None
        if not isinstance(title, str) or not title.strip():
            return None

        authorships = record.get("authorships")
        authors = []
        if isinstance(authorships, list):
            for authorship in authorships[:100]:
                author = authorship.get("author") if isinstance(authorship, dict) else None
                name = author.get("display_name") if isinstance(author, dict) else None
                if isinstance(name, str) and name.strip():
                    authors.append(name)

        publication_date = None
        raw_date = record.get("publication_date")
        if isinstance(raw_date, str):
            try:
                publication_date = date.fromisoformat(raw_date)
            except ValueError:
                pass
        year = record.get("publication_year")
        if type(year) is not int or not 1 <= year <= 9999:
            year = None
        citations = record.get("cited_by_count")
        if type(citations) is not int or citations < 0:
            citations = None

        primary = record.get("primary_location")
        primary = primary if isinstance(primary, dict) else {}
        source = primary.get("source")
        source = source if isinstance(source, dict) else {}
        best = record.get("best_oa_location")
        best = best if isinstance(best, dict) else {}
        open_access = record.get("open_access")
        open_access = open_access if isinstance(open_access, dict) else {}
        full_text = best.get("pdf_url") or best.get("landing_page_url") or open_access.get("oa_url")
        is_oa = open_access.get("is_oa")
        if type(is_oa) is not bool:
            is_oa = None

        try:
            return Paper.model_validate(
                {
                    "provider": "openalex",
                    "provider_id": provider_id,
                    "doi": record.get("doi"),
                    "title": title,
                    "abstract": reconstruct_abstract(record.get("abstract_inverted_index")),
                    "authors": authors,
                    "publication_year": year,
                    "publication_date": publication_date,
                    "venue": source.get("display_name"),
                    "citation_count": citations,
                    "source_url": source_url,
                    "publication_url": safe_provider_url(primary.get("landing_page_url")),
                    "full_text_url": safe_provider_url(full_text),
                    "is_open_access": is_oa,
                }
            )
        except (ValidationError, ValueError, TypeError):
            return None
