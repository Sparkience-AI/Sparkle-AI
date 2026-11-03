"""Pure state for opt-in clipboard monitoring and provider selection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256

LIKELY_SECRET_PATTERN = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?:api[_-]?key|password|secret|token)\s*[:=]|"
    r"AIza[0-9A-Za-z_-]{20,}|sk-[0-9A-Za-z_-]{16,})",
    re.IGNORECASE,
)


class ProviderMode(StrEnum):
    OLLAMA = "ollama"
    GEMINI = "gemini"


class ProviderSelectionError(ValueError):
    """Raised when a cloud provider is selected without consent or credentials."""


@dataclass(slots=True)
class ClipboardMonitorState:
    """Deduplicate clipboard changes after the GUI-owned debounce timer fires."""

    enabled: bool = False
    max_characters: int = 20_000
    _last_digest: str | None = field(default=None, init=False, repr=False)
    last_rejection: str | None = field(default=None, init=False)

    @staticmethod
    def _digest(text: str) -> str:
        return sha256(text.encode("utf-8", errors="replace")).hexdigest()

    def enable(self, current_text: str = "") -> None:
        self.enabled = True
        self._last_digest = self._digest(current_text) if current_text else None

    def disable(self) -> None:
        self.enabled = False

    def accept(self, text: str) -> str | None:
        self.last_rejection = None
        if not self.enabled or not text.strip():
            return None
        digest = self._digest(text)
        if digest == self._last_digest:
            return None
        self._last_digest = digest
        if "\x00" in text or len(text.strip()) > self.max_characters:
            self.last_rejection = "Automatic capture skipped unsupported or oversized content."
            return None
        if LIKELY_SECRET_PATTERN.search(text):
            self.last_rejection = "Automatic capture skipped text that looks like a credential."
            return None
        return text


@dataclass(slots=True)
class ProviderSelection:
    """In-memory provider choice; Gemini credentials are never persisted."""

    mode: ProviderMode = ProviderMode.OLLAMA
    _gemini_api_key: str | None = field(default=None, init=False, repr=False)

    @property
    def display_name(self) -> str:
        return "Local Ollama" if self.mode is ProviderMode.OLLAMA else "Google Gemini (cloud)"

    @property
    def gemini_api_key(self) -> str | None:
        return self._gemini_api_key

    def use_ollama(self) -> None:
        self.mode = ProviderMode.OLLAMA

    def use_gemini(self, api_key: str, *, cloud_consent: bool) -> None:
        normalized = api_key.strip()
        if not normalized:
            raise ProviderSelectionError("A Google API key is required for Gemini.")
        if not cloud_consent:
            raise ProviderSelectionError("Cloud transmission consent is required for Gemini.")
        self._gemini_api_key = normalized
        self.mode = ProviderMode.GEMINI

    def clear_gemini_key(self) -> None:
        self._gemini_api_key = None
        self.mode = ProviderMode.OLLAMA
