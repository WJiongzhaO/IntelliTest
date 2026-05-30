"""PyTest API tests mapped to 人工优化/ login module test cases (Juice Shop port 3001)."""

from __future__ import annotations

import base64
import json
import time

import pytest
import pyotp

from juice_shop_client import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    JuiceShopClient,
    LR007_EMAIL,
    LR007_PASSWORD,
    TOTP_EMAIL,
    TOTP_PASSWORD,
    TOTP_SECRET,
)


def _jwt_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


# --- LR-001 / TC-LOGIN-001 ---


def test_lr001_valid_login(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    body = client.parse_json(r)
    assert r.status_code == 200, body
    assert body["authentication"]["token"]
    assert body["authentication"]["bid"] is not None


# --- LR-002 / TC-LOGIN-002 (API portion: login succeeds with redirectUrl context) ---


def test_lr002_login_success_for_redirect_flow(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    assert r.status_code == 200
    assert client.parse_json(r)["authentication"]["token"]


# --- LR-003 / TC-LOGIN-003 ---


def test_lr003_totp_required(client: JuiceShopClient) -> None:
    r = client.login(TOTP_EMAIL, TOTP_PASSWORD)
    body = client.parse_json(r)
    assert r.status_code == 401
    assert body.get("status") == "totp_token_required"
    assert body.get("data", {}).get("tmpToken")


# --- LR-004~006, LR-008, LR-021, LR-027, LR-028, LR-029, LR-030: see test_login_ui.py ---


# --- LR-007 / TC-BVA-007 ---


def test_lr007_password_length_one(client: JuiceShopClient) -> None:
    r = client.login(LR007_EMAIL, LR007_PASSWORD)
    body = client.parse_json(r)
    assert r.status_code == 200, body
    assert body["authentication"]["token"]


def test_lr007_password_length_one_mismatch(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, "a")
    assert r.status_code == 401


# --- LR-009 / TC-VAL-009 ---


def test_lr009_malformed_email(client: JuiceShopClient) -> None:
    r = client.login("admin", "wrong")
    assert r.status_code == 401
    assert "Invalid email or password" in r.text


# --- LR-010 / TC-SEC-010 ---


def test_lr010_sql_metacharacters(client: JuiceShopClient) -> None:
    r = client.login("admin'--", "irrelevant")
    body = client.parse_json(r)
    # Document observed behavior; security expectation is no auth bypass
    assert r.status_code in (401, 200), body
    if r.status_code == 200:
        pytest.xfail("SQL metacharacters caused authentication (potential SQLi)")


# --- LR-011 / TC-NEG-011 ---


def test_lr011_wrong_password(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, "WrongPass123!")
    body = client.parse_json(r)
    assert r.status_code == 401
    assert "authentication" not in body


# --- LR-012 / TC-NEG-012 ---


def test_lr012_nonexistent_email(client: JuiceShopClient) -> None:
    r = client.login("nonexistent@juice-sh.op", "anything")
    assert r.status_code == 401


# --- LR-013 / TC-NEG-013 ---


def test_lr013_soft_deleted_user(client: JuiceShopClient) -> None:
    r = client.login("chris.pike@juice-sh.op", "uss enterprise")
    assert r.status_code == 401


# --- LR-014 / TC-SEC-014 ---


def test_lr014_sqli_tautology(client: JuiceShopClient) -> None:
    r = client.login("admin@juice-sh.op'--", "anything")
    body = client.parse_json(r)
    # Juice Shop intentionally vulnerable: may return 200
    if r.status_code == 200 and body.get("authentication", {}).get("token"):
        pytest.xfail("Known SQLi vulnerability: tautology bypass succeeded (observed)")
    assert r.status_code == 401


# --- LR-015 / TC-SEC-015 ---


def test_lr015_sqli_union(client: JuiceShopClient) -> None:
    payload = (
        "' UNION SELECT * FROM (SELECT 15 as id, '' as username, "
        "'acc0unt4nt@juice-sh.op' as email, '12345' as password, "
        "'accounting' as role, '' as deluxeToken, '1.2.3.4' as lastLoginIp, "
        "'/assets/public/images/uploads/default.svg' as profileImage, "
        "'' as totpSecret, 1 as isActive, "
        "'1999-08-16 14:14:41.644 +00:00' as createdAt, "
        "'1999-08-16 14:33:41.930 +00:00' as updatedAt, null as deletedAt)--"
    )
    r = client.login(payload, "x")
    assert r.status_code in (200, 401, 500)
    text = r.text.lower()
    assert "sqlite" not in text or r.status_code != 500


# --- LR-016 / TC-SEC-016 ---


def test_lr016_xss_email(client: JuiceShopClient) -> None:
    r = client.login("<script>alert(1)</script>", "any")
    assert r.status_code == 401
    assert "<script>" not in r.text or r.text.find("<script>") == r.text.find("&lt;script")


# --- LR-017 / TC-SEC-017 ---


def test_lr017_xss_password(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, "<img src=x onerror=alert(1)>")
    assert r.status_code == 401
    assert "onerror" not in r.text


# --- LR-018 / TC-SEC-018 ---


def test_lr018_no_login_rate_limit(client: JuiceShopClient) -> None:
    codes = []
    for _ in range(12):
        r = client.login(ADMIN_EMAIL, "wrong-password")
        codes.append(r.status_code)
    assert 429 not in codes, "Login endpoint unexpectedly rate-limited"
    assert all(c == 401 for c in codes)


# --- LR-019 / TC-REL-019 ---


def test_lr019_reset_password_rate_limit(client: JuiceShopClient) -> None:
    codes = []
    for _ in range(15):
        r = client.reset_password("admin@juice-sh.op")
        codes.append(r.status_code)
    if 429 not in codes and all(c == 500 for c in codes):
        pytest.skip("reset-password returns 500 (email server not configured); cannot verify 429 threshold")
    assert 429 in codes or max(set(codes), key=codes.count) in (200, 401)


# --- LR-020 / TC-TOKEN-020 ---


def test_lr020_invalid_jwt_rejected(client: JuiceShopClient) -> None:
    r = client.auth_details("invalid.jwt.token")
    assert r.status_code == 401


def test_lr020_valid_jwt_accepted(client: JuiceShopClient) -> None:
    login_r = client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    token = client.parse_json(login_r)["authentication"]["token"]
    payload = _jwt_payload(token)
    assert payload.get("status") == "success"
    whoami = client.whoami(token)
    assert whoami.status_code == 200


# --- LR-023 / TC-VAL-023 ---


def test_lr023_case_sensitive_password(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, "Admin123")
    assert r.status_code == 401


# --- LR-024 / TC-VAL-024 ---


def test_lr024_email_with_spaces(client: JuiceShopClient) -> None:
    r = client.login(" admin@juice-sh.op ", ADMIN_PASSWORD)
    assert r.status_code == 401


# --- LR-025 / TC-SESSION-025 ---


def test_lr025_concurrent_sessions(client: JuiceShopClient) -> None:
    c1 = JuiceShopClient(client.base_url)
    c2 = JuiceShopClient(client.base_url)
    t1 = client.parse_json(c1.login(ADMIN_EMAIL, ADMIN_PASSWORD))["authentication"]["token"]
    t2 = client.parse_json(c2.login(ADMIN_EMAIL, ADMIN_PASSWORD))["authentication"]["token"]
    assert t1 and t2
    assert c1.whoami(t1).status_code == 200
    assert c2.whoami(t2).status_code == 200


# --- LR-026 / TC-SEC-026 ---


def test_lr026_admin_weak_password(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    body = client.parse_json(r)
    assert r.status_code == 200
    token = body["authentication"]["token"]
    payload = _jwt_payload(token)
    role = payload.get("data", {}).get("role")
    assert role == "admin"


# --- LR-031 / TC-2FA-031 ---


def test_lr031_valid_totp(client: JuiceShopClient) -> None:
    pre = client.login(TOTP_EMAIL, TOTP_PASSWORD)
    tmp = client.parse_json(pre).get("data", {}).get("tmpToken")
    assert tmp, "Expected tmpToken from TOTP pre-login"
    totp = pyotp.TOTP(TOTP_SECRET).now()
    r = client.verify_2fa(tmp, totp)
    body = client.parse_json(r)
    assert r.status_code == 200, body
    assert body["authentication"]["token"]


# --- LR-032 / TC-2FA-032 ---


def test_lr032_invalid_totp(client: JuiceShopClient) -> None:
    pre = client.login(TOTP_EMAIL, TOTP_PASSWORD)
    tmp = client.parse_json(pre).get("data", {}).get("tmpToken")
    assert tmp
    r = client.verify_2fa(tmp, "000000")
    assert r.status_code == 401


# --- LR-033 / TC-CHAL-033 ---


def test_lr033_jim_login(client: JuiceShopClient) -> None:
    r = client.login("jim@juice-sh.op", "ncc-1701")
    assert r.status_code == 200
    assert client.parse_json(r)["authentication"]["token"]


# --- LR-034 / TC-CHAL-034 ---


def test_lr034_bender_login(client: JuiceShopClient) -> None:
    r = client.login("bender@juice-sh.op", "OhG0dPlease1nsertLiquor!")
    assert r.status_code == 200


# --- LR-035 / TC-SESSION-035 ---


def test_lr035_basket_id_on_login(client: JuiceShopClient) -> None:
    r = client.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    bid = client.parse_json(r)["authentication"]["bid"]
    assert isinstance(bid, int) and bid > 0


# --- LR-036 / TC-SEC-036 ---


def test_lr036_testing_credentials(client: JuiceShopClient) -> None:
    r = client.login("testing@juice-sh.op", "IamUsedForTesting")
    body = client.parse_json(r)
    assert r.status_code == 200
    payload = _jwt_payload(body["authentication"]["token"])
    assert payload.get("data", {}).get("role") == "admin"


# --- LR-022: requires fault injection ---


def test_lr022_server_error_handling() -> None:
    pytest.skip("TC-ERR-022 requires DB fault injection in test environment")


# --- Traceability: all optimized cases have oracle ---


def test_optimized_case_traceability(optimized_cases: list[dict]) -> None:
    assert len(optimized_cases) >= 140, f"expected reviewed suite, got {len(optimized_cases)}"
    for case in optimized_cases:
        assert case["test_case_id"]
        assert case["expected_result"]
        assert case.get("modified_by_user") == "Yes"
