"""PyTest Playwright UI tests for Juice Shop login module (TC-* UI cases)."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from juice_shop_client import ADMIN_EMAIL, ADMIN_PASSWORD
from login_page import (
    EMAIL_ERROR,
    PASSWORD_ERROR,
    assert_no_login_requests,
    dismiss_overlays,
    goto_login,
    password_toggle,
    track_login_requests,
)

pytestmark = pytest.mark.ui


@pytest.fixture
def login_page(page: Page) -> Page:
    goto_login(page)
    return page


# --- TC-VAL-004 / LR-004 ---


def test_tc_val_004_empty_email(login_page: Page) -> None:
    captured, stop = track_login_requests(login_page)
    login_page.locator("#password").fill("anything")
    login_page.locator("#email").click()
    login_page.locator("#password").click()
    expect(login_page.locator("#loginButton")).to_be_disabled()
    errors = login_page.locator("mat-error").all_inner_texts()
    if errors:
        assert any(EMAIL_ERROR.search(e) for e in errors)
    login_page.locator("#loginButton").click(force=True)
    login_page.wait_for_timeout(500)
    stop()
    assert_no_login_requests(captured)


# --- TC-VAL-005 / LR-005 ---


def test_tc_val_005_empty_password(login_page: Page) -> None:
    captured, stop = track_login_requests(login_page)
    login_page.locator("#email").fill("user@juice-sh.op")
    login_page.locator("#password").click()
    login_page.locator("#email").click()
    expect(login_page.locator("#loginButton")).to_be_disabled()
    errors = login_page.locator("mat-error").all_inner_texts()
    assert any(PASSWORD_ERROR.search(e) for e in errors)
    stop()
    assert_no_login_requests(captured)


# --- TC-VAL-006 / LR-006 ---


def test_tc_val_006_both_empty(login_page: Page) -> None:
    captured, stop = track_login_requests(login_page)
    login_page.locator("#email").click()
    login_page.locator("#password").click()
    expect(login_page.locator("#loginButton")).to_be_disabled()
    errors = login_page.locator("mat-error").all_inner_texts()
    assert len(errors) >= 1
    stop()
    assert_no_login_requests(captured)


# --- TC-BVA-008 / LR-008 ---


def test_tc_bva_008_password_empty_boundary(login_page: Page) -> None:
    captured, stop = track_login_requests(login_page)
    login_page.locator("#email").fill("user@juice-sh.op")
    login_page.locator("#password").click()
    login_page.locator("#email").click()
    expect(login_page.locator("#loginButton")).to_be_disabled()
    errors = login_page.locator("mat-error").all_inner_texts()
    assert any(PASSWORD_ERROR.search(e) for e in errors)
    stop()
    assert_no_login_requests(captured)


# --- TC-SESSION-021 / LR-021 ---


def test_tc_session_021_remember_me(login_page: Page) -> None:
    test_email = "remember-me-test@juice-sh.op"
    login_page.locator("#email").fill(test_email)
    login_page.locator("#rememberMe").click()
    login_page.locator("#password").fill("wrong-password")
    login_page.locator("#loginButton").click()
    login_page.wait_for_timeout(1500)
    stored = login_page.evaluate("() => localStorage.getItem('email')")
    assert stored == test_email

    goto_login(login_page)
    prefilled = login_page.locator("#email").input_value()
    assert prefilled == test_email


# --- TC-UI-027 / LR-027 ---


def test_tc_ui_027_password_visibility_toggle(login_page: Page) -> None:
    pwd = login_page.locator("#password")
    pwd.fill("Secret123")
    expect(pwd).to_have_attribute("type", "password")
    password_toggle(login_page).click()
    expect(pwd).to_have_attribute("type", "text")
    password_toggle(login_page).click()
    expect(pwd).to_have_attribute("type", "password")


# --- TC-UI-028 / LR-028 ---


def test_tc_ui_028_enter_submits_login(login_page: Page) -> None:
    captured, stop = track_login_requests(login_page)
    login_page.locator("#email").fill(ADMIN_EMAIL)
    login_page.locator("#password").fill(ADMIN_PASSWORD)
    login_page.locator("#password").press("Enter")
    login_page.wait_for_url(re.compile(r"#/(search|login)"), timeout=15_000)
    login_page.wait_for_timeout(1500)
    stop()
    assert len(captured) == 1
    assert captured[0].method == "POST"
    assert login_page.url.rstrip("/").endswith("#/search") or "search" in login_page.url


# --- TC-OAUTH-029 / LR-029 ---


def test_tc_oauth_029_google_oauth_button(login_page: Page) -> None:
    google = login_page.locator(
        'button:has-text("Google"), a[href*="accounts.google.com"], '
        '[aria-label*="Google"], img[alt*="Google"]'
    )
    if google.count() == 0:
        pytest.skip("Google OAuth button not rendered on this deployment (oauthUnavailable)")
    with login_page.expect_navigation(timeout=15_000):
        google.first.click()
    assert "accounts.google.com" in login_page.url


# --- TC-OAUTH-030 / LR-030 ---


def test_tc_oauth_030_oauth_hidden_when_unavailable(login_page: Page) -> None:
    google = login_page.locator('button:has-text("Google")')
    assert google.count() == 0, "Expected no Google login button on current origin"
    login_page.reload(wait_until="networkidle")
    login_page.wait_for_timeout(1000)
    dismiss_overlays(login_page)
    assert login_page.locator('button:has-text("Google")').count() == 0
