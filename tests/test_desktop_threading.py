from __future__ import annotations

import sys
import threading

import pytest

if sys.platform != "win32":
    pytest.skip("Qt desktop threading is validated on Windows CI.", allow_module_level=True)

from PyQt6.QtCore import QCoreApplication

from sparkle_ai.desktop import CaptureBridge


def test_capture_bridge_marshals_hotkey_signal_to_gui_thread() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    bridge = CaptureBridge()
    callback_threads: list[int] = []
    bridge.requested.connect(lambda: callback_threads.append(threading.get_ident()))

    worker = threading.Thread(target=bridge.requested.emit)
    worker.start()
    worker.join()
    app.processEvents()

    assert callback_threads == [threading.get_ident()]


def test_packaged_entry_point_reports_version_without_starting_qt(capsys) -> None:
    from sparkle_ai.desktop import main

    assert main(["sparkle-ai", "--version"]) == 0
    assert capsys.readouterr().out.strip() == "Sparkle AI 0.1.0"
