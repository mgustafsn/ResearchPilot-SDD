"""FR-RET-002–005 domain behavior; no database or external provider calls."""

import pytest
from researchpilot.paper_domain import (
    Paper,
    allocate_query_budgets,
    deduplicate_papers,
    normalize_doi,
    normalize_title,
    publication_year_filters,
    reconstruct_abstract,
    safe_provider_url,
)


def record(provider_id, doi, title, **values):
    paper = {
        "provider": "openalex",
        "provider_id": provider_id,
        "doi": doi,
        "title": title,
        "source_url": f"https://openalex.org/{provider_id}",
        "authors": [],
        "abstract": None,
        "publication_year": None,
        "publication_date": None,
        "venue": None,
        "citation_count": None,
        "publication_url": None,
        "full_text_url": None,
        "is_open_access": None,
    }
    paper.update(values)
    return paper


def test_FR_RET_002_budget_is_divided_in_enabled_slot_order():
    queries = [
        {"id": "later", "text": "Later", "slot": 4, "enabled": True},
        {"id": "off", "text": "Disabled", "slot": 2, "enabled": False},
        {"id": "first", "text": "First", "slot": 1, "enabled": True},
        {"id": "middle", "text": "Middle", "slot": 3, "enabled": True},
    ]
    used, unused = allocate_query_budgets(queries, 250)
    assert [(q.id, q.limit) for q in used] == [("first", 84), ("middle", 83), ("later", 83)]
    assert unused == []


def test_FR_RET_002_zero_allocation_queries_are_unused_and_not_called():
    queries = [
        {"id": str(slot), "text": f"Q{slot}", "slot": slot, "enabled": True}
        for slot in range(1, 21)
    ]
    used, unused = allocate_query_budgets(queries, 3)
    assert [(item.id, item.limit) for item in used] == [("1", 1), ("2", 1), ("3", 1)]
    assert [item.id for item in unused] == [str(slot) for slot in range(4, 21)]


def test_FR_RET_002_saved_query_cap_keeps_total_page_requests_within_twenty():
    for query_count in range(1, 21):
        queries = [
            {"id": str(slot), "text": f"Q{slot}", "slot": slot, "enabled": True}
            for slot in range(1, query_count + 1)
        ]
        for paper_limit in range(1, 251):
            used, _ = allocate_query_budgets(queries, paper_limit)
            request_count = sum((item.limit + 99) // 100 for item in used)
            assert request_count <= 20


def test_FR_RET_002_more_than_twenty_saved_queries_is_rejected():
    queries = [
        {"id": str(slot), "text": f"Q{slot}", "slot": slot, "enabled": True}
        for slot in range(1, 22)
    ]
    with pytest.raises(ValueError):
        allocate_query_budgets(queries, 250)


@pytest.mark.parametrize("paper_limit", [0, 251, True, "5"])
def test_FR_RET_002_invalid_budget_is_rejected(paper_limit):
    with pytest.raises(ValueError):
        allocate_query_budgets([], paper_limit)


def test_FR_RET_004_doi_normalization_strips_resolver_and_casefolds():
    assert normalize_doi(" DOI: HTTPS://DOI.ORG/10.1234/AbC ") == "10.1234/abc"
    assert normalize_doi(None) is None


def test_FR_RET_004_title_normalization_uses_unicode_ascii_tokens():
    assert normalize_title("  Éducation—AI: 2026! ") == "education ai 2026"
    assert normalize_title("東京") == ""


def test_FR_RET_003_abstract_is_rebuilt_by_token_position():
    assert reconstruct_abstract({"a": [0, 3], "useful": [1], "abstract": [2]}) == (
        "a useful abstract a"
    )
    assert reconstruct_abstract(None) is None


def test_FR_RET_001_year_filters_are_inclusive_and_omitted_when_unbounded():
    assert publication_year_filters(2020, 2024) == {
        "from_publication_date": "2020-01-01",
        "to_publication_date": "2024-12-31",
    }
    assert publication_year_filters(None, 2024) == {"to_publication_date": "2024-12-31"}
    assert publication_year_filters(None, None) == {}


def test_FR_RET_003_paper_requires_provider_identity_title_and_safe_source_url():
    valid = record("W1", None, "A real title")
    assert Paper.model_validate(valid).title == "A real title"
    for invalid in [
        {**valid, "provider_id": ""},
        {**valid, "title": " "},
        {**valid, "source_url": "javascript:alert(1)"},
        {**valid, "is_open_access": "true"},
    ]:
        with pytest.raises(ValueError):
            Paper.model_validate(invalid)


@pytest.mark.parametrize(
    "year_from,year_to", [(0, None), (None, 10000), (2025, 2020), (True, 2025)]
)
def test_FR_RET_001_invalid_year_filters_are_rejected(year_from, year_to):
    with pytest.raises(ValueError):
        publication_year_filters(year_from, year_to)


@pytest.mark.parametrize(
    "value",
    [
        "javascript:alert(1)",
        "data:text/html,unsafe",
        "file:///etc/passwd",
        "//example.org/paper",
        "https://user:pass@example.org/paper",
    ],
)
def test_FR_RET_010_unsafe_or_credentialed_provider_urls_are_rejected(value):
    assert safe_provider_url(value) is None


@pytest.mark.parametrize(
    "value",
    [
        "https://openalex.org/W1",
        "http://example.org/paper",
    ],
)
def test_FR_RET_009_http_and_https_provider_links_are_allowed(value):
    assert safe_provider_url(value) == value


def test_FR_RET_004_same_doi_merges_richer_record_but_distinct_dois_never_merge():
    records = [
        record("W1", "10.1234/SAME", "Study"),
        record(
            "W2",
            "https://doi.org/10.1234/same",
            "Study",
            abstract="A richer abstract",
            authors=["Author"],
        ),
        record("W3", "10.1234/OTHER", "Study"),
    ]
    result = deduplicate_papers(records)
    assert len(result.papers) == 2
    assert result.duplicate_count == 1
    merged = next(paper for paper in result.papers if paper.doi == "10.1234/same")
    assert merged.provider_id == "W2"
    assert merged.abstract == "A richer abstract"


def test_FR_RET_005_doi_less_title_record_cannot_bridge_conflicting_dois():
    records = [
        record("W1", "10.1234/a", "Same title"),
        record("W2", None, "Same title"),
        record("W3", "10.1234/b", "Same title"),
    ]
    result = deduplicate_papers(records)
    assert len(result.papers) == 3
    assert result.duplicate_count == 0


def test_FR_RET_005_title_duplicates_merge_when_doi_set_is_unambiguous():
    records = [
        record("W1", "10.1234/a", "Same title"),
        record("W2", None, "Same title", venue="Journal"),
    ]
    result = deduplicate_papers(records)
    assert len(result.papers) == 1
    assert result.duplicate_count == 1
    assert result.papers[0].doi == "10.1234/a"
    assert result.papers[0].venue == "Journal"
