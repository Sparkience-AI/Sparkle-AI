"""Framework-independent application services."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Event

from sparkle_ai.prompts import build_analysis_prompt
from sparkle_ai.providers import TextProvider


class InputRejectedError(ValueError):
    """Raised when captured text is outside the supported product contract."""


@dataclass(frozen=True)
class InputPolicy:
    """Limits for text accepted by the desktop application."""

    max_characters: int = 20_000
    max_response_characters: int = 20_000

    def validate(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            raise InputRejectedError("No text was available to analyze.")
        if len(normalized) > self.max_characters:
            raise InputRejectedError(
                f"Captured text exceeds the {self.max_characters:,}-character limit."
            )
        if "\x00" in normalized:
            raise InputRejectedError("Binary or null-delimited content is not supported.")
        return normalized


class AnalysisService:
    """Validate input and stream analysis through an injected provider."""

    def __init__(self, provider: TextProvider, *, policy: InputPolicy | None = None) -> None:
        self._provider = provider
        self._policy = policy or InputPolicy()

    def analyze(
        self,
        text: str,
        *,
        on_chunk: Callable[[str], None] | None = None,
        cancelled: Event | None = None,
    ) -> str:
        validated = self._policy.validate(text)
        cancellation = cancelled or Event()
        if cancellation.is_set():
            return ""

        result: list[str] = []
        response_characters = 0
        for chunk in self._provider.stream(build_analysis_prompt(validated)):
            if cancellation.is_set():
                break
            if not chunk:
                continue
            response_characters += len(chunk)
            if response_characters > self._policy.max_response_characters:
                raise InputRejectedError("Provider output exceeded the configured response limit.")
            result.append(chunk)
            if on_chunk is not None:
                on_chunk(chunk)
        return "".join(result)


def safe_error_message(error: Exception) -> str:
    """Return a stable user message without leaking provider or payload details."""
    if isinstance(error, InputRejectedError):
        return str(error)
    return "The selected provider could not complete the request. Check its local setup and retry."
