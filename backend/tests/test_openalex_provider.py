"""FR-RET-001–003/009: HTTPX-mocked OpenAlex mapping and bounds; never live."""

import asyncio
import logging

import httpx
import pytest
from conftest import run_async
from researchpilot.integrations.openalex_papers import OpenAlexPaperProvider, build_client
from researchpilot.paper_provider import PaperProviderError

WORK = {
    "id": "https://openalex.org/W1",
    "doi": "https://doi.org/10.1234/Example",
    "title": "A provider title",
    "abstract_inverted_index": {"An": [0], "abstract": [1], "from": [2], "OpenAlex": [3]},
    "authorships": [
        {"author": {"display_name": "Ada Author"}},
        {"author": {"display_name": "Grace Author"}},
    ],
    "publication_year": 2024,
    "publication_date": "2024-03-01",
    "primary_location": {
        "source": {"display_name": "Journal of Tests"},
        "landing_page_url": "https://publisher.example/paper",
    },
    "best_oa_location": {
        "landing_page_url": "https://repository.example/paper",
        "pdf_url": "https://repository.example/paper.pdf",
    },
    "open_access": {"is_oa": True},
    "cited_by_count": 9,
}


def provider(handler, **options):
    requests = []

    async def record(request):
        requests.append(request)
        result = handler(request)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    client = httpx.AsyncClient(transport=httpx.MockTransport(record), trust_env=False)
    return OpenAlexPaperProvider(client=client, **options), requests


def search(instance, query="AI tutors", year_from=2020, year_to=2024, limit=10):
    async def run():
        try:
            return await instance.search(query, year_from, year_to, limit)
        finally:
            await instance.aclose()

    return run_async(run())


def response(records, *, count=None, page=1, per_page=25, cost_usd=None):
    meta = {"count": len(records) if count is None else count, "page": page, "per_page": per_page}
    if cost_usd is not None:
        meta["cost_usd"] = cost_usd
    return httpx.Response(200, json={"meta": meta, "results": records})


def test_FR_RET_001_request_sends_exact_query_and_inclusive_year_filters_only():
    instance, requests = provider(lambda request: response([]))
    result = search(instance, query="  AI & tutors? ", limit=3)
    request = requests[0]
    params = dict(request.url.params)
    assert request.method == "GET"
    assert request.url.scheme == "https"
    assert request.url.host == "api.openalex.org"
    assert request.url.path == "/works"
    assert params["search"] == "  AI & tutors? "
    assert params["filter"] == ("from_publication_date:2020-01-01,to_publication_date:2024-12-31")
    assert params["per_page"] == "3" and params["page"] == "1"
    assert "api_key" not in params
    assert "projectQuestion" not in params and "keywords" not in params
    assert "authorization" not in request.headers
    assert result.request_count == 1 and result.raw_count == 0


def test_FR_RET_001_002_unbounded_year_and_zero_budget_make_no_extra_request():
    instance, requests = provider(lambda request: response([]))
    result = search(instance, year_from=None, year_to=None, limit=0)
    assert result.papers == [] and result.request_count == 0
    assert requests == []


def test_FR_RET_003_provider_fields_and_abstract_index_are_normalized():
    instance, _ = provider(lambda request: response([WORK]))
    result = search(instance)
    paper = result.papers[0]
    assert paper.provider == "openalex" and paper.provider_id == "https://openalex.org/W1"
    assert paper.doi == "10.1234/example"
    assert paper.title == "A provider title"
    assert paper.abstract == "An abstract from OpenAlex"
    assert paper.authors == ["Ada Author", "Grace Author"]
    assert paper.publication_year == 2024 and str(paper.publication_date) == "2024-03-01"
    assert paper.venue == "Journal of Tests" and paper.citation_count == 9
    assert paper.source_url == "https://openalex.org/W1"
    assert paper.publication_url == "https://publisher.example/paper"
    assert paper.full_text_url == "https://repository.example/paper.pdf"
    assert paper.is_open_access is True


def test_FR_RET_003_missing_title_is_skipped_and_counted():
    instance, _ = provider(lambda request: response([WORK, {"id": "https://openalex.org/W2"}]))
    result = search(instance, limit=2)
    assert len(result.papers) == 1
    assert result.raw_count == 2 and result.skipped_count == 1


