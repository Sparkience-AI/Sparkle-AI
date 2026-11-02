from pathlib import Path

MAIN_SOURCE = (Path(__file__).parents[1] / "src" / "sparkle_ai" / "desktop.py").read_text(
    encoding="utf-8"
)


def test_clipboard_is_not_processed_passively() -> None:
    assert ".dataChanged.connect" not in MAIN_SOURCE
    assert ".selectionChanged.connect" not in MAIN_SOURCE
    assert (
        'keyboard.add_hotkey("ctrl+shift+space", self.capture_bridge.requested.emit)' in MAIN_SOURCE
    )
    assert "self.capture_bridge.requested.connect(self.analyze_clipboard)" in MAIN_SOURCE


def test_runtime_does_not_mutate_process_global_google_key() -> None:
    assert "os.environ" not in MAIN_SOURCE


def test_runtime_does_not_log_captured_text_or_response_chunks() -> None:
    assert "text[:" not in MAIN_SOURCE
    assert "chunk[:" not in MAIN_SOURCE


def test_close_cancels_deferred_processing_start() -> None:
    assert "self.start_timer.stop()" in MAIN_SOURCE
    assert "self.pending_text = None" in MAIN_SOURCE
