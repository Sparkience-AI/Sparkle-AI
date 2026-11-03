"""Provider adapters used by the Sparkle AI application core."""

from collections.abc import Callable, Iterable
from typing import Any, Protocol
from urllib.parse import urlsplit


class TextProvider(Protocol):
    """Minimal streaming capability required by the application."""

    def stream(self, prompt: str) -> Iterable[str]:
        """Yield response text for an application-owned prompt."""


OllamaClientFactory = Callable[..., Any]
GeminiClientFactory = Callable[..., Any]


class EndpointPolicyError(ValueError):
    """Raised when an Ollama endpoint is not an explicit loopback URL."""


def validate_loopback_endpoint(host: str) -> str:
    try:
        parsed = urlsplit(host)
        port = parsed.port
    except ValueError as exc:
        raise EndpointPolicyError("The Ollama endpoint contains an invalid host or port.") from exc
    if parsed.scheme not in {"http", "https"}:
        raise EndpointPolicyError("The Ollama endpoint must use HTTP or HTTPS.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise EndpointPolicyError("The Ollama endpoint must not contain credentials or parameters.")
    if parsed.path not in {"", "/"}:
        raise EndpointPolicyError("The Ollama endpoint must not contain a path.")
    if parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise EndpointPolicyError("Sparkle AI supports loopback Ollama endpoints only.")
    if port is None or not 1 <= port <= 65_535:
        raise EndpointPolicyError("The Ollama endpoint must include a port from 1 to 65535.")
    return host.rstrip("/")


class OllamaProvider:
    """Loopback Ollama adapter with an explicit model and bounded request timeout."""

    def __init__(
        self,
        *,
        model: str = "llama3.2:3b",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 60.0,
        client_factory: OllamaClientFactory | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("An Ollama model is required.")
        host = validate_loopback_endpoint(host)
        if client_factory is None:
            from ollama import Client

            client_factory = Client
        self.model = model
        self._client = client_factory(host=host, timeout=timeout_seconds)

    def stream(self, prompt: str) -> Iterable[str]:
        response = self._client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in response:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield str(content)


class GeminiProvider:
    """Optional cloud adapter configured directly with a session-owned key."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-3.8-flash",
        client_factory: GeminiClientFactory | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Google API key is required for Gemini.")
        if client_factory is None:
            from langchain_google_genai import ChatGoogleGenerativeAI

            client_factory = ChatGoogleGenerativeAI
        self._client = client_factory(model=model, google_api_key=api_key)

    def stream(self, prompt: str) -> Iterable[str]:
        from langchain_core.messages import HumanMessage

        for chunk in self._client.stream([HumanMessage(content=prompt)]):
            content = getattr(chunk, "content", "")
            if content:
                yield str(content)
