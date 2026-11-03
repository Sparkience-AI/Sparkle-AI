from pathlib import Path

MAIN_SOURCE = (Path(__file__).parents[1] / "src" / "sparkle_ai" / "desktop.py").read_text(
    encoding="utf-8"
)


def test_clipboard_monitoring_is_connected_but_opt_in() -> None:
    assert "self.clipboard.dataChanged.connect(self.schedule_passive_capture)" in MAIN_SOURCE
    assert "self.monitor_action.setChecked(False)" in MAIN_SOURCE
    assert "if not self.active or not self.monitor_state.enabled" in MAIN_SOURCE
    assert ".selectionChanged.connect" not in MAIN_SOURCE
    assert (
        'keyboard.add_hotkey("ctrl+shift+space", self.capture_bridge.requested.emit)' in MAIN_SOURCE
    )
    assert "self.capture_bridge.requested.connect(self.analyze_clipboard)" in MAIN_SOURCE


def test_overlay_follow_up_and_close_use_gui_thread_signals() -> None:
    assert "analysis_requested = pyqtSignal(str)" in MAIN_SOURCE
    assert "cancellation_requested = pyqtSignal()" in MAIN_SOURCE
    assert "self.analysis_requested.emit(message)" in MAIN_SOURCE
    assert "self.cancellation_requested.emit()" in MAIN_SOURCE


def test_runtime_does_not_mutate_process_global_google_key() -> None:
    assert "os.environ" not in MAIN_SOURCE


def test_runtime_does_not_log_captured_text_or_response_chunks() -> None:
    assert "text[:" not in MAIN_SOURCE
    assert "chunk[:" not in MAIN_SOURCE


def test_close_cancels_deferred_processing_start() -> None:
    assert "self.start_timer.stop()" in MAIN_SOURCE
    assert "self.pending_text = None" in MAIN_SOURCE
