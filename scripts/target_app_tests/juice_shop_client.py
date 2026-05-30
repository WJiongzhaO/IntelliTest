"""Juice Shop login API client for PyTest execution."""

from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = os.environ.get("JUICE_SHOP_URL", "http://localhost:3001").rstrip("/")
LOGIN_PATH = "/rest/user/login"
VERIFY_2FA_PATH = "/rest/2fa/verify"
RESET_PASSWORD_PATH = "/rest/user/reset-password"
WHOAMI_PATH = "/rest/user/whoami"

ADMIN_EMAIL = "admin@juice-sh.op"
ADMIN_PASSWORD = "admin123"
TOTP_EMAIL = "wurstbrot@juice-sh.op"
TOTP_PASSWORD = "EinBelegtesBrotMitSchinkenSCHINKEN!"
TOTP_SECRET = "IFTXE3SPOEYVURT2MRYGI52TKJ4HC3KH"
LR007_EMAIL = "lr007test@juice-sh.op"
LR007_PASSWORD = "a"


class JuiceShopClient:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, email: str, password: str) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{LOGIN_PATH}",
            json={"email": email, "password": password},
            timeout=30,
        )

    def verify_2fa(self, tmp_token: str, totp_token: str) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{VERIFY_2FA_PATH}",
            json={"tmpToken": tmp_token, "totpToken": totp_token},
            timeout=30,
        )

    def reset_password(self, email: str) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{RESET_PASSWORD_PATH}",
            json={"email": email},
            timeout=30,
        )

    def whoami(self, token: str) -> requests.Response:
        return self.session.get(
            f"{self.base_url}{WHOAMI_PATH}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    def auth_details(self, token: str) -> requests.Response:
        return self.session.get(
            f"{self.base_url}/rest/user/authentication-details",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    @staticmethod
    def parse_json(response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}


def health_check(base_url: str = BASE_URL) -> bool:
    try:
        r = requests.get(f"{base_url}/", timeout=5)
        return r.status_code < 500
    except requests.RequestException:
        return False
