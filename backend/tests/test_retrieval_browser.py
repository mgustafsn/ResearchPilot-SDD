"""FR-RET-001/006/007/008/009/010 browser journeys with a fake provider."""

import asyncio
import threading

from playwright.sync_api import expect
from researchpilot.paper_domain import Paper
from researchpilot.paper_provider import PaperProviderError, PaperSearchResult


class RetrievalProvider:
    def __init__(self, results, blocked=False, fail_on_call=None):
        self.results = list(results)
        self.calls = []
        self.fail_on_call = fail_on_call
        self.started = threading.Event()
        self.release = threading.Event()
        if not blocked:
            self.release.set()

    async def search(self, query, year_from, year_to, limit):
        self.calls.append((query, year_from, year_to, limit))
        self.started.set()
        if not await asyncio.to_thread(self.release.wait, 5):
            raise PaperProviderError("timeout")
        if len(self.calls) == self.fail_on_call:
            raise PaperProviderError("rate_limited")
        return PaperSearchResult(papers=self.results.pop(0), raw_count=1, request_count=1)


def provider_paper(title="OpenAlex work", **overrides):
    value = {
        "provider": "openalex",
        "provider_id": "W1",
        "doi": None,
        "title": title,
        "source_url": "https://openalex.org/W1",
        "authors": ["A Author"],
        "publication_year": 2022,
        "venue": "Journal",
        "is_open_access": None,
        "publication_url": "https://publisher.example/work",
    }
    value.update(overrides)
    return Paper.model_construct(**value)


def create_project(page, base):
    page.set_default_timeout(3000)
    page.goto(base)
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_label("Project name", exact=True).fill("Retrieval browser project")
    page.get_by_label("Research question", exact=True).fill("Question not sent")
    page.get_by_label("Keywords (one per line, optional)", exact=True).fill("private keyword")
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.locator("#detail-title")).to_have_text("Retrieval browser project")


def add_query(page, text="AI tutors"):
    page.get_by_label("Query text", exact=True).fill(text)
    page.get_by_role("button", name="Save query", exact=True).click()
    expect(page.locator("#query-list")).to_contain_text(text)


def test_FR_RET_001_006_search_is_explicit_and_displays_provider_results(page, query_server):
    provider = RetrievalProvider([[provider_paper()]])
    with query_server(paper_provider=provider) as base:
        create_project(page, base)
        add_query(page)
        expect(page.locator("#paper-list li")).to_have_count(0)
        expect(page.locator("#search-privacy")).to_contain_text("OpenAlex")
        assert provider.calls == []
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        expect(page.locator("#paper-list")).to_contain_text("OpenAlex work")
        expect(page.locator("#paper-list")).to_contain_text("Open-access status unknown")
        expect(page.get_by_role("link", name="OpenAlex record", exact=True)).to_have_attribute(
            "href", "https://openalex.org/W1"
        )
        expect(page.locator("#paper-list")).not_to_contain_text("Question not sent")
        expect(page.locator("#paper-list")).not_to_contain_text("private keyword")
        assert provider.calls == [("AI tutors", None, None, 100)]


def test_FR_RET_010_malicious_title_is_inert_and_unsafe_links_are_not_rendered(page, query_server):
    unsafe_paper = provider_paper(
        '<img src=x onerror="alert(1)">',
        publication_url="javascript:alert(2)",
        full_text_url="data:text/html,bad",
    )
    provider = RetrievalProvider([[unsafe_paper]])
    with query_server(paper_provider=provider) as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        expect(page.locator("#paper-list")).to_contain_text('<img src=x onerror="alert(1)">')
        expect(page.locator("#paper-list img")).to_have_count(0)
        expect(page.locator("#paper-list [onerror]")).to_have_count(0)
        expect(page.locator('#paper-list a[href^="javascript:"]')).to_have_count(0)
        expect(page.locator('#paper-list a[href^="data:"]')).to_have_count(0)


def test_FR_RET_007_provider_failure_keeps_previous_results_visible(page, query_server):
    provider = RetrievalProvider([[provider_paper("Original", provider_id="W1")]], fail_on_call=2)
    with query_server(paper_provider=provider) as base:
        create_project(page, base)
        add_query(page)
        search = page.get_by_role("button", name="Search OpenAlex", exact=True)
        search.click()
        expect(page.locator("#paper-list")).to_contain_text("Original")
        search.click()
        expect(page.get_by_role("alert")).to_contain_text("OpenAlex is unavailable")
        expect(page.locator("#paper-list")).to_contain_text("Original")
        expect(page.locator("#search-status")).to_contain_text("previous results were kept")


def test_FR_RET_010_late_search_response_does_not_repaint_another_project(page, query_server):
    provider = RetrievalProvider([[provider_paper("Project A result")]], blocked=True)
    with query_server(paper_provider=provider) as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        expect(page.locator("#search-status")).to_contain_text("Searching OpenAlex")
        assert provider.started.wait(5)
        page.get_by_role("button", name="New project", exact=True).click()
        page.get_by_label("Project name", exact=True).fill("Project B")
        page.get_by_label("Research question", exact=True).fill("Another question")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.locator("#detail-title")).to_have_text("Project B")
        provider.release.set()
        expect(page.locator("#detail-title")).to_have_text("Project B")
        expect(page.locator("#paper-list")).not_to_contain_text("Project A result")
