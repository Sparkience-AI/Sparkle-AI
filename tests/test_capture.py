import pytest

from sparkle_ai.capture import (
    ClipboardMonitorState,
    ProviderMode,
    ProviderSelection,
    ProviderSelectionError,
)


def test_clipboard_monitor_is_opt_in_and_deduplicates_changes() -> None:
    monitor = ClipboardMonitorState()

    assert monitor.accept("first") is None
    monitor.enable("first")
    assert monitor.accept("first") is None
    assert monitor.accept("second") == "second"
    assert monitor.accept("second") is None
    monitor.disable()
    assert monitor.accept("third") is None


def test_automatic_monitor_skips_likely_secrets_and_oversized_text() -> None:
    monitor = ClipboardMonitorState()
    monitor.enable()

    assert monitor.accept("token=SPARKLE_TEST_SECRET") is None
    assert "credential" in (monitor.last_rejection or "")

    small_monitor = ClipboardMonitorState(max_characters=5)
    small_monitor.enable()
    assert small_monitor.accept("123456") is None
    assert "oversized" in (small_monitor.last_rejection or "")


def test_provider_selection_requires_key_and_cloud_consent() -> None:
    selection = ProviderSelection()

    assert selection.mode is ProviderMode.OLLAMA
    assert selection.display_name == "Local Ollama"
    with pytest.raises(ProviderSelectionError, match="API key"):
        selection.use_gemini(" ", cloud_consent=True)
    with pytest.raises(ProviderSelectionError, match="consent"):
        selection.use_gemini("session-key", cloud_consent=False)

    selection.use_gemini(" session-key ", cloud_consent=True)
    assert selection.mode is ProviderMode.GEMINI
    assert selection.gemini_api_key == "session-key"
    assert selection.display_name == "Google Gemini (cloud)"

    selection.clear_gemini_key()
    assert selection.mode is ProviderMode.OLLAMA
    assert selection.gemini_api_key is None


@pytest.mark.parametrize(
    ("mode", "model", "expected_name"),
    [
        (ProviderMode.GEMINI, "gemini-custom", "Google Gemini (cloud)"),
        (ProviderMode.OPENAI, "gpt-custom", "OpenAI (cloud)"),
        (ProviderMode.ANTHROPIC, "claude-custom", "Anthropic Claude (cloud)"),
    ],
)
def test_cloud_provider_keys_and_models_are_session_state(
    mode: ProviderMode, model: str, expected_name: str
) -> None:
    selection = ProviderSelection()
    selection.use_cloud(mode, " session-key ", model=model, cloud_consent=True)

    assert selection.mode is mode
    assert selection.api_key_for(mode) == "session-key"
    assert selection.model_for(mode) == model
    assert selection.display_name == expected_name

    selection.clear_key(mode)
    assert selection.mode is ProviderMode.OLLAMA
    assert selection.api_key_for(mode) is None


def test_cloud_provider_rejects_blank_model_and_local_mode() -> None:
    selection = ProviderSelection()
    with pytest.raises(ProviderSelectionError, match="model identifier"):
        selection.use_cloud(ProviderMode.OPENAI, "session-key", model=" ", cloud_consent=True)
    with pytest.raises(ProviderSelectionError, match="supported cloud"):
        selection.use_cloud(ProviderMode.OLLAMA, "session-key", model="local", cloud_consent=True)
