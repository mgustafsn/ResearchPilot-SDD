"""AC-PRJ-001–004 and NFR-PRJ-002 against Chromium and real PostgreSQL."""

import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def browser_timeouts(page):
    page.set_default_timeout(3000)


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


def create_project(page, title="Browser project"):
    page.get_by_role("button", name="New project", exact=True).click()
    fill_project(page, title=title)
    page.get_by_role("button", name="Save project", exact=True).click()
    expect(page.locator("#detail-title")).to_have_text(title)


def test_FR_PRJ_006_007_edit_reopen_and_failed_edit(page, live_server):
    with live_server() as base:
        page.goto(base)
        create_project(page)
        page.get_by_role("button", name="Edit project", exact=True).click()
        fill_project(page, title="Edited project")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.locator("#detail-title")).to_have_text("Edited project")
        page.reload()
        page.get_by_role("button", name="Edited project", exact=True).click()
        page.get_by_role("button", name="Edit project", exact=True).click()
        fill_project(page, title="")
        page.get_by_role("button", name="Save project", exact=True).click()
        expect(page.get_by_role("alert")).to_be_visible()
        expect(page.get_by_label("Project name", exact=True)).to_have_value("")
        page.get_by_role("button", name="Cancel", exact=True).click()
        expect(page.locator("#detail-title")).to_have_text("Edited project")


def test_FR_PRJ_008_NFR_PRJ_002_confirm_cancel_and_isolation(page, live_server):
    with live_server() as base:
        page.goto(base)
        create_project(page)
        create_project(page, title="Other project")
        page.get_by_role("button", name="Browser project", exact=True).click()
        deletes = []
        page.on("request", lambda request: deletes.append(request.url)
                if request.method == "DELETE" else None)
        page.get_by_role("button", name="Delete project", exact=True).click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_contain_text("permanently")
        expect(dialog).to_contain_text("no undo")
        dialog.get_by_role("button", name="Cancel deletion", exact=True).press("Enter")
        expect(dialog).not_to_be_visible()
        assert deletes == []
        expect(page.locator("#detail-title")).to_have_text("Browser project")
        page.get_by_role("button", name="Delete project", exact=True).click()
        dialog.get_by_role("button", name="Delete permanently", exact=True).press("Enter")
        expect(page.get_by_role("button", name="Browser project", exact=True)).to_have_count(0)
        expect(page.get_by_role("button", name="Other project", exact=True)).to_be_visible()
        assert len(deletes) == 1
        page.reload()
        expect(page.get_by_role("button", name="Other project", exact=True)).to_be_visible()


def test_NFR_PRJ_001_user_text_never_executes(page, live_server):
    payload = '<img src=x onerror="window.injected=true">'
    with live_server() as base:
        page.goto(base)
        create_project(page, title=payload)
        expect(page.locator("#detail-title")).to_have_text(payload)
        expect(page.locator("#detail img")).to_have_count(0)
        expect(page.locator("#project-list img")).to_have_count(0)
        assert page.evaluate("window.injected") is None


def test_FR_PRJ_007_failed_delete_and_escape_keep_project(page, live_server):
    with live_server() as base:
        page.goto(base)
        create_project(page)
        page.get_by_role("button", name="Delete project", exact=True).click()
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).not_to_be_visible()
        expect(page.get_by_role("button", name="Delete project", exact=True)).to_be_focused()
        page.route("**/api/projects/*", lambda route: route.fulfill(status=503,
            content_type="application/json", body='{"error":{"message":"Storage unavailable",'
            '"fields":[]}}') if route.request.method == "DELETE" else route.continue_())
        page.get_by_role("button", name="Delete project", exact=True).click()
        page.get_by_role("button", name="Delete permanently", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Storage unavailable")
        expect(page.locator("#detail-title")).to_have_text("Browser project")
        page.reload()
        expect(page.get_by_role("button", name="Browser project", exact=True)).to_be_visible()
