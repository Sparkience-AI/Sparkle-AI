import datetime
import sys
from pathlib import Path
from threading import Event

import keyboard
from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QActionGroup, QColor, QCursor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from sparkle_ai.application import AnalysisService, safe_error_message
from sparkle_ai.capture import ClipboardMonitorState, ProviderMode, ProviderSelection
from sparkle_ai.providers import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
    TextProvider,
)


def debug_print(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[DEBUG {timestamp}] {message}")
    sys.stdout.flush()  # Force immediate output


class AnimatedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_animation()

    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setLoopCount(-1)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.3)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    def start_animation(self):
        if hasattr(self, "animation"):
            self.animation.start()

    def stop_animation(self):
        if hasattr(self, "animation"):
            self.animation.stop()
            if hasattr(self, "opacity_effect"):
                self.opacity_effect.setOpacity(1.0)


class TextProcessor(QThread):
    result_ready = pyqtSignal(str)
    chunk_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, provider: TextProvider):
        super().__init__()
        self.text = text
        self.service = AnalysisService(provider)
        self.cancelled = Event()

    def stop(self):
        self.cancelled.set()
        self.requestInterruption()
        return self.isFinished()

    def run(self):
        try:
            if self.cancelled.is_set():
                return

            debug_print("Starting text processing thread")
            response = self.service.analyze(
                self.text,
                on_chunk=self.chunk_ready.emit,
                cancelled=self.cancelled,
            )

            if response and not self.cancelled.is_set():
                debug_print("Processing completed successfully")
                self.result_ready.emit(response)
            elif not self.cancelled.is_set():
                self.error_occurred.emit("No response received from AI model")
        except Exception as e:
            if not self.cancelled.is_set():
                debug_print(f"Text processing failed: {type(e).__name__}")
                self.error_occurred.emit(safe_error_message(e))


