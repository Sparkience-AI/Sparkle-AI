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
    assert "self.dismiss()" in MAIN_SOURCE
    assert "self.overlay.dismiss()" in MAIN_SOURCE
    assert "self.overlay.hide()" not in MAIN_SOURCE


def test_runtime_does_not_mutate_process_global_cloud_keys() -> None:
    assert "os.environ" not in MAIN_SOURCE


def test_cloud_providers_are_explicit_byok_choices() -> None:
    assert 'provider_menu.addAction("Google Gemini (BYOK)")' in MAIN_SOURCE
    assert 'provider_menu.addAction("OpenAI (BYOK)")' in MAIN_SOURCE
    assert 'provider_menu.addAction("Anthropic Claude (BYOK)")' in MAIN_SOURCE
    assert "self.provider_selection.use_cloud(" in MAIN_SOURCE
    assert "cloud_consent=True" in MAIN_SOURCE


def test_runtime_does_not_log_captured_text_or_response_chunks() -> None:
    assert "text[:" not in MAIN_SOURCE
    assert "chunk[:" not in MAIN_SOURCE


def test_close_cancels_deferred_processing_start() -> None:
    assert "self.start_timer.stop()" in MAIN_SOURCE
    assert "self.pending_text = None" in MAIN_SOURCE


def test_fresh_requests_and_provider_changes_invalidate_old_output() -> None:
    assert "self.overlay.begin_response()" in MAIN_SOURCE
    assert "self.invalidate_response_context()" in MAIN_SOURCE
    assert "self.accepting_processor_output = False" in MAIN_SOURCE
    assert "self.text_processor.chunk_ready.connect(self.handle_chunk)" in MAIN_SOURCE
