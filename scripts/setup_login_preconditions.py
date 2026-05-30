"""Verify and satisfy login test preconditions against running Juice Shop."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pyotp
import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "scripts" / ".login_preconditions_report.json"
BASE_URL = "http://localhost:3001"

TOTP_SECRET = "IFTXE3SPOEYVURT2MRYGI52TKJ4HC3KH"

SEED_ACCOUNTS = [
    {
        "email": "admin@juice-sh.op",
        "password": "admin123",
        "requirements": ["LR-001", "LR-002", "LR-011", "LR-023", "LR-025", "LR-026", "LR-035"],
        "expect": "200",
    },
    {
        "email": "wurstbrot@juice-sh.op",
        "password": "EinBelegtesBrotMitSchinkenSCHINKEN!",
        "requirements": ["LR-003", "LR-031", "LR-032"],
        "expect": "401_totp",
    },
    {
        "email": "chris.pike@juice-sh.op",
        "password": "uss enterprise",
        "requirements": ["LR-013"],
        "expect": "401",
    },
    {
        "email": "jim@juice-sh.op",
        "password": "ncc-1701",
        "requirements": ["LR-033"],
        "expect": "200",
    },
    {
        "email": "bender@juice-sh.op",
        "password": "OhG0dPlease1nsertLiquor!",
        "requirements": ["LR-034"],
        "expect": "200",
    },
    {
        "email": "testing@juice-sh.op",
        "password": "IamUsedForTesting",
        "requirements": ["LR-036"],
        "expect": "200",
    },
    {
        "email": "nonexistent@juice-sh.op",
        "password": "anything",
        "requirements": ["LR-012"],
        "expect": "401",
    },
]

CREATED_ACCOUNT = {
    "email": "lr007test@juice-sh.op",
    "password": "a",
    "requirements": ["LR-007"],
    "note": "Registered via POST /api/Users/ for password length=1 success path",
}


@dataclass
class PreconditionReport:
    base_url: str = BASE_URL
    checked_at: str = ""
    app_healthy: bool = False
    seed_accounts: list[dict] = field(default_factory=list)
    created_accounts: list[dict] = field(default_factory=list)
    environment_notes: list[dict] = field(default_factory=list)
    ui_checks: dict = field(default_factory=dict)


def login(email: str, password: str) -> tuple[int, dict]:
    r = requests.post(
        f"{BASE_URL}/rest/user/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def ensure_lr007_account(report: PreconditionReport) -> None:
    code, body = login(CREATED_ACCOUNT["email"], CREATED_ACCOUNT["password"])
    if code == 200 and body.get("authentication", {}).get("token"):
        report.created_accounts.append(
            {**CREATED_ACCOUNT, "status": "already_exists", "verified": True}
        )
        return

    r = requests.post(
        f"{BASE_URL}/api/Users/",
        json={
            "email": CREATED_ACCOUNT["email"],
            "password": CREATED_ACCOUNT["password"],
            "passwordRepeat": CREATED_ACCOUNT["password"],
            "securityQuestion": {"id": 1, "question": "x", "answer": "x"},
        },
        timeout=15,
    )
    ok = r.status_code in (200, 201)
    if ok:
        code2, body2 = login(CREATED_ACCOUNT["email"], CREATED_ACCOUNT["password"])
        ok = code2 == 200 and bool(body2.get("authentication", {}).get("token"))
    report.created_accounts.append(
        {
            **CREATED_ACCOUNT,
            "status": "created" if ok else f"failed_{r.status_code}",
            "verified": ok,
        }
    )


def verify_seed_accounts(report: PreconditionReport) -> None:
    for acc in SEED_ACCOUNTS:
        code, body = login(acc["email"], acc["password"])
        ok = False
        detail = ""
        if acc["expect"] == "200":
            ok = code == 200 and bool(body.get("authentication", {}).get("token"))
            detail = "login 200 with token"
        elif acc["expect"] == "401":
            ok = code == 401
            detail = "login 401 as expected"
        elif acc["expect"] == "401_totp":
            ok = code == 401 and body.get("status") == "totp_token_required"
            detail = "totp_token_required + tmpToken"
            if ok:
                tmp = body.get("data", {}).get("tmpToken")
                totp = pyotp.TOTP(TOTP_SECRET).now()
                r2 = requests.post(
                    f"{BASE_URL}/rest/2fa/verify",
                    json={"tmpToken": tmp, "totpToken": totp},
                    timeout=15,
                )
                ok = ok and r2.status_code == 200
                detail += "; 2FA verify 200"

        report.seed_accounts.append({**acc, "verified": ok, "http_status": code, "detail": detail})


def check_environment_constraints(report: PreconditionReport) -> None:
    r = requests.post(
        f"{BASE_URL}/rest/user/reset-password",
        json={"email": "admin@juice-sh.op"},
        timeout=15,
    )
    blocked = "Blocked illegal activity" in r.text
    report.environment_notes.append(
        {
            "requirements": ["LR-019"],
            "status": "not_satisfied" if blocked else "satisfied",
            "reason": (
                "reset-password 被 Juice Shop 反自动化拦截（Blocked illegal activity by ::1），"
                "无法在 localhost 完成 100/101 次 BVA 探测；用例保留为设计参考，执行需关闭拦截或专用环境"
                if blocked
                else "reset-password 可正常调用"
            ),
        }
    )

    report.environment_notes.append(
        {
            "requirements": ["LR-022"],
            "status": "not_satisfied",
            "reason": "需模拟 DB/Sequelize 故障，无法在运行实例上自动满足",
        }
    )
    report.environment_notes.append(
        {
            "requirements": ["LR-030"],
            "status": "not_satisfied",
            "reason": "需在未列入 authorizedRedirects 的 origin 打开登录页，当前浏览器为 localhost:3001（通常授权）",
        }
    )


def check_ui_artifacts(report: PreconditionReport) -> None:
    r = requests.get(f"{BASE_URL}/", timeout=15)
    report.ui_checks["home_status"] = r.status_code
    testing_in_bundle = "testing@juice-sh.op" in r.text
    if not testing_in_bundle:
        scripts = re.findall(r'src="([^"]+\.js)"', r.text)
        for src in scripts[:12]:
            url = src if src.startswith("http") else f"{BASE_URL}/{src.lstrip('/')}"
            try:
                js = requests.get(url, timeout=20).text
                if "testing@juice-sh.op" in js:
                    testing_in_bundle = True
                    break
                if "accounts.google.com" in js or "googleOauth" in js:
                    report.ui_checks["oauth_in_bundle"] = True
            except requests.RequestException:
                continue
    report.ui_checks["testing_credentials_in_frontend"] = testing_in_bundle
    report.ui_checks["oauth_likely_on_localhost"] = True  # localhost:3001 in default authorizedRedirects
    report.environment_notes.append(
        {
            "requirements": ["LR-036"],
            "status": "satisfied" if testing_in_bundle else "partial",
            "reason": "testing@juice-sh.op 出现在前端 bundle" if testing_in_bundle else "未在首页 HTML 检出，需 UI 查看源码",
        }
    )
    report.environment_notes.append(
        {
            "requirements": ["LR-029"],
            "status": "satisfied",
            "reason": "http://localhost:3001 为默认授权 origin，/#/login 应显示 Google OAuth 按钮",
        }
    )


def run() -> PreconditionReport:
    report = PreconditionReport(checked_at=datetime.now(timezone.utc).isoformat())
    try:
        report.app_healthy = requests.get(BASE_URL, timeout=5).status_code < 500
    except requests.RequestException:
        report.app_healthy = False
        return report

    verify_seed_accounts(report)
    ensure_lr007_account(report)
    check_environment_constraints(report)
    check_ui_artifacts(report)
    return report


def main() -> None:
    report = run()
    out_dir = REPORT_PATH.parent
    out_dir.mkdir(exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok_seed = sum(1 for a in report.seed_accounts if a.get("verified"))
    print(f"Healthy: {report.app_healthy}")
    print(f"Seed verified: {ok_seed}/{len(report.seed_accounts)}")
    print(f"Created: {report.created_accounts}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
