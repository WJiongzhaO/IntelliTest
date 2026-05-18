"""LLM provider routing tests (no live API calls)."""

from __future__ import annotations

import pytest

from app.exceptions import IntelliTestError
from app.services.llm_client import LLMClient


def test_unsupported_provider_raises() -> None:
    client = LLMClient(provider="unknown")
    with pytest.raises(IntelliTestError, match="Unsupported LLM_PROVIDER"):
        client._raw_complete("sys", "user", temperature=0.0)


def test_deepseek_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "")
    client = LLMClient(provider="deepseek")
    with pytest.raises(IntelliTestError, match="DEEPSEEK_API_KEY"):
        client._raw_complete("sys", "user", temperature=0.0)