def test_FR_RET_006_provider_cost_metadata_is_typed_and_optional():
    instance, _ = provider(lambda request: response([WORK], cost_usd=0.001))
    result = search(instance)
    assert result.provider_cost_usd == 0.001
    malformed, _ = provider(lambda request: response([WORK], cost_usd="private"))
    assert search(malformed).provider_cost_usd is None


def test_FR_RET_009_missing_optional_metadata_stays_absent():
    minimal = {"id": "https://openalex.org/W4", "title": "Minimal"}
    instance, _ = provider(lambda request: response([minimal]))
    paper = search(instance).papers[0]
    assert paper.abstract is None and paper.doi is None and paper.authors == []
    assert paper.publication_url is None and paper.full_text_url is None
    assert paper.is_open_access is None


def test_FR_RET_002_paging_never_exceeds_allocation_or_openalex_max_page_size():
    calls = []

    def handler(request):
        params = request.url.params
        page = int(params["page"])
        per_page = int(params["per_page"])
        calls.append((page, per_page))
        records = [
            {
                **WORK,
                "id": f"https://openalex.org/W{page}-{index}",
                "doi": f"10.1234/{page}-{index}",
                "title": f"Work {page}-{index}",
            }
            for index in range(per_page)
        ]
        return response(records, count=500, page=page, per_page=per_page)

    instance, _ = provider(handler)
    result = search(instance, year_from=None, year_to=None, limit=250)
    assert calls == [(1, 100), (2, 100), (3, 50)]
    assert result.request_count == 3 and result.raw_count == 250


@pytest.mark.parametrize(
    "status,category",
    [
        (400, "unavailable"),
        (401, "unavailable"),
        (403, "unavailable"),
        (404, "unavailable"),
        (408, "timeout"),
        (429, "rate_limited"),
        (500, "unavailable"),
        (503, "unavailable"),
        (504, "timeout"),
        (302, "unavailable"),
    ],
)
def test_FR_RET_007_provider_http_failures_are_sanitized_without_retry(status, category):
    instance, requests = provider(lambda request: httpx.Response(status, text="SECRET query body"))
    with pytest.raises(PaperProviderError) as raised:
        search(instance)
    assert raised.value.category == category
    assert len(requests) == 1
    assert "SECRET" not in str(raised.value)


def test_FR_RET_003_invalid_json_or_envelope_fails_closed():
    for response_value in [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"results": "not-a-list"}),
        httpx.Response(200, json=[]),
    ]:
        instance, _ = provider(lambda request, value=response_value: value)
        with pytest.raises(PaperProviderError) as raised:
            search(instance)
        assert raised.value.category == "invalid_response"


def test_FR_RET_010_unsafe_optional_urls_are_omitted():
    unsafe = {
        **WORK,
        "primary_location": {
            "source": {"display_name": "Journal"},
            "landing_page_url": "javascript:alert(1)",
        },
        "best_oa_location": {"pdf_url": "data:text/html,bad"},
    }
    instance, _ = provider(lambda request: response([unsafe]))
    paper = search(instance).papers[0]
    assert paper.publication_url is None and paper.full_text_url is None


def test_FR_RET_007_oversized_response_is_rejected_incrementally():
    instance, _ = provider(
        lambda request: httpx.Response(200, content=b" " * 2049), max_body_bytes=2048
    )
    with pytest.raises(PaperProviderError) as raised:
        search(instance)
    assert raised.value.category == "invalid_response"


def test_FR_RET_007_only_safe_typed_metadata_is_logged(caplog):
    caplog.set_level(logging.DEBUG)
    instance, _ = provider(lambda request: httpx.Response(503, text="SECRET body"))
    with pytest.raises(PaperProviderError):
        search(instance, query="PRIVATE query")
    assert "SECRET" not in caplog.text and "PRIVATE" not in caplog.text


def test_FR_RET_007_cancellation_propagates_and_does_not_retry():
    started = asyncio.Event()
    requests = []

    async def handler(request):
        requests.append(request)
        started.set()
        await asyncio.sleep(5)

    instance, _ = provider(handler)

    async def run():
        task = asyncio.create_task(instance.search("query", None, None, 1))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await instance.aclose()

    run_async(run())
    assert len(requests) == 1


def test_FR_RET_007_http_client_security_and_pool_bounds():
    client = build_client()
    try:
        assert client.follow_redirects is False
        assert client._trust_env is False
        assert client.timeout.connect == 2 and client.timeout.read == 8
        assert client.timeout.write == 2 and client.timeout.pool == 1
        assert client._transport._pool._max_connections == 2
    finally:
        run_async(client.aclose())
