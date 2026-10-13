"""Real Chromium/PostgreSQL manual-query journeys, with provider injection disabled."""

from playwright.sync_api import expect


def create_project(page, base):
    page.set_default_timeout(3000)
    page.goto(base)
    page.get_by_role("button", name="New project", exact=True).click()
    page.get_by_label("Project name", exact=True).fill("Manual query project")
    page.get_by_label("Research question", exact=True).fill("Research question")
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.locator("#detail-title")).to_have_text("Manual query project")


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
        expect(page.get_by_role("checkbox", name="Use query: AI tutors", exact=True)
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
            "aria-invalid", "true")
        expect(page.locator("#query-list li")).to_have_count(0)


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
