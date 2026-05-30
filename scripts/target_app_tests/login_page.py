"""Playwright helpers for Juice Shop login page UI tests."""

from __future__ import annotations

import re
from typing import Callable

from playwright.sync_api import Page, Request

from juice_shop_client import BASE_URL

LOGIN_URL = f"{BASE_URL}/#/login"
EMAIL_ERROR = re.compile(r"email|MANDATORY_EMAIL|Please provide an email", re.I)
PASSWORD_ERROR = re.compile(r"password|MANDATORY_PASSWORD|Please provide a password", re.I)


def dismiss_overlays(page: Page) -> None:
    for sel in (
        'button[aria-label="Close Welcome Banner"]',
        'button:has-text("Dismiss")',
    ):
        btn = page.locator(sel)
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            page.wait_for_timeout(300)


def goto_login(page: Page) -> None:
    page.goto(LOGIN_URL, wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(800)
    dismiss_overlays(page)


def track_login_requests(page: Page) -> tuple[list[Request], Callable[[], None]]:
    captured: list[Request] = []

    def on_request(request: Request) -> None:
        if "/rest/user/login" in request.url:
            captured.append(request)

    page.on("request", on_request)

    def stop() -> None:
        page.remove_listener("request", on_request)

    return captured, stop


def password_toggle(page: Page):
    return page.get_by_role("button", name=re.compile(r"display the password|hide the password", re.I))


def assert_no_login_requests(captured: list[Request]) -> None:
    assert not captured, f"Unexpected login API calls: {[r.url for r in captured]}"
