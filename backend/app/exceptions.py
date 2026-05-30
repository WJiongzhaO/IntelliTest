"""Application-wide exception hierarchy."""


class IntelliTestError(Exception):
    """Base exception for IntelliTest domain errors."""


class WhiteboxModelError(IntelliTestError):
    """Raised when state machine extraction, validation, or planning fails."""


class OracleSynthesisError(IntelliTestError):
    """Raised when oracle CoT synthesis or validation fails."""


class BlackboxGenerationError(IntelliTestError):
    """Raised when LLM black-box test design or validation fails."""
