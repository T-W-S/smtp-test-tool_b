"""Playwright E2E smoke tests for the SMTP Test Tool.

These tests require a running app and a Playwright browser.
Run with: pytest tests/e2e/ --browser chromium
"""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_main_page_loads(page, app_server):
    page.goto(app_server)
    assert page.title() == "SMTP Testing Tool - Send Email"
    assert page.locator("#emailForm").is_visible()


def test_navbar_links_present(page, app_server):
    page.goto(app_server)
    nav = page.locator("nav.navbar")
    assert nav.locator("text=Send Email").is_visible()
    assert nav.locator("text=SMTP Settings").is_visible()
    assert nav.locator("text=Templates").is_visible()
    assert nav.locator("text=Logs").is_visible()


def test_settings_page_loads(page, app_server):
    page.goto(f"{app_server}/settings")
    assert "SMTP Profiles" in page.content()
    assert page.locator("text=Add Profile").is_visible()


def test_templates_page_loads(page, app_server):
    page.goto(f"{app_server}/templates")
    assert "Email Templates" in page.content()
    assert page.locator("text=Add Template").is_visible()


def test_logs_page_loads(page, app_server):
    page.goto(f"{app_server}/logs")
    assert "Email Sending Logs" in page.content()


def test_addresses_page_loads(page, app_server):
    page.goto(f"{app_server}/addresses")
    assert "Email Address Management" in page.content()


def test_advanced_settings_page_loads(page, app_server):
    page.goto(f"{app_server}/advanced_settings")
    assert "Advanced SMTP Settings" in page.content()


def test_dark_theme_applied(page, app_server):
    page.goto(app_server)
    html = page.locator("html")
    assert html.get_attribute("data-bs-theme") == "dark"


def test_health_check_via_browser(page, app_server):
    page.goto(f"{app_server}/health_check")
    content = page.content()
    assert '"status"' in content
    assert '"ok"' in content


def test_add_profile_modal_opens(page, app_server):
    page.goto(f"{app_server}/settings")
    page.locator("text=Add Profile").click()
    modal = page.locator("#addProfileModal")
    modal.wait_for(state="visible")
    assert modal.locator("input[name='name']").is_visible()
    assert modal.locator("input[name='server']").is_visible()


def test_email_form_fields_present(page, app_server):
    page.goto(app_server)
    form = page.locator("#emailForm")
    assert form.locator("#profile").is_visible()
    assert form.locator("#sender").is_visible()
    assert form.locator("#recipients").is_visible()
    assert form.locator("#subject").is_visible()
    assert form.locator("#body").is_visible()
    assert form.locator("#sendButton").is_visible()