class StatusIndicatorWidget(QWidget):
    def __init__(self, text, active=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        # Create indicator
        self.indicator = QLabel()
        self.indicator.setAccessibleName("Assistant status")
        self.indicator.setFixedSize(8, 8)
        self.update_status(active)

        # Create text label
        self.text_label = QLabel(text)
        self.text_label.setAccessibleName("Assistant toggle label")

        layout.addWidget(self.indicator)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def update_status(self, active):
        # Create a colored circle
        pixmap = QPixmap(8, 8)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if active:
            # Green for active
            painter.setBrush(QColor("#64ffda"))
        else:
            # Gray for inactive
            painter.setBrush(QColor("#6e7681"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 8, 8)
        painter.end()

        self.indicator.setPixmap(pixmap)


class OverlayWidget(QWidget):
    analysis_requested = pyqtSignal(str)
    cancellation_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        self.current_response = ""

        # Install event filter on the application instance
        QApplication.instance().installEventFilter(self)

    def setup_ui(self):
        debug_print("Setting up OverlayWidget UI")
        # Main container
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: rgba(28, 30, 35, 0.95);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
             #closeButton {
                background-color: transparent;
                color: #64ffda;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 16px;
            }
            #closeButton:hover {
                background-color: rgba(100, 255, 218, 0.1);
            }
            #closeButton:pressed {
                background-color: rgba(100, 255, 218, 0.2);
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(100, 255, 218, 0.5);
            }
            QPushButton {
                background-color: #64ffda;
                color: #1c1e23;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9fffea;
            }
            QPushButton:pressed {
                background-color: #4cd9b7;
            }
        """)

        # Set fixed size for the container
        self.container.setFixedSize(500, 400)

        # Header layout for close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch()

        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setAccessibleName("Close assistant overlay")
        self.close_button.setToolTip("Close and cancel the current request")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.handle_close)
        header_layout.addWidget(self.close_button)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.layout.addLayout(header_layout)

        self.provider_label = QLabel("Provider: Local Ollama")
        self.provider_label.setAccessibleName("Active provider")
        self.provider_label.setStyleSheet("color: #a8b3cf; font-size: 12px; padding: 2px;")
        self.layout.addWidget(self.provider_label)

        # Processing indicator
        self.processing_label = AnimatedLabel("Processing...")
        self.processing_label.setAccessibleName("Processing status")
        self.processing_label.setStyleSheet("""
            color: #64ffda;
            font-size: 14px;
            padding: 5px;
        """)
        self.processing_label.hide()

        # Create scroll area for response
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Response container widget
        self.response_container = QWidget()
        self.response_layout = QVBoxLayout(self.response_container)

        # Response text area
        self.response_label = QLabel()
        self.response_label.setAccessibleName("AI response")
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("""
            color: #e4e4e4;
            font-size: 14px;
            line-height: 1.5;
            padding: 10px;
        """)

        self.response_layout.addWidget(self.response_label)
        self.response_layout.addStretch()

        self.scroll_area.setWidget(self.response_container)

        # Error label
        self.error_label = QLabel()
        self.error_label.setAccessibleName("Provider error")
        self.error_label.setStyleSheet("""
            color: #ff6b6b;
            font-size: 14px;
            padding: 5px;
        """)
        self.error_label.hide()

        # Chat input container
        self.chat_container = QWidget()
        chat_layout = QHBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(8)

        # Chat input field
        self.chat_input = QLineEdit()
        self.chat_input.setAccessibleName("Follow-up message")
        self.chat_input.setAccessibleDescription("Enter a follow-up about the current response")
        self.chat_input.setPlaceholderText("Type your message...")
        self.chat_input.returnPressed.connect(self.send_message)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setAccessibleName("Send follow-up")
        self.send_button.setFixedSize(70, 36)
        self.send_button.clicked.connect(self.send_message)

        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.send_button)

        self.layout.addWidget(self.processing_label)
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.error_label)
        self.layout.addWidget(self.chat_container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        main_layout.setContentsMargins(15, 15, 15, 15)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            # Get the mouse position
            mouse_pos = QCursor.pos()
            # Convert global position to local widget coordinates
            local_pos = self.mapFromGlobal(mouse_pos)

            # Check if click is outside both the widget and its container
            if not self.rect().contains(local_pos) and not self.container.rect().contains(
                local_pos
            ):
                if self.isVisible():
                    self.dismiss()
                    return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure the widget is properly sized when shown
        self.adjustSize()
        self.center_on_screen()

    def hideEvent(self, event):
        super().hideEvent(event)
        # Clear any existing error messages when hiding
        self.error_label.hide()
        self.processing_label.hide()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        center_x = (screen.width() - self.width()) // 2
        center_y = (screen.height() - self.height()) // 2
        self.move(center_x, center_y)

    def handle_close(self):
        debug_print("Close button clicked")
        self.dismiss()

    def dismiss(self):
        """Cancel the active lifecycle before hiding the overlay."""

        self.cancellation_requested.emit()
        self.hide()

    def show(self):
        super().show()
        self.center_on_screen()

    def show_processing(self):
        debug_print("Showing processing animation")
        self.error_label.hide()
        self.processing_label.show()
        self.processing_label.start_animation()

    def hide_processing(self):
        debug_print("Hiding processing animation")
        self.processing_label.stop_animation()
        self.processing_label.hide()

    def show_error(self, error_message):
        debug_print(f"Showing error: {error_message}")
        self.hide_processing()
        self.error_label.setText(error_message)
        self.error_label.show()

    def begin_response(self):
        """Start a request with no response or follow-up context from the prior request."""

        self.current_response = ""
        self.response_label.clear()
        self.chat_input.clear()
        self.error_label.clear()
        self.error_label.hide()

    def set_response(self, text):
        debug_print("Setting response text")
        self.current_response = text
        self.response_label.setText(text)

    def set_provider(self, provider_name):
        self.provider_label.setText(f"Provider: {provider_name}")

    def append_chunk(self, chunk):
        debug_print("Appending provider response chunk")
        self.current_response += chunk
        self.response_label.setText(self.current_response)

    def send_message(self):
        message = self.chat_input.text().strip()
        if message:
            self.chat_input.clear()
            # Update the conversation context
            full_context = f"{self.current_response}\n\nUser: {message}"
            # Process the new message with context
            self.process_new_message(full_context)

    def process_new_message(self, message):
        self.analysis_requested.emit(message)


class CaptureBridge(QObject):
    """Move global-hotkey callbacks safely onto the Qt GUI thread."""

    requested = pyqtSignal()


class AIAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.active = True
        self.text_processor = None
        self.pending_text = None
        self.pending_monitor_text = None
        self.accepting_processor_output = False
        self.monitor_state = ClipboardMonitorState()
        self.provider_selection = ProviderSelection()
        self.capture_bridge = CaptureBridge(self)
        self.capture_bridge.requested.connect(self.analyze_clipboard)
        self.start_timer = QTimer(self)
        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.start_pending_processing)
        self.monitor_timer = QTimer(self)
        self.monitor_timer.setSingleShot(True)
        self.monitor_timer.setInterval(750)
        self.monitor_timer.timeout.connect(self.analyze_monitored_clipboard)

        # Then create overlay and setup other components
        self.overlay = OverlayWidget()
        self.overlay.analysis_requested.connect(self.process_text)
        self.overlay.cancellation_requested.connect(self.cancel_processing)
        self.setup_tray()
        self.setup_explicit_capture()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = str(Path(__file__).parent / "icon.png")
        if Path(icon_path).exists():
            self.tray_icon.setIcon(QIcon(icon_path))
            debug_print("Tray icon loaded successfully")
        else:
            debug_print("Warning: icon.png not found in the application directory")

        tray_menu = QMenu()

        # Create status indicator widget
        self.status_indicator = StatusIndicatorWidget("Toggle Assistant", True)
        status_action = QWidgetAction(tray_menu)
        status_action.setDefaultWidget(self.status_indicator)
        tray_menu.addAction(status_action)

        # Connect the entire widget to toggle action
        self.status_indicator.mouseReleaseEvent = lambda e: self.toggle_assistant()

        # Add separator for visual clarity
        tray_menu.addSeparator()

        analyze_action = tray_menu.addAction("Analyze clipboard now")
        analyze_action.triggered.connect(self.analyze_clipboard)

        self.monitor_action = tray_menu.addAction("Monitor clipboard automatically")
        self.monitor_action.setCheckable(True)
        self.monitor_action.setChecked(False)
        self.monitor_action.toggled.connect(self.set_passive_monitoring)

        provider_menu = tray_menu.addMenu("Provider")
        provider_group = QActionGroup(self)
        provider_group.setExclusive(True)
        self.ollama_action = provider_menu.addAction("Local Ollama")
        self.ollama_action.setCheckable(True)
        self.ollama_action.setChecked(True)
        self.ollama_action.triggered.connect(self.select_ollama_provider)
        provider_group.addAction(self.ollama_action)
        self.gemini_action = provider_menu.addAction("Google Gemini (BYOK)")
        self.gemini_action.setCheckable(True)
        self.gemini_action.triggered.connect(self.select_gemini_provider)
        provider_group.addAction(self.gemini_action)
        self.openai_action = provider_menu.addAction("OpenAI (BYOK)")
        self.openai_action.setCheckable(True)
        self.openai_action.triggered.connect(self.select_openai_provider)
        provider_group.addAction(self.openai_action)
        self.anthropic_action = provider_menu.addAction("Anthropic Claude (BYOK)")
        self.anthropic_action.setCheckable(True)
        self.anthropic_action.triggered.connect(self.select_anthropic_provider)
        provider_group.addAction(self.anthropic_action)
        provider_menu.addSeparator()
        clear_gemini_action = provider_menu.addAction("Clear Gemini API key")
        clear_gemini_action.triggered.connect(self.clear_gemini_key)
        clear_openai_action = provider_menu.addAction("Clear OpenAI API key")
        clear_openai_action.triggered.connect(self.clear_openai_key)
        clear_anthropic_action = provider_menu.addAction("Clear Anthropic API key")
        clear_anthropic_action.triggered.connect(self.clear_anthropic_key)

        tray_menu.addSeparator()

        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.cleanup_and_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.update_tray_tooltip()

    def setup_explicit_capture(self):
        debug_print("Setting up explicit clipboard capture")
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.schedule_passive_capture)
        keyboard.add_hotkey("ctrl+shift+space", self.capture_bridge.requested.emit)

    def set_passive_monitoring(self, enabled):
        if enabled:
            provider = self.provider_selection.display_name
            consequence = (
                "Every new clipboard text value will be sent automatically to "
                f"{provider} after a short debounce."
            )
            if self.provider_selection.mode is not ProviderMode.OLLAMA:
                consequence += " This transmits clipboard text to the selected cloud provider."
            response = QMessageBox.question(
                self,
                "Enable automatic clipboard monitoring?",
                consequence + "\n\nEnable monitoring until Sparkle AI exits?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response is not QMessageBox.StandardButton.Yes:
                self.monitor_action.blockSignals(True)
                self.monitor_action.setChecked(False)
                self.monitor_action.blockSignals(False)
                return
            self.monitor_state.enable(self.clipboard.text())
        else:
            self.monitor_state.disable()
            self.monitor_timer.stop()
            self.pending_monitor_text = None
        self.update_tray_tooltip()

    def schedule_passive_capture(self):
        if not self.active or not self.monitor_state.enabled:
            return
        self.pending_monitor_text = self.clipboard.text()
        self.monitor_timer.start()

    def analyze_monitored_clipboard(self):
        text = self.pending_monitor_text
        self.pending_monitor_text = None
        if not self.active or text is None:
            return
        accepted = self.monitor_state.accept(text)
        if accepted is not None:
            debug_print("Opt-in clipboard monitoring requested analysis")
            self.process_text(accepted)
        elif self.monitor_state.last_rejection:
            self.tray_icon.showMessage(
                "Sparkle AI skipped automatic capture",
                self.monitor_state.last_rejection,
                QSystemTrayIcon.MessageIcon.Warning,
                4_000,
            )

    def select_ollama_provider(self):
        changed = self.provider_selection.mode is not ProviderMode.OLLAMA
        self.provider_selection.use_ollama()
        if changed:
            self.invalidate_response_context()
        self.ollama_action.setChecked(True)
        self.overlay.set_provider(self.provider_selection.display_name)
        self.update_tray_tooltip()

    def select_gemini_provider(self):
        self.select_cloud_provider(ProviderMode.GEMINI)

    def select_openai_provider(self):
        self.select_cloud_provider(ProviderMode.OPENAI)

    def select_anthropic_provider(self):
        self.select_cloud_provider(ProviderMode.ANTHROPIC)

    def sync_provider_action(self):
        {
            ProviderMode.OLLAMA: self.ollama_action,
            ProviderMode.GEMINI: self.gemini_action,
            ProviderMode.OPENAI: self.openai_action,
            ProviderMode.ANTHROPIC: self.anthropic_action,
        }[self.provider_selection.mode].setChecked(True)

    def select_cloud_provider(self, mode):
        settings = {
            ProviderMode.GEMINI: ("Google Gemini", "Google API key"),
            ProviderMode.OPENAI: ("OpenAI", "OpenAI API key"),
            ProviderMode.ANTHROPIC: ("Anthropic Claude", "Anthropic API key"),
        }
        provider_name, key_label = settings[mode]
        api_key, accepted = QInputDialog.getText(
            self,
            f"Configure {provider_name}",
            f"{key_label} (kept in memory until cleared or exit):",
            QLineEdit.EchoMode.Password,
        )
        if not accepted or not api_key.strip():
            self.sync_provider_action()
            return
        model, accepted = QInputDialog.getText(
            self,
            f"Choose {provider_name} model",
            "Model identifier:",
            QLineEdit.EchoMode.Normal,
            self.provider_selection.model_for(mode),
        )
        if not accepted or not model.strip():
            self.sync_provider_action()
            return
        monitoring_note = (
            " Automatic monitoring is currently enabled, so future clipboard text will also be "
            "sent automatically."
            if self.monitor_state.enabled
            else ""
        )
        response = QMessageBox.question(
            self,
            f"Use {provider_name}?",
            f"Captured text and follow-up messages will be sent to {provider_name} using this key."
            + monitoring_note
            + f"\n\nUse {provider_name} for this process session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response is not QMessageBox.StandardButton.Yes:
            self.sync_provider_action()
            return
        self.provider_selection.use_cloud(
            mode,
            api_key,
            model=model,
            cloud_consent=True,
        )
        self.invalidate_response_context()
        {
            ProviderMode.GEMINI: self.gemini_action,
            ProviderMode.OPENAI: self.openai_action,
            ProviderMode.ANTHROPIC: self.anthropic_action,
        }[mode].setChecked(True)
        self.overlay.set_provider(self.provider_selection.display_name)
        self.update_tray_tooltip()

    def clear_gemini_key(self):
        self.clear_cloud_key(ProviderMode.GEMINI)

    def clear_openai_key(self):
        self.clear_cloud_key(ProviderMode.OPENAI)

    def clear_anthropic_key(self):
        self.clear_cloud_key(ProviderMode.ANTHROPIC)

    def clear_cloud_key(self, mode):
        was_active = self.provider_selection.mode is mode
        self.provider_selection.clear_key(mode)
        if was_active:
            self.invalidate_response_context()
        self.sync_provider_action()
        self.overlay.set_provider(self.provider_selection.display_name)
        self.update_tray_tooltip()

    def analyze_clipboard(self):
        if not self.active:
            return
        text = self.clipboard.text()
        debug_print("Explicit clipboard analysis requested")
        self.process_text(text)

    def process_text(self, text):
        self.cancel_processing()
        self.overlay.begin_response()
        self.overlay.show()
        self.overlay.show_processing()
        self.pending_text = text
        self.start_timer.start(100)

    def start_pending_processing(self):
        text = self.pending_text
        self.pending_text = None
        if text is not None and self.overlay.isVisible():
            self.start_processing(text)

    def start_processing(self, text):
        # Stop any existing text processor
        if self.text_processor is not None:
            if self.text_processor.isRunning():
                self.text_processor.stop()
                self.overlay.show_error(
                    "The previous local request is still stopping. Please retry shortly."
                )
                return
            self.text_processor.deleteLater()
            self.text_processor = None

        try:
            mode = self.provider_selection.mode
            if mode is not ProviderMode.OLLAMA:
                api_key = self.provider_selection.api_key_for(mode)
                if api_key is None:
                    self.overlay.show_error(
                        "Configure an API key before using this cloud provider."
                    )
                    self.select_ollama_provider()
                    return
                model = self.provider_selection.model_for(mode)
                if mode is ProviderMode.GEMINI:
                    provider: TextProvider = GeminiProvider(api_key, model=model)
                elif mode is ProviderMode.OPENAI:
                    provider = OpenAIProvider(api_key, model=model)
                else:
                    provider = AnthropicProvider(api_key, model=model)
            else:
                provider = OllamaProvider()
        except Exception as error:
            self.overlay.show_error(safe_error_message(error))
            return
        self.overlay.set_provider(self.provider_selection.display_name)
        self.text_processor = TextProcessor(text, provider=provider)
        self.text_processor.chunk_ready.connect(self.handle_chunk)
        self.text_processor.result_ready.connect(self.handle_response)
        self.text_processor.error_occurred.connect(self.handle_error)
        self.text_processor.finished.connect(self.handle_processor_finished)
        self.accepting_processor_output = True
        self.text_processor.start()

    def handle_chunk(self, chunk):
        if self.accepting_processor_output and self.sender() is self.text_processor:
            self.overlay.append_chunk(chunk)

    def handle_error(self, error_message):
        if not self.accepting_processor_output or self.sender() is not self.text_processor:
            return
        debug_print(f"Error handled: {error_message}")
        self.overlay.show_error(error_message)

    def toggle_assistant(self):
        self.active = not self.active
        debug_print(f"Assistant toggled: {'active' if self.active else 'inactive'}")
        self.status_indicator.update_status(self.active)
        self.update_tray_tooltip()
        if not self.active:
            self.monitor_timer.stop()
            self.pending_monitor_text = None
            self.overlay.dismiss()

    def update_tray_tooltip(self):
        monitoring = "monitoring on" if self.monitor_state.enabled else "monitoring off"
        self.tray_icon.setToolTip(
            f"Sparkle AI: {'Active' if self.active else 'Inactive'} · "
            f"{self.provider_selection.display_name} · {monitoring}"
        )

    def handle_response(self, response):
        if not self.accepting_processor_output or self.sender() is not self.text_processor:
            return
        debug_print("Response received and processing complete")
        self.overlay.hide_processing()
        if response:
            self.overlay.set_response(response)

    def handle_processor_finished(self):
        processor = self.sender()
        if processor is self.text_processor:
            self.accepting_processor_output = False
            processor.deleteLater()
            self.text_processor = None

    def cancel_processing(self):
        self.accepting_processor_output = False
        self.start_timer.stop()
        self.monitor_timer.stop()
        self.pending_text = None
        self.pending_monitor_text = None
        if self.text_processor is not None:
            self.text_processor.stop()

    def invalidate_response_context(self):
        """Cancel work and remove follow-up context after a provider identity change."""

        self.cancel_processing()
        self.overlay.begin_response()

    def cleanup_and_exit(self):
        debug_print("Cleaning up and exiting")
        self.start_timer.stop()
        self.monitor_timer.stop()
        self.pending_text = None
        self.pending_monitor_text = None
        if self.text_processor is not None:
            self.text_processor.stop()
            if self.text_processor.isRunning():
                self.overlay.show_error(
                    "The local provider is still stopping. Please retry Exit shortly."
                )
                return
            self.text_processor.deleteLater()
            self.text_processor = None

        keyboard.unhook_all()
        self.provider_selection.clear_all_cloud_keys()
        QApplication.quit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if "--version" in argv:
        print("Sparkle AI 0.1.0")
        return 0

    app = QApplication(list(argv))

    # Set application-wide stylesheet
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)

    assistant = AIAssistant()
    assistant.setObjectName("SparkleAssistant")
    debug_print("Application started")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
