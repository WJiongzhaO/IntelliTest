"""FR 5.0 test oracle synthesis engine."""

__all__ = ["DefaultOracleSynthesizer", "OracleSynthesizer"]


def __getattr__(name: str):
    if name in ("DefaultOracleSynthesizer", "OracleSynthesizer"):
        from app.engines.oracle_synthesizer.synthesizer import DefaultOracleSynthesizer

        return DefaultOracleSynthesizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
