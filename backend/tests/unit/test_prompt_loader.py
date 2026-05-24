"""Prompt template loading tests."""

from app.prompts.loader import load_prompt_template, render_user_prompt, prompts_dir
from app.utils.prompt_paths import resolve_prompt_file, resolve_prompts_dir


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


def test_resolve_prompts_dir_supports_docker_depth(tmp_path) -> None:
    shared_prompts = tmp_path / "app" / "prompts"
    shared_prompts.mkdir(parents=True)
    template_file = shared_prompts / "state_transition.txt"
    template_file.write_text("template", encoding="utf-8")

    docker_loader_path = tmp_path / "app" / "app" / "prompts" / "loader.py"

    assert resolve_prompts_dir(from_file=docker_loader_path) == shared_prompts
    assert (
        resolve_prompt_file("state_transition.txt", from_file=docker_loader_path)
        == template_file
    )
