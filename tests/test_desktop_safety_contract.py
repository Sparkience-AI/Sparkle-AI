from pathlib import Path

MAIN_SOURCE = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")


def test_clipboard_is_not_processed_passively() -> None:
    assert ".dataChanged.connect" not in MAIN_SOURCE
    assert ".selectionChanged.connect" not in MAIN_SOURCE
    assert 'keyboard.add_hotkey("ctrl+shift+space", self.analyze_clipboard)' in MAIN_SOURCE


def test_runtime_does_not_mutate_process_global_google_key() -> None:
    assert "os.environ" not in MAIN_SOURCE


def test_runtime_does_not_log_captured_text_or_response_chunks() -> None:
    assert "text[:" not in MAIN_SOURCE
    assert "chunk[:" not in MAIN_SOURCE
