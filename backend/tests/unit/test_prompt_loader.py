"""Prompt template loading tests."""

from app.prompts.loader import load_prompt_template, render_user_prompt, prompts_dir


def test_prompts_dir_exists() -> None:
    assert prompts_dir().is_dir()


def test_load_state_transition_template() -> None:
    template = load_prompt_template("state_transition")
    assert "ISTQB" in template["system"]
    rendered = render_user_prompt(
        template,
        raw_text="sample",
        input_fields="[]",
        conditions="[]",
        expected_actions="[]",
    )
    assert "sample" in rendered
