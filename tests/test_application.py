from threading import Event

import pytest

from sparkle_ai.application import (
    AnalysisService,
    InputPolicy,
    InputRejectedError,
    safe_error_message,
)


class FakeProvider:
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks
        self.prompts: list[str] = []

    def stream(self, prompt: str):
        self.prompts.append(prompt)
        yield from self.chunks


def test_analysis_streams_chunks_and_returns_complete_response() -> None:
    provider = FakeProvider(["hello", " ", "world"])
    emitted: list[str] = []

    result = AnalysisService(provider).analyze("  captured text  ", on_chunk=emitted.append)

    assert result == "hello world"
    assert emitted == ["hello", " ", "world"]
    assert '{"captured_text": "captured text"}' in provider.prompts[0]


def test_analysis_does_not_call_provider_when_already_cancelled() -> None:
    provider = FakeProvider(["unused"])
    cancelled = Event()
    cancelled.set()

    assert AnalysisService(provider).analyze("text", cancelled=cancelled) == ""
    assert provider.prompts == []


def test_analysis_stops_emitting_after_cooperative_cancellation() -> None:
    provider = FakeProvider(["first", "second"])
    cancelled = Event()
    emitted: list[str] = []

    def cancel_after_first(chunk: str) -> None:
        emitted.append(chunk)
        cancelled.set()

    result = AnalysisService(provider).analyze(
        "text", on_chunk=cancel_after_first, cancelled=cancelled
    )

    assert result == "first"
    assert emitted == ["first"]


@pytest.mark.parametrize("text", ["", "   ", "binary\x00value"])
def test_input_policy_rejects_unsupported_content(text: str) -> None:
    with pytest.raises(InputRejectedError):
        InputPolicy().validate(text)


def test_input_policy_rejects_oversized_content() -> None:
    with pytest.raises(InputRejectedError, match="10-character"):
        InputPolicy(max_characters=10).validate("x" * 11)


def test_safe_error_message_does_not_expose_provider_exception_details() -> None:
    message = safe_error_message(RuntimeError("request failed with secret-key"))

    assert "secret-key" not in message
    assert message == (
        "The selected provider could not complete the request. Check its local setup and retry."
    )
