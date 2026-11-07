from __future__ import annotations

import sys
import threading
from os import environ

import pytest

if sys.platform != "win32":
    pytest.skip("Qt desktop threading is validated on Windows CI.", allow_module_level=True)

environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from sparkle_ai.desktop import CaptureBridge, OverlayWidget


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


def test_packaged_entry_point_reports_version_without_starting_qt(capsys) -> None:
    from sparkle_ai.desktop import main

    assert main(["sparkle-ai", "--version"]) == 0
    assert capsys.readouterr().out.strip() == "Sparkle AI 0.1.0"
