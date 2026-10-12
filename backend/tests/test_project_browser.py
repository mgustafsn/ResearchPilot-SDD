"""AC-PRJ-001–004 and NFR-PRJ-002 against Chromium and real PostgreSQL."""

from playwright.sync_api import expect


def fill_project(page, title="Browser project", question="A browser research question"):
    page.get_by_label("Project name", exact=True).fill(title)
    page.get_by_label("Research question", exact=True).fill(question)


def test_FR_PRJ_001_005_AC_PRJ_001_004_create_reopen(page, live_server):
    with live_server() as base:
        page.goto(base)
        expect(page.get_by_text("No projects yet.", exact=True)).to_be_visible()
        page.get_by_role("button", name="New project", exact=True).click()
        expect(page.get_by_label("Paper limit", exact=True)).to_have_value("100")
        fill_project(page)
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.locator("#detail-title")).to_have_text("Browser project")
        page.reload()
        page.get_by_role("button", name="Browser project", exact=True).click()
        expect(page.locator("#detail-question")).to_have_text("A browser research question")


def test_FR_PRJ_007_NFR_PRJ_002_validation_preserves_form(page, live_server):
    with live_server() as base:
        page.goto(base)
        page.get_by_role("button", name="New project", exact=True).click()
        fill_project(page, title="   ")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Please check")
        expect(page.get_by_label("Project name", exact=True)).to_have_value("   ")
        expect(page.get_by_label("Research question", exact=True)).to_have_value(
            "A browser research question"
        )
        expect(page.get_by_label("Project name", exact=True)).to_have_attribute(
            "aria-invalid", "true"
        )


def test_FR_PRJ_007_storage_error_preserves_form(page, live_server):
    with live_server() as base:
        page.goto(base)
        page.get_by_role("button", name="New project", exact=True).click()
        fill_project(page)
        page.route("**/api/projects", lambda route: route.fulfill(status=503,
            content_type="application/json", body='{"error":{"message":"Storage unavailable",'
            '"fields":[]}}') if route.request.method == "POST" else route.continue_())
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Storage unavailable")
        expect(page.get_by_label("Project name", exact=True)).to_have_value("Browser project")


def test_NFR_PRJ_002_keyboard_create(page, live_server):
    with live_server() as base:
        page.goto(base)
        page.get_by_role("button", name="New project", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_label("Project name", exact=True)).to_be_focused()
        page.keyboard.type("Keyboard project")
        page.keyboard.press("Tab")
        expect(page.get_by_label("Research question", exact=True)).to_be_focused()
        page.keyboard.type("Keyboard question")
        page.get_by_role("button", name="Save project", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.locator("#detail-title")).to_have_text("Keyboard project")
