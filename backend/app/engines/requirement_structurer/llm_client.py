"""LLM client abstraction supporting both Anthropic and OpenAI backends."""

import json

from app.config import settings
from app.engines.requirement_structurer.prompts import (
    FEW_SHOT_EXAMPLES,
    OUTPUT_SCHEMA_DESCRIPTION,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def _build_messages(requirement_text: str) -> list[dict]:
    """Build the full message list for the LLM call."""
    user_content = USER_PROMPT_TEMPLATE.format(requirement_text=requirement_text)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["requirement"]})
        messages.append(
            {"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)}
        )

    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "user", "content": OUTPUT_SCHEMA_DESCRIPTION})
    return messages


async def call_llm(requirement_text: str) -> str:
    """Send requirement to LLM and return the raw response text."""
    provider = settings.llm_provider
    model = settings.llm_model
    temperature = settings.llm_temperature_structured

    logger.info("LLM call: provider=%s model=%s", provider, model)

    if provider == "anthropic":
        return await _call_anthropic(requirement_text, model, temperature)
    elif provider == "openai":
        return await _call_openai(requirement_text, model, temperature)
    elif provider == "deepseek":
        return await _call_openai(
            requirement_text,
            model,
            temperature,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


async def _call_anthropic(requirement_text: str, model: str, temperature: float) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system = SYSTEM_PROMPT + "\n\n" + OUTPUT_SCHEMA_DESCRIPTION

    user_messages: list[dict] = []
    for example in FEW_SHOT_EXAMPLES:
        user_messages.append(
            {
                "role": "user",
                "content": example["requirement"],
            }
        )
        user_messages.append(
            {
                "role": "assistant",
                "content": json.dumps(example["output"], ensure_ascii=False),
            }
        )
    user_messages.append(
        {
            "role": "user",
            "content": "Requirement:\n" + requirement_text + "\n\nOutput JSON:",
        }
    )

    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=temperature,
        system=system,
        messages=user_messages,
    )
    text = response.content[0].text
    logger.info("Anthropic response: %d chars", len(text))
    return text


async def _call_openai(
    requirement_text: str,
    model: str,
    temperature: float,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=base_url,
    )
    messages = _build_messages(requirement_text)
    total_chars = sum(len(m.get("content", "")) for m in messages)
    logger.info(
        "OpenAI request: model=%s messages=%d total_chars=%d",
        model,
        len(messages),
        total_chars,
    )

    response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        max_tokens=1024,
    )
    text = response.choices[0].message.content or ""
    logger.info("OpenAI response: %d chars — %s", len(text), text[:200])
    return text
