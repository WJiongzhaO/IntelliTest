"""Unified LLM client with retries for structured JSON responses."""

from __future__ import annotations

import json
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.exceptions import IntelliTestError
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _settings():
    from app.config import settings

    return settings


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    block = _JSON_BLOCK_RE.search(stripped)
    if block:
        stripped = block.group(1).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise IntelliTestError(f"LLM response is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise IntelliTestError("LLM JSON root must be an object")
    return parsed


class LLMClient:
    """Anthropic / OpenAI / DeepSeek (OpenAI-compatible) wrapper with configurable retries."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
    ) -> None:
        cfg = _settings()
        self.provider = provider or cfg.llm_provider
        self.model = model or cfg.llm_model
        self.max_retries = max_retries if max_retries is not None else cfg.llm_max_retries

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Call the configured provider and parse a JSON object."""
        cfg = _settings()
        temp = (
            temperature
            if temperature is not None
            else cfg.llm_temperature_structured
        )
        logger.info(
            "LLM request provider=%s model=%s temp=%s user_len=%d",
            self.provider,
            self.model,
            temp,
            len(user),
        )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            reraise=True,
        )
        def _call() -> dict[str, Any]:
            raw = self._raw_complete(system, user, temperature=temp)
            result = _extract_json(raw)
            logger.info("LLM response keys=%s", list(result.keys()))
            return result

        try:
            return _call()
        except Exception as exc:
            logger.error("LLM call failed after retries: %s", exc)
            raise IntelliTestError(f"LLM call failed: {exc}") from exc

    def _raw_complete(self, system: str, user: str, *, temperature: float) -> str:
        if self.provider in ("openai", "deepseek"):
            return self._openai_compatible_complete(
                system, user, temperature=temperature, provider=self.provider
            )
        if self.provider == "anthropic":
            return self._anthropic_complete(system, user, temperature=temperature)
        raise IntelliTestError(
            f"Unsupported LLM_PROVIDER '{self.provider}'. "
            "Use 'deepseek', 'openai', or 'anthropic'."
        )

    def _anthropic_complete(self, system: str, user: str, *, temperature: float) -> str:
        cfg = _settings()
        if not cfg.anthropic_api_key:
            raise IntelliTestError("ANTHROPIC_API_KEY is not configured")
        import anthropic

        client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [block.text for block in message.content if hasattr(block, "text")]
        return "".join(parts)

    def _openai_compatible_complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float,
        provider: str,
    ) -> str:
        """Call OpenAI or DeepSeek via the OpenAI Python SDK (compatible API)."""
        cfg = _settings()
        if provider == "deepseek":
            api_key = cfg.deepseek_api_key
            base_url = cfg.deepseek_base_url or "https://api.deepseek.com/v1"
            if not api_key:
                raise IntelliTestError("DEEPSEEK_API_KEY is not configured")
        else:
            api_key = cfg.openai_api_key
            base_url = None
            if not api_key:
                raise IntelliTestError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        client = (
            OpenAI(api_key=api_key, base_url=base_url)
            if base_url
            else OpenAI(api_key=api_key)
        )
        response = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
