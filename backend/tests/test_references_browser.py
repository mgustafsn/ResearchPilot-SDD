"""FR-REF-004/006/008 saved-reference browser flows with a fake provider."""

from playwright.sync_api import expect
from researchpilot.paper_domain import Paper
from researchpilot.paper_provider import PaperSearchResult


class ReferencesProvider:
    def __init__(self):
        self.items = [
            Paper.model_validate(
                {
                    "provider": "openalex",
                    "provider_id": "W2",
                    "doi": None,
                    "title": "Zebra result",
                    "authors": ["A. Author"],
                    "source_url": "https://openalex.org/W2",
                    "publication_url": "https://publisher.example/W2",
                }
            ),
            Paper.model_validate(
                {
                    "provider": "openalex",
                    "provider_id": "W1",
                    "doi": "10.1234/test",
                    "title": '<img src=x onerror="alert(1)">',
                    "authors": ["B. Author"],
                    "publication_year": 2024,
                    "source_url": "https://openalex.org/W1",
                    "publication_url": "https://publisher.example/W1",
                }
            ),
        ]

    async def search(self, query, year_from, year_to, limit):
        return PaperSearchResult(papers=self.items, raw_count=len(self.items), request_count=1)


def create_and_search(page, base):
    page.set_default_timeout(3000)
    page.goto(base)
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_label("Project name", exact=True).fill("Saved references project")
    page.get_by_label("Research question", exact=True).fill("Local review question")
    page.get_by_role("button", name="Save project", exact=True).click()
    page.get_by_label("Query text", exact=True).fill("Provider query")
    page.get_by_role("button", name="Save query", exact=True).click()
    page.get_by_role("button", name="Search OpenAlex", exact=True).click()
    expect(page.locator("#paper-list")).to_contain_text('<img src=x onerror="alert(1)">')


def test_FR_REF_004_006_008_save_list_remove_is_safe_and_keeps_search_result(page, query_server):
    provider = ReferencesProvider()
    with query_server(paper_provider=provider) as base:
        create_and_search(page, base)
        paper = page.locator("#paper-list li").filter(has_text='<img src=x onerror="alert(1)">')
        paper.get_by_role("button", name="Save reference", exact=True).click()
        expect(page.locator("#saved-reference-list")).to_contain_text(
            '<img src=x onerror="alert(1)">'
        )
        expect(paper.get_by_role("button", name="Saved", exact=True)).to_be_disabled()
        expect(page.locator("#saved-reference-list li")).to_have_count(1)
        expect(page.locator("#saved-reference-list img")).to_have_count(0)
        expect(page.locator("#saved-reference-list [onerror]")).to_have_count(0)
        expect(
            page.locator('#saved-reference-list a[href="https://openalex.org/W1"]')
        ).to_have_count(1)
        page.locator("#saved-reference-list").get_by_role(
            "button", name="Remove reference", exact=True
        ).click()
        expect(page.locator("#saved-reference-list li")).to_have_count(0)
        expect(page.locator("#paper-list")).to_contain_text('<img src=x onerror="alert(1)">')
        expect(page.locator("#paper-list img")).to_have_count(0)
