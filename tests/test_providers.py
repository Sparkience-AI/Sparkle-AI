import pytest

from sparkle_ai.providers import (
    AnthropicProvider,
    EndpointPolicyError,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)


class FakeOllamaClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return iter(
            [
                {"message": {"content": "first"}},
                {"message": {"content": ""}},
                {"message": {"content": "second"}},
            ]
        )


def test_ollama_provider_uses_loopback_timeout_model_and_streaming() -> None:
    client = FakeOllamaClient()
    factory_calls: list[dict[str, object]] = []

    def factory(**kwargs):
        factory_calls.append(kwargs)
        return client

    provider = OllamaProvider(model="test-model", client_factory=factory)

    assert list(provider.stream("prompt")) == ["first", "second"]
    assert factory_calls == [{"host": "http://127.0.0.1:11434", "timeout": 60.0}]
    assert client.calls[0]["model"] == "test-model"
    assert client.calls[0]["stream"] is True


@pytest.mark.parametrize(
    "host",
    [
        "http://192.168.1.10:11434",
        "https://ollama.example.com:11434",
        "http://user:secret@localhost:11434",
        "http://localhost:not-a-port",
        "http://localhost:70000",
        "file:///tmp/ollama.sock",
    ],
)
def test_ollama_provider_rejects_non_loopback_or_ambiguous_hosts(host: str) -> None:
    with pytest.raises(EndpointPolicyError):
        OllamaProvider(host=host, client_factory=lambda **_: FakeOllamaClient())


def test_gemini_provider_requires_an_explicit_key() -> None:
    with pytest.raises(ValueError, match="Google API key"):
        GeminiProvider(" ", client_factory=lambda **_: object())


def test_gemini_key_is_passed_directly_to_the_client() -> None:
    calls: list[dict[str, object]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        return object()

    GeminiProvider("session-key", client_factory=factory)

    assert calls == [{"model": "gemini-3.8-flash", "google_api_key": "session-key"}]


class FakeOpenAIResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return [
            type(
                "Event",
                (),
                {"type": "response.output_text.delta", "delta": value},
            )()
            for value in ("first", "second")
        ]


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeOpenAIResponses()


def test_openai_uses_responses_stream_without_server_storage() -> None:
    client = FakeOpenAIClient()
    factory_calls: list[dict[str, object]] = []

    def factory(**kwargs):
        factory_calls.append(kwargs)
        return client

    provider = OpenAIProvider("session-key", model="gpt-test", client_factory=factory)

    assert list(provider.stream("prompt")) == ["first", "second"]
    assert factory_calls == [{"api_key": "session-key", "timeout": 60.0}]
    assert client.responses.calls == [
        {"model": "gpt-test", "input": "prompt", "stream": True, "store": False}
    ]


class FakeAnthropicStream:
    text_stream = iter(["first", "second"])

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


class FakeAnthropicMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeAnthropicStream()


class FakeAnthropicClient:
    def __init__(self) -> None:
        self.messages = FakeAnthropicMessages()


def test_anthropic_uses_messages_text_stream() -> None:
    client = FakeAnthropicClient()
    factory_calls: list[dict[str, object]] = []

    def factory(**kwargs):
        factory_calls.append(kwargs)
        return client

    provider = AnthropicProvider("session-key", model="claude-test", client_factory=factory)

    assert list(provider.stream("prompt")) == ["first", "second"]
    assert factory_calls == [{"api_key": "session-key", "timeout": 60.0}]
    assert client.messages.calls == [
        {
            "model": "claude-test",
            "max_tokens": 2_048,
            "messages": [{"role": "user", "content": "prompt"}],
        }
    ]


@pytest.mark.parametrize("provider", [OpenAIProvider, AnthropicProvider])
def test_cloud_providers_require_explicit_keys(provider) -> None:
    with pytest.raises(ValueError, match="API key"):
        provider(" ", client_factory=lambda **_: object())
