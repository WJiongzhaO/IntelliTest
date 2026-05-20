"""Extract state-transition tuples from structured requirements via LLM."""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.exceptions import WhiteboxModelError, IntelliTestError
from app.models.requirement import StructuredRequirement
from app.models.state_machine import StateMachineModel, StateTransitionTuple
from app.prompts.loader import load_prompt_template, render_user_prompt
from app.services.llm_types import LLMClientProtocol
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def extract_state_machine(
    requirement: StructuredRequirement,
    llm: LLMClientProtocol | None = None,
) -> StateMachineModel:
    """Call LLM to extract a state machine model from a requirement."""
    if llm is None:
        from app.services.llm_client import LLMClient

        client = LLMClient()
    else:
        client = llm
    template = load_prompt_template("state_transition")
    user_prompt = render_user_prompt(
        template,
        raw_text=requirement.raw_text,
        input_fields=json.dumps(requirement.input_fields, ensure_ascii=False),
        conditions=json.dumps(requirement.conditions, ensure_ascii=False),
        expected_actions=json.dumps(requirement.expected_actions, ensure_ascii=False),
    )

    try:
        payload = client.complete_json(
            template["system"],
            user_prompt,
            temperature=0.0,
        )
    except IntelliTestError as exc:
        raise WhiteboxModelError(f"State extraction LLM failed: {exc}") from exc

    logger.info(
        "Extracted state machine states=%d transitions=%d",
        len(payload.get("states", [])),
        len(payload.get("transitions", [])),
    )
    return _parse_payload(payload, requirement.id)


def _parse_payload(payload: dict, requirement_id: str) -> StateMachineModel:
    try:
        transitions = [
            StateTransitionTuple.model_validate(item)
            for item in payload.get("transitions", [])
        ]
        model = StateMachineModel(
            initial_state=payload["initial_state"],
            states=payload.get("states", []),
            transitions=transitions,
            mermaid_diagram=payload.get("mermaid_diagram", ""),
            requirement_id=requirement_id,
        )
        return model
    except (KeyError, ValidationError) as exc:
        raise WhiteboxModelError(f"Invalid state machine JSON schema: {exc}") from exc
