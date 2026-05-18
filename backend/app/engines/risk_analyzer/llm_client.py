"""LLM calls for risk assessment (Anthropic / OpenAI / DeepSeek)."""

import json

from app.config import settings
from app.engines.risk_analyzer.prompts import (
    FEW_SHOT_EXAMPLES,
    OUTPUT_SCHEMA_DESCRIPTION,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def call_llm_risk(
    requirement_id: str,
    raw_text: str,
    structured_json: str,
) -> str:
    """Invoke configured LLM for impact/likelihood JSON."""
    provider = settings.llm_provider
    model = settings.llm_model
    temperature = settings.llm_temperature_structured
    logger.info("Risk LLM: provider=%s model=%s req=%s", provider, model, requirement_id)

    if provider == "anthropic":
        return await _call_anthropic(requirement_id, raw_text, structured_json, model, temperature)
    if provider == "openai":
        return await _call_openai(requirement_id, raw_text, structured_json, model, temperature)
    if provider == "deepseek":
        return await _call_openai(
            requirement_id,
            raw_text,
            structured_json,
            model,
            temperature,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    raise ValueError(f"Unknown LLM provider: {provider}")


async def _call_anthropic(
    requirement_id: str,
    raw_text: str,
    structured_json: str,
    model: str,
    temperature: float,
) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system = SYSTEM_PROMPT + "\n\n" + OUTPUT_SCHEMA_DESCRIPTION

    user_messages: list[dict] = []
    for ex in FEW_SHOT_EXAMPLES:
        user_messages.append(
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    requirement_id=ex["requirement_id"],
                    raw_text=ex["raw_text"],
                    structured_json=ex["structured_json"],
                ),
            }
        )
        user_messages.append(
            {
                "role": "assistant",
                "content": json.dumps(ex["output"], ensure_ascii=False),
            }
        )

    user_messages.append(
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                requirement_id=requirement_id,
                raw_text=raw_text,
                structured_json=structured_json,
            ),
        }
    )

    response = await client.messages.create(
        model=model,
        max_tokens=512,
        temperature=temperature,
        system=system,
        messages=user_messages,
    )
    text = response.content[0].text
    logger.info("Anthropic risk response: %d chars", len(text))
    return text


async def _call_openai(
    requirement_id: str,
    raw_text: str,
    structured_json: str,
    model: str,
    temperature: float,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key or settings.openai_api_key, base_url=base_url)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for ex in FEW_SHOT_EXAMPLES:
        messages.append(
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    requirement_id=ex["requirement_id"],
                    raw_text=ex["raw_text"],
                    structured_json=ex["structured_json"],
                ),
            }
        )
        messages.append(
            {"role": "assistant", "content": json.dumps(ex["output"], ensure_ascii=False)}
        )

    messages.append(
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                requirement_id=requirement_id,
                raw_text=raw_text,
                structured_json=structured_json,
            ),
        }
    )
    messages.append({"role": "user", "content": OUTPUT_SCHEMA_DESCRIPTION})

    response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        max_tokens=512,
    )
    text = response.choices[0].message.content or ""
    logger.info("OpenAI risk response: %d chars", len(text))
    return text
