"""Real Chromium/PostgreSQL query journeys with disabled or injected fake providers."""

from conftest import FakeSuggestionProvider
from playwright.sync_api import expect
from researchpilot.query_provider import SuggestionProviderError


def create_project(page, base, name="Manual query project", navigate=True):
    page.set_default_timeout(3000)
    if navigate:
        page.goto(base)
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_label("Project name", exact=True).fill(name)
    page.get_by_label("Research question", exact=True).fill("Research question")
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.locator("#detail-title")).to_have_text(name)


def add_query(page, value="AI tutors"):
    page.get_by_label("Query text", exact=True).fill(value)
    page.get_by_role("button", name="Save query", exact=True).click()
    expect(page.locator("#query-list")).to_contain_text(value)


def test_FR_QRY_003_manual_controls_reopen_edit_delete(page, query_server):
    with query_server() as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("checkbox", name="Use query: AI tutors", exact=True).uncheck()
        checkbox = page.get_by_role("checkbox", name="Use query: AI tutors", exact=True)
        expect(checkbox).not_to_be_checked()
        expect(checkbox).to_be_enabled()
        page.reload()
        page.get_by_role("button", name="Manual query project", exact=True).click()
        expect(
            page.get_by_role("checkbox", name="Use query: AI tutors", exact=True)
        ).not_to_be_checked()
        page.get_by_role("button", name="Edit query", exact=True).click()
        page.get_by_label("Query text", exact=True).fill("Edited query")
        page.get_by_role("button", name="Save query", exact=True).click()
        expect(page.locator("#query-list")).to_contain_text("Edited query")
        page.get_by_role("button", name="Delete query", exact=True).click()
        expect(page.locator("#query-list li")).to_have_count(0)


def test_FR_QRY_002_005_failed_query_preserves_input(page, query_server):
    with query_server() as base:
        create_project(page, base)
        page.get_by_label("Query text", exact=True).fill("   ")
        page.get_by_role("button", name="Save query", exact=True).click()
        expect(page.get_by_role("alert")).to_be_visible()
        expect(page.get_by_label("Query text", exact=True)).to_have_value("   ")
        expect(page.get_by_label("Query text", exact=True)).to_have_attribute(
            "aria-invalid", "true"
        )
        expect(page.locator("#query-list li")).to_have_count(0)


def test_FR_QRY_003_010_hostile_query_text_renders_as_inert_text(page, query_server):
    hostile = '<img src=x onerror="alert(1)"> query'
    with query_server() as base:
        create_project(page, base)
        query_input = page.get_by_label("Query text", exact=True)
        query_input.fill(hostile)
        query_input.press("Tab")
        save_button = page.get_by_role("button", name="Save query", exact=True)
        expect(save_button).to_be_focused()
        save_button.press("Enter")
        expect(page.locator("#query-list")).to_contain_text(hostile)
        expect(page.locator("#query-list img")).to_have_count(0)
        expect(page.locator("#query-list [onerror]")).to_have_count(0)


def test_FR_QRY_009_context_notice_survives_reopen(page, query_server):
    with query_server() as base:
        create_project(page, base)
        add_query(page)
        page.get_by_role("button", name="Edit project", exact=True).click()
        page.get_by_label("Research question", exact=True).fill("New question")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.locator("#query-refresh")).to_be_visible()
        expect(page.locator("#query-list")).to_contain_text("AI tutors")
        page.reload()
        page.get_by_role("button", name="Manual query project", exact=True).click()
        expect(page.locator("#query-refresh")).to_be_visible()


# --- FR-QRY-001/003–010: explicit generation with injected fake providers ---


class FailingProvider:
    def __init__(self, category):
        self.category, self.contexts = category, []

    async def suggest(self, context):
        self.contexts.append(context)
        raise SuggestionProviderError(self.category)


def generate_button(page):
    return page.get_by_role("button", name="Generate suggestions", exact=True)


def test_FR_QRY_005_missing_provider_disables_generate_not_manual(page, query_server):
    with query_server() as base:
        create_project(page, base)
        expect(generate_button(page)).to_be_disabled()
        expect(page.locator("#query-availability")).to_contain_text("not configured")
        add_query(page)


def test_FR_QRY_001_explicit_generation_privacy_and_result(page, query_server):
    provider = FakeSuggestionProvider(queries=("AI tutoring", "Feedback", "<b>Learning</b>"))
    with query_server(provider) as base:
        create_project(page, base)
        page.get_by_role("button", name="Edit project", exact=True).click()
        page.get_by_label("Research question", exact=True).fill("Changed question")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.locator("#query-refresh")).to_be_visible()
        expect(page.locator("#query-privacy")).to_contain_text("OpenAI")
        assert provider.contexts == []  # Load and project edits never call the provider.
        page.get_by_label("Query text", exact=True).fill("Unsaved draft")
        generate_button(page).click()
        status = page.locator("#generation-status")
        expect(status).to_contain_text("3 added")
        expect(page.locator("#query-list li")).to_have_count(3)
        expect(page.locator("#query-list")).to_contain_text("generated · untouched suggestion")
        expect(page.locator("#query-list b")).to_have_count(0)
        expect(page.locator("#query-list")).to_contain_text("<b>Learning</b>")
        expect(page.locator("#query-refresh")).to_be_hidden()
        expect(page.get_by_label("Query text", exact=True)).to_have_value("Unsaved draft")
        assert len(provider.contexts) == 1
        assert provider.contexts[0].question == "Changed question"


