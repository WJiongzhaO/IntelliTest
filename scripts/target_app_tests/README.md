# Target Application Tests

PyTest suite for executing **人工优化** IntelliTest login module cases against OWASP Juice Shop.

## Prerequisites

- Juice Shop running (default: http://localhost:3001)
- Python packages: `pytest`, `requests`, `pyotp`, `playwright`, `pytest-playwright`

```powershell
$env:JUICE_SHOP_URL = "http://localhost:3001"
pip install pytest requests pyotp playwright pytest-playwright
python -m playwright install chromium
```

Optional: register LR-007 boundary user

```powershell
python scripts/setup_login_preconditions.py
```

## Workflow

```powershell
# 1. Sync final cases to test_cases.json
python scripts/target_app_tests/build_test_cases.py

# 2. Run API regression
python -m pytest scripts/target_app_tests/test_login_api.py -v

# 3. Run UI regression (Playwright)
python -m pytest scripts/target_app_tests/test_login_ui.py -v

# 4. Full suite
python -m pytest scripts/target_app_tests/test_login_api.py scripts/target_app_tests/test_login_ui.py -v
```

## Files

| File | Purpose |
| --- | --- |
| `juice_shop_client.py` | HTTP client for login / 2FA / auth APIs |
| `login_page.py` | Playwright helpers (overlay dismiss, login request tracking) |
| `test_login_api.py` | API tests mapped to TC-* / LR-001 ~ LR-036 |
| `test_login_ui.py` | Playwright UI tests (TC-VAL-004 ~ TC-OAUTH-030) |
| `test_login_flow.py` | Traceability checks |
| `test_cases.json` | Generated from `人工优化/*.csv` (146 cases) |
| `build_test_cases.py` | CSV → JSON sync script |

## Latest results (2026-05-30)

**35 passed, 3 skipped, 1 xfailed** against http://localhost:3001

See `fixtures/juice-shop/JuiceShop登录模块详细测试设计与执行文档(1).md` §11–§12.

## Test categories

- **API (automated)**: login success/failure, 2FA, SQLi/XSS probes, rate limit observation, challenge users
- **UI (Playwright)**: client-side validation, Remember Me, password toggle, Enter submit, OAuth visibility
- **Blocked**: LR-019 (reset-password 500), LR-022 (DB fault injection), TC-OAUTH-029 (no Google button on localhost)
