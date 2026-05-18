"""FR 4.0 whitebox state modeling engine."""

from app.engines.whitebox_modeler.mermaid_renderer import ensure_mermaid, render_mermaid

__all__ = [
    "DefaultStateModelGenerator",
    "StateModelGenerator",
    "ensure_mermaid",
    "render_mermaid",
]


def __getattr__(name: str):
    if name in ("DefaultStateModelGenerator", "StateModelGenerator"):
        from app.engines.whitebox_modeler.generator import DefaultStateModelGenerator

        return DefaultStateModelGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