def test_FR_QRY_004_008_regeneration_keeps_owned_and_reports_skips(page, query_server):
    provider = FakeSuggestionProvider(queries=("First", "Second", "Third"))
    with query_server(provider) as base:
        create_project(page, base)
        generate_button(page).click()
        expect(page.locator("#query-list li")).to_have_count(3)
        page.get_by_role("checkbox", name="Use query: Second", exact=True).uncheck()
        expect(page.locator("#query-list")).to_contain_text("user-owned")
        provider.queries = ("second", "Fourth", "Fifth")
        generate_button(page).click()
        expect(page.locator("#generation-status")).to_contain_text("1 skipped as duplicate")
        expect(
            page.get_by_role("checkbox", name="Use query: Second", exact=True)
        ).not_to_be_checked()
        expect(page.locator("#query-list")).not_to_contain_text("First")
        expect(page.locator("#query-list li")).to_have_count(3)


def test_FR_QRY_005_failure_keeps_list_and_input(page, query_server):
    with query_server(FailingProvider("timeout")) as base:
        create_project(page, base)
        add_query(page, "Kept query")
        page.get_by_label("Query text", exact=True).fill("Unsaved")
        generate_button(page).click()
        expect(page.get_by_role("alert")).to_contain_text("took too long")
        expect(page.locator("#query-list li")).to_have_count(1)
        expect(page.get_by_label("Query text", exact=True)).to_have_value("Unsaved")
        expect(generate_button(page)).to_be_enabled()
        page.get_by_role("button", name="Save query", exact=True).click()
        expect(page.locator("#query-list li")).to_have_count(2)


def test_FR_QRY_007_manual_work_while_pending_makes_result_stale(page, query_server):
    provider = FakeSuggestionProvider(blocked=True)
    with query_server(provider) as base:
        create_project(page, base)
        generate_button(page).click()
        expect(page.locator("#generation-status")).to_contain_text("Generating")
        expect(generate_button(page)).to_be_disabled()
        assert provider.started.wait(5)
        generate_button(page).click(force=True)
        add_query(page, "Added while pending")
        page.get_by_label("Query text", exact=True).fill("Still typing")
        provider.release.set()
        expect(page.get_by_role("alert")).to_contain_text("changed while suggestions")
        expect(page.locator("#query-list li")).to_have_count(1)
        expect(page.get_by_label("Query text", exact=True)).to_have_value("Still typing")
        expect(generate_button(page)).to_be_enabled()
        assert len(provider.contexts) == 1


def test_FR_QRY_007_edit_while_pending_keeps_new_text_and_rejects_result(page, query_server):
    provider = FakeSuggestionProvider()
    with query_server(provider) as base:
        create_project(page, base)
        add_query(page, "Original query")
        provider.release.clear()
        provider.started.clear()
        generate_button(page).click()
        expect(page.locator("#generation-status")).to_contain_text("Generating")
        assert provider.started.wait(5)
        page.get_by_role("button", name="Edit query", exact=True).click()
        query_input = page.get_by_label("Query text", exact=True)
        query_input.fill("Edited while pending")
        page.get_by_role("button", name="Save query", exact=True).click()
        expect(page.locator("#query-list")).to_contain_text("Edited while pending")
        provider.release.set()
        expect(page.get_by_role("alert")).to_contain_text("changed")
        expect(page.locator("#query-list")).to_contain_text("Edited while pending")
        expect(page.locator("#query-list")).not_to_contain_text("First")


def test_FR_QRY_010_navigation_while_pending_never_repaints_other_project(page, query_server):
    provider = FakeSuggestionProvider(queries=("Alpha", "Beta", "Gamma"), blocked=True)
    with query_server(provider) as base:
        create_project(page, base, "Project A")
        generate_button(page).click()
        assert provider.started.wait(5)
        create_project(page, base, "Project B", navigate=False)
        expect(generate_button(page)).to_be_enabled()
        provider.release.set()
        page.wait_for_timeout(500)
        expect(page.locator("#detail-title")).to_have_text("Project B")
        expect(page.locator("#query-list li")).to_have_count(0)
        expect(page.locator("#generation-status")).not_to_contain_text("added")
        expect(page.get_by_role("alert")).to_be_hidden()
        page.get_by_role("button", name="Project A", exact=True).click()
        expect(page.locator("#query-list li")).to_have_count(3)


def test_FR_QRY_010_deleted_project_while_pending_is_not_reopened(page, query_server):
    provider = FakeSuggestionProvider(blocked=True)
    with query_server(provider) as base:
        create_project(page, base, "Doomed")
        generate_button(page).click()
        assert provider.started.wait(5)
        page.get_by_role("button", name="Delete project", exact=True).click()
        page.get_by_role("button", name="Delete permanently", exact=True).click()
        expect(page.locator("#detail")).to_be_hidden()
        provider.release.set()
        page.wait_for_timeout(500)
        expect(page.locator("#detail")).to_be_hidden()
        expect(page.get_by_role("alert")).to_be_hidden()
        expect(page.get_by_role("button", name="Doomed", exact=True)).to_have_count(0)
