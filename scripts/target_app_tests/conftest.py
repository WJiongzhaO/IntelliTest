"""PyTest fixtures for Juice Shop target application tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from juice_shop_client import BASE_URL, JuiceShopClient, health_check

CASES_PATH = Path(__file__).parent / "test_cases.json"
OPTIMIZED_DIR = Path(__file__).resolve().parents[2] / "人工优化"


def load_optimized_cases() -> list[dict]:
    if CASES_PATH.exists():
        return json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases: list[dict] = []
    for csv_path in sorted(OPTIMIZED_DIR.glob("LR-*.csv")):
        import csv

        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                cases.append(row)
    return cases


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def require_juice_shop(base_url: str) -> None:
    if not health_check(base_url):
        pytest.skip(f"Juice Shop not reachable at {base_url}")


@pytest.fixture
def client(base_url: str) -> JuiceShopClient:
    return JuiceShopClient(base_url)


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    return {"viewport": {"width": 1280, "height": 720}}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ui: browser UI tests (Playwright)")


@pytest.fixture
def optimized_cases() -> list[dict]:
    return load_optimized_cases()
