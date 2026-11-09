from __future__ import annotations

import sys
import threading
from os import environ

import pytest

if sys.platform != "win32":
    pytest.skip("Qt desktop threading is validated on Windows CI.", allow_module_level=True)

environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from sparkle_ai.capture import ProviderMode
from sparkle_ai.desktop import AIAssistant, CaptureBridge, OverlayWidget


def test_capture_bridge_marshals_hotkey_signal_to_gui_thread() -> None:
    app = QApplication.instance() or QApplication([])
    bridge = CaptureBridge()
    callback_threads: list[int] = []
    bridge.requested.connect(lambda: callback_threads.append(threading.get_ident()))

    worker = threading.Thread(target=bridge.requested.emit)
    worker.start()
    worker.join()
    app.processEvents()

    assert callback_threads == [threading.get_ident()]


def test_overlay_follow_up_and_close_emit_gui_signals() -> None:
    app = QApplication.instance() or QApplication([])
    overlay = OverlayWidget()
    analysis_requests: list[str] = []
    cancellations: list[bool] = []
    overlay.analysis_requested.connect(analysis_requests.append)
    overlay.cancellation_requested.connect(lambda: cancellations.append(True))
    overlay.set_response("Existing answer")
    overlay.chat_input.setText("Explain further")

    overlay.send_message()
    overlay.handle_close()

    assert analysis_requests == ["Existing answer\n\nUser: Explain further"]
    assert cancellations == [True]
    assert app is not None


def test_overlay_controls_have_accessible_names() -> None:
    app = QApplication.instance() or QApplication([])
    overlay = OverlayWidget()
    assert overlay.close_button.accessibleName() == "Close assistant overlay"
    assert overlay.provider_label.accessibleName() == "Active provider"
    assert overlay.response_label.accessibleName() == "AI response"
    assert overlay.error_label.accessibleName() == "Provider error"
    assert overlay.chat_input.accessibleName() == "Follow-up message"
    assert overlay.send_button.accessibleName() == "Send follow-up"
    assert app is not None


def test_overlay_starts_each_request_without_prior_follow_up_context() -> None:
    app = QApplication.instance() or QApplication([])
    overlay = OverlayWidget()
    overlay.set_response("Prior answer")
    overlay.chat_input.setText("Prior follow-up")

    overlay.begin_response()

    assert overlay.current_response == ""
    assert overlay.response_label.text() == ""
    assert overlay.chat_input.text() == ""
    assert app is not None


def test_assistant_invalidates_response_context_before_a_fresh_capture(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr("sparkle_ai.desktop.keyboard.add_hotkey", lambda *_: None)
    assistant = AIAssistant()
    assistant.overlay.set_response("Prior answer")
    assistant.overlay.chat_input.setText("Prior follow-up")

    assistant.process_text("Fresh capture")

    assert assistant.overlay.current_response == ""
    assert assistant.overlay.chat_input.text() == ""
    assert assistant.pending_text == "Fresh capture"
    assert assistant.start_timer.isActive()
    assistant.cancel_processing()
    assistant.overlay.dismiss()
    assistant.tray_icon.hide()
    assert app is not None


def test_provider_change_clears_response_and_follow_up_context(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr("sparkle_ai.desktop.keyboard.add_hotkey", lambda *_: None)
    assistant = AIAssistant()
    assistant.provider_selection.use_cloud(
        ProviderMode.GEMINI,
        "session-key",
        model="gemini-test",
        cloud_consent=True,
    )
    assistant.overlay.set_response("Cloud account answer")
    assistant.overlay.chat_input.setText("Cloud account follow-up")

    assistant.select_ollama_provider()

    assert assistant.provider_selection.mode is ProviderMode.OLLAMA
    assert assistant.overlay.current_response == ""
    assert assistant.overlay.chat_input.text() == ""
    assert assistant.accepting_processor_output is False
    assistant.overlay.dismiss()
    assistant.tray_icon.hide()
    assert app is not None


def test_packaged_entry_point_reports_version_without_starting_qt(capsys) -> None:
    from sparkle_ai.desktop import main

    assert main(["sparkle-ai", "--version"]) == 0
    assert capsys.readouterr().out.strip() == "Sparkle AI 0.1.0"
