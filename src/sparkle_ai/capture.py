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
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


PROVIDER_NAMES = {
    ProviderMode.OLLAMA: "Local Ollama",
    ProviderMode.GEMINI: "Google Gemini (cloud)",
    ProviderMode.OPENAI: "OpenAI (cloud)",
    ProviderMode.ANTHROPIC: "Anthropic Claude (cloud)",
}

DEFAULT_MODELS = {
    ProviderMode.GEMINI: "gemini-3.8-flash",
    ProviderMode.OPENAI: "gpt-6-luna",
    ProviderMode.ANTHROPIC: "claude-sonnet-5-5",
}


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
    """In-memory provider choice; cloud credentials are never persisted."""

    mode: ProviderMode = ProviderMode.OLLAMA
    _api_keys: dict[ProviderMode, str] = field(default_factory=dict, init=False, repr=False)
    _models: dict[ProviderMode, str] = field(
        default_factory=lambda: dict(DEFAULT_MODELS), init=False, repr=False
    )

    @property
    def display_name(self) -> str:
        return PROVIDER_NAMES[self.mode]

    @property
    def gemini_api_key(self) -> str | None:
        return self.api_key_for(ProviderMode.GEMINI)

    def api_key_for(self, mode: ProviderMode) -> str | None:
        return self._api_keys.get(mode)

    def model_for(self, mode: ProviderMode) -> str:
        try:
            return self._models[mode]
        except KeyError as exc:
            raise ProviderSelectionError("Local Ollama models are configured separately.") from exc

    def use_ollama(self) -> None:
        self.mode = ProviderMode.OLLAMA

    def use_gemini(self, api_key: str, *, cloud_consent: bool) -> None:
        self.use_cloud(
            ProviderMode.GEMINI,
            api_key,
            model=DEFAULT_MODELS[ProviderMode.GEMINI],
            cloud_consent=cloud_consent,
        )

    def use_cloud(
        self,
        mode: ProviderMode,
        api_key: str,
        *,
        model: str,
        cloud_consent: bool,
    ) -> None:
        if mode not in DEFAULT_MODELS:
            raise ProviderSelectionError("Choose a supported cloud provider.")
        normalized = api_key.strip()
        if not normalized:
            raise ProviderSelectionError(f"An API key is required for {PROVIDER_NAMES[mode]}.")
        normalized_model = model.strip()
        if not normalized_model:
            raise ProviderSelectionError("A model identifier is required.")
        if not cloud_consent:
            raise ProviderSelectionError("Cloud transmission consent is required.")
        self._api_keys[mode] = normalized
        self._models[mode] = normalized_model
        self.mode = mode

    def clear_gemini_key(self) -> None:
        self.clear_key(ProviderMode.GEMINI)

    def clear_key(self, mode: ProviderMode) -> None:
        self._api_keys.pop(mode, None)
        if self.mode is mode:
            self.mode = ProviderMode.OLLAMA

    def clear_all_cloud_keys(self) -> None:
        self._api_keys.clear()
        self.mode = ProviderMode.OLLAMA
