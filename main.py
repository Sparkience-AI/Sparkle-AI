import sys
import os
import keyboard
import pyperclip
import win32gui
import win32con
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QSystemTrayIcon, QMenu, QFrame,
                            QGraphicsOpacityEffect, QScrollArea)
from PyQt6.QtWidgets import QLineEdit, QHBoxLayout, QWidgetAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QCursor, QColor, QPixmap, QPainter
import requests
from pathlib import Path
import json
import ollama
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import datetime


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
        if hasattr(self, 'animation'):
            self.animation.start()

    def stop_animation(self):
        if hasattr(self, 'animation'):
            self.animation.stop()
            if hasattr(self, 'opacity_effect'):
                self.opacity_effect.setOpacity(1.0)


# In TextProcessor class, add a stop method
class TextProcessor(QThread):
    result_ready = pyqtSignal(str)
    chunk_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, text, use_gemini=False):
        super().__init__()
        self.text = text
        self.use_gemini = use_gemini
        self.running = True
        os.environ['GOOGLE_API_KEY'] = 'AIzaSyDCsW36FPu38wqYzPRHSxaeHpgvC5NcAWw'
    
    def stop(self):
        self.running = False
        self.wait()  # Wait for the thread to finish
    
    def run(self):
        try:
            if not self.running:
                return
                
            debug_print(f"Starting text processing thread") 
            if self.use_gemini and self._check_internet():
                debug_print("Using Gemini for processing")
                response = self._process_with_gemini()
            else:
                debug_print("Using Ollama for processing")
                response = self._process_with_ollama()
            
            if response and self.running:
                debug_print("Processing completed successfully")
                self.result_ready.emit(response)
            elif self.running:
                self.error_occurred.emit("No response received from AI model")
        except Exception as e:
            if self.running:
                debug_print(f"Error in TextProcessor: {str(e)}")
                self.error_occurred.emit(f"Error processing text: {str(e)}")


    def _check_internet(self):
        try:
            requests.get("http://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            debug_print("No internet connection detected")
            return False

    def _process_with_ollama(self):
        try:
            accumulated_response = ""
            stream = ollama.chat(
                model='llama3.2:3b',
                messages=[{
                    'role': 'user',
                    'content': f"Analyze this text and provide a relevant explanation: {self.text}"
                }],
                stream=True
            )
            
            for chunk in stream:
                chunk_content = chunk['message']['content']
                accumulated_response += chunk_content
                self.chunk_ready.emit(chunk_content)
                debug_print(f"Emitted chunk: {chunk_content[:50]}...")
            
            return accumulated_response
            
        except Exception as e:
            debug_print(f"Ollama error: {str(e)}")
            raise

    def _process_with_gemini(self):
        try:
            debug_print("Initializing Gemini model")
            model = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")
            prompt_template = """
            Analyze the following text and provide a relevant explanation. 
            If the text appears to be from a casual context, provide a conversational response.
            If the text is technical or formal, provide a concise, professional explanation.
            
            Text to analyze: {text}
            """
            prompt = prompt_template.format(text=self.text)
            message = HumanMessage(content=prompt)
            response = model.stream([message])
            result = ''.join([r.content for r in response])
            debug_print(f"Gemini response received: {result[:50]}...")
            return result
        except Exception as e:
            debug_print(f"Gemini error: {str(e)}")
            raise


class StatusIndicatorWidget(QWidget):
    def __init__(self, text, active=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        
        # Create indicator
        self.indicator = QLabel()
        self.indicator.setFixedSize(8, 8)
        self.update_status(active)
        
        # Create text label
        self.text_label = QLabel(text)
        
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
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        self.current_response = ""
        
        # Create timer for reactivation
        self.reactivation_timer = QTimer()
        self.reactivation_timer.setSingleShot(True)
        self.reactivation_timer.timeout.connect(self.reactivate_assistant)

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
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.handle_close)
        header_layout.addWidget(self.close_button)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.layout.addLayout(header_layout)
        
        # Processing indicator
        self.processing_label = AnimatedLabel("Processing...")
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
        self.chat_input.setPlaceholderText("Type your message...")
        self.chat_input.returnPressed.connect(self.send_message)
        
        # Send button
        self.send_button = QPushButton("Send")
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
            if not self.rect().contains(local_pos) and not self.container.rect().contains(local_pos):
                if self.isVisible():
                    self.hide()
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
        if hasattr(self, 'parent') and hasattr(self.parent, 'toggle_assistant'):
            self.parent.toggle_assistant()  # Deactivate
            debug_print("Starting 3-second timer for reactivation")
            self.reactivation_timer.start(3000)  # 3000ms = 3 seconds 

    def reactivate_assistant(self):
        debug_print("Reactivating assistant after delay")
        if hasattr(self, 'parent') and hasattr(self.parent, 'toggle_assistant'):
            if not self.parent.active:  # Only reactivate if currently inactive
                self.parent.toggle_assistant()  # Reactivate

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
    
    def set_response(self, text):
        debug_print("Setting response text")
        self.current_response = text
        self.response_label.setText(text)
    
    def append_chunk(self, chunk):
        debug_print(f"Appending chunk: {chunk[:50]}...")
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
        self.show_processing()
        # Emit a signal to the main window to process the message
        if hasattr(self, 'parent') and hasattr(self.parent, 'process_text'):
            self.parent.process_text(message)

class AIAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.active = True
        self.text_processor = None
        
        # Then create overlay and setup other components
        self.overlay = OverlayWidget()
        self.overlay.parent = self
        self.setup_tray()
        self.setup_clipboard_monitor()

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
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.cleanup_and_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.update_tray_tooltip()



    def setup_clipboard_monitor(self):
        debug_print("Setting up clipboard monitor")
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.handle_clipboard_change)
        self.clipboard.selectionChanged.connect(self.handle_selection_change)
        keyboard.add_hotkey('ctrl+shift+space', self.toggle_assistant)

    def handle_selection_change(self):
        if not self.active:
            return
            
        text = self.clipboard.text(mode=QApplication.clipboard().Selection)
        if text and text.strip():
            debug_print(f"Selection changed: {text[:50]}...")
            self.process_text(text)

    def handle_clipboard_change(self):
        if not self.active:
            return
            
        text = self.clipboard.text()
        if text and text.strip():
            debug_print(f"Clipboard changed: {text[:50]}...")
            self.process_text(text)

    def process_text(self, text):
        self.overlay.show()
        self.overlay.show_processing()
        QTimer.singleShot(100, lambda: self.start_processing(text))

    def start_processing(self, text):
        # Stop any existing text processor
        if self.text_processor is not None:
            self.text_processor.stop()
            self.text_processor.deleteLater()
        
        self.text_processor = TextProcessor(text, use_gemini=True)
        self.text_processor.chunk_ready.connect(self.overlay.append_chunk)
        self.text_processor.result_ready.connect(self.handle_response)
        self.text_processor.error_occurred.connect(self.handle_error)
        self.text_processor.start()

    def handle_error(self, error_message):
        debug_print(f"Error handled: {error_message}")
        self.overlay.show_error(error_message)

    def toggle_assistant(self):
        self.active = not self.active
        debug_print(f"Assistant toggled: {'active' if self.active else 'inactive'}")
        self.status_indicator.update_status(self.active)
        self.update_tray_tooltip()
        if not self.active:
            self.overlay.hide()

    def update_tray_tooltip(self):
        self.tray_icon.setToolTip(f"Sparkience: {'Active' if self.active else 'Inactive'}")


    def handle_response(self, response):
        debug_print("Response received and processing complete")
        self.overlay.hide_processing()
        if response:
            self.overlay.set_response(response)
        
        # Cleanup the text processor after response is handled
        if self.text_processor is not None:
            self.text_processor.stop()
            self.text_processor.deleteLater()
            self.text_processor = None

    def cleanup_and_exit(self):
        debug_print("Cleaning up and exiting")
        # Stop the text processor if it exists
        if self.text_processor is not None:
            self.text_processor.stop()
            self.text_processor.deleteLater()
        
        keyboard.unhook_all()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application-wide stylesheet
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    assistant = AIAssistant()
    debug_print("Application started")
    sys.exit(app.exec())
