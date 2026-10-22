"""FR-RNK-005 score/disclosure journey with test-only fake providers."""

from conftest import FakeEmbeddingProvider
from playwright.sync_api import expect
from test_retrieval_api import FakePaperProvider
from test_retrieval_browser import add_query, create_project


def test_FR_RNK_005_local_ranking_labels_and_failure(page, query_server):
    embeddings = FakeEmbeddingProvider()
    with query_server(paper_provider=FakePaperProvider(), embedding_provider=embeddings) as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        page.get_by_text("Embedding similarity:", exact=False).wait_for()
        assert page.get_by_text("not a probability", exact=False).is_visible()
        assert page.get_by_text("256", exact=False).count() > 0
        embeddings.failure = "model_missing"
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        page.get_by_text("Local embedding model is missing", exact=False).wait_for()
        assert page.get_by_text("Embedding similarity:", exact=False).is_visible()


def test_FR_RNK_005_zero_percent_truncation_and_refresh(page, query_server):
    class ZeroEmbeddings(FakeEmbeddingProvider):
        async def embed(self, inputs):
            result = await super().embed(inputs)
            for item in result.items[1:]:
                item.vector = [0.0] * 384
                item.truncated = True
            result.items[0].truncated = True
            return result

    with query_server(
        paper_provider=FakePaperProvider(), embedding_provider=ZeroEmbeddings()
    ) as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("button", name="Search OpenAlex", exact=True).click()
        expect(page.locator("#paper-list")).to_contain_text("Embedding similarity: 0.0%")
        expect(page.locator("#paper-list")).to_contain_text("Paper input was truncated")
        expect(page.locator("#ranking-model")).to_contain_text(
            "Research-question/keyword input was truncated"
        )
        page.reload()
        page.get_by_role("button", name="Retrieval browser project", exact=True).click()
        expect(page.locator("#paper-list")).to_contain_text("Embedding similarity: 0.0%")
