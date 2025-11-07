"""
Dialog for application settings
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel,
    QVBoxLayout, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from .styles import get_dialog_style
from .constants import SPACING_NORMAL, SPACING_SMALL
import sys


class ShortcutCaptureWidget(QLineEdit):
    """Widget that captures keyboard shortcuts by key press"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click here and press your shortcut keys...")
        self.shortcut_string = ""
        self.previous_shortcut = ""  # Store previous shortcut when starting capture
        self.capturing = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def mousePressEvent(self, event):
        """Start capturing when widget is clicked"""
        super().mousePressEvent(event)
        self.setFocus()
        self.start_capturing()
    
    def focusInEvent(self, event):
        """Start capturing when widget gains focus"""
        super().focusInEvent(event)
        self.start_capturing()
    
    def focusOutEvent(self, event):
        """Stop capturing when widget loses focus"""
        super().focusOutEvent(event)
        self.stop_capturing()
    
    def start_capturing(self):
        """Start capturing mode"""
        self.capturing = True
        self.previous_shortcut = self.shortcut_string  # Save current shortcut
        self.setText("Press your shortcut keys...")
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #0e639c;
                border: 2px solid #0e639c;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
    
    def stop_capturing(self):
        """Stop capturing mode"""
        self.capturing = False
        if self.shortcut_string:
            self.setText(self.shortcut_string)
        else:
            self.setPlaceholderText("Click here and press your shortcut keys...")
            self.clear()
        # Reset to default style
        self.setStyleSheet("")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Capture key press and build shortcut string"""
        if not self.capturing:
            super().keyPressEvent(event)
            return
        
        # Handle Escape to cancel and restore previous shortcut
        if event.key() == Qt.Key.Key_Escape:
            self.shortcut_string = self.previous_shortcut
            self.stop_capturing()
            return
        
        # Get modifiers
        modifiers = []
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("Ctrl")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("Alt")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("Shift")
        if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("Win")
        
        # Get the key
        key = event.key()
        
        # Ignore if only modifiers are pressed (waiting for actual key)
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, 
                   Qt.Key.Key_Meta, Qt.Key.Key_AltGr):
            return
        
        # Map Qt keys to string representation
        key_str = self._key_to_string(key)
        
        if not key_str:
            # Unknown key, ignore
            return
        
        # Build shortcut string
        if modifiers:
            self.shortcut_string = "+".join(modifiers + [key_str])
        else:
            # No modifiers, just show the key (but this won't be valid for shortcuts)
            self.shortcut_string = key_str
        
        # Update display
        self.setText(self.shortcut_string)
        self.stop_capturing()
    
    def _key_to_string(self, key: int) -> str:
        """Convert Qt key code to string representation"""
        # Function keys
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        
        # Special keys
        special_keys = {
            Qt.Key.Key_Space: "Space",
            Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Escape: "Esc",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Delete: "Delete",
            Qt.Key.Key_Insert: "Insert",
            Qt.Key.Key_Home: "Home",
            Qt.Key.Key_End: "End",
            Qt.Key.Key_PageUp: "PageUp",
            Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Down: "Down",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Right: "Right",
        }
        
        if key in special_keys:
            return special_keys[key]
        
        # Regular character keys
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key).upper()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        
        # Number pad keys
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        
        return None
    
    def get_shortcut(self) -> str:
        """Get the captured shortcut string"""
        return self.shortcut_string
    
    def set_shortcut(self, shortcut: str):
        """Set the shortcut string"""
        self.shortcut_string = shortcut
        if shortcut:
            self.setText(shortcut)
        else:
            self.setText("")


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setStyleSheet(get_dialog_style())
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING_NORMAL)
        layout.setContentsMargins(SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL)
        
        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.setSpacing(SPACING_SMALL)
        
        # Python Command
        self.python_command_input = QLineEdit()
        self.python_command_input.setPlaceholderText("python, python3, py, etc.")
        form_layout.addRow("Python Command:", self.python_command_input)
        
        # Node Command
        self.node_command_input = QLineEdit()
        self.node_command_input.setPlaceholderText("node, nodejs, etc.")
        form_layout.addRow("Node Command:", self.node_command_input)
        
        # Flask Command
        self.flask_command_input = QLineEdit()
        self.flask_command_input.setPlaceholderText("flask, python -m flask, etc.")
        form_layout.addRow("Flask Command:", self.flask_command_input)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Tray Shortcut
        self.tray_shortcut_input = ShortcutCaptureWidget()
        shortcut_hint = QLabel("Click the field above and press your desired key combination")
        shortcut_hint.setStyleSheet("color: #858585; font-size: 11px;")
        form_layout.addRow("Tray Shortcut:", self.tray_shortcut_input)
        form_layout.addRow("", shortcut_hint)
        
        # Platform-specific note
        if sys.platform != "win32":
            platform_note = QLabel("Note: Global shortcuts are only supported on Windows.")
            platform_note.setStyleSheet("color: #f44336; font-size: 11px;")
            form_layout.addRow("", platform_note)
            self.tray_shortcut_input.setEnabled(False)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings into the form"""
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            settings = self.parent_window.server_manager.settings
            self.python_command_input.setText(settings.get("python_command", "python"))
            self.node_command_input.setText(settings.get("node_command", "node"))
            self.flask_command_input.setText(settings.get("flask_command", "flask"))
            self.tray_shortcut_input.set_shortcut(settings.get("tray_shortcut", "Ctrl+Alt+S"))
    
    def validate_shortcut(self, shortcut_str: str) -> bool:
        """Validate shortcut format"""
        if not shortcut_str or not shortcut_str.strip():
            return False
        
        parts = shortcut_str.upper().split('+')
        if len(parts) < 2:
            return False
        
        has_modifier = False
        has_key = False
        
        for part in parts:
            part = part.strip()
            if part in ["CTRL", "CONTROL", "ALT", "SHIFT", "WIN", "WINDOWS"]:
                has_modifier = True
            elif len(part) == 1:
                has_key = True
            elif part in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
                         "SPACE", "ENTER", "TAB", "ESC", "ESCAPE"]:
                has_key = True
            else:
                return False
        
        return has_modifier and has_key
    
    def validate_and_save(self):
        """Validate settings and save if valid"""
        # Validate shortcut if on Windows
        if sys.platform == "win32":
            shortcut = self.tray_shortcut_input.get_shortcut().strip()
            if not shortcut or not self.validate_shortcut(shortcut):
                QMessageBox.warning(
                    self, "Invalid Shortcut",
                    "Please capture a valid shortcut by clicking the field and pressing your desired key combination.\n\n"
                    "The shortcut must include at least one modifier (Ctrl, Alt, Shift, or Win) and a key.\n\n"
                    "Examples:\n"
                    "• Ctrl+Alt+S\n"
                    "• Ctrl+Shift+T\n"
                    "• Alt+F1\n"
                    "• Ctrl+Win+Space"
                )
                return
        
        # Validate commands are not empty
        if not self.python_command_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Python command cannot be empty.")
            return
        
        if not self.node_command_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Node command cannot be empty.")
            return
        
        if not self.flask_command_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Flask command cannot be empty.")
            return
        
        # Save settings
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            server_manager = self.parent_window.server_manager
            old_shortcut = server_manager.settings.get("tray_shortcut", "Ctrl+Alt+S")
            
            # Update settings
            server_manager.settings["python_command"] = self.python_command_input.text().strip()
            server_manager.settings["node_command"] = self.node_command_input.text().strip()
            server_manager.settings["flask_command"] = self.flask_command_input.text().strip()
            
            if sys.platform == "win32":
                new_shortcut = self.tray_shortcut_input.get_shortcut().strip()
                
                # Update shortcut if it changed
                if new_shortcut != old_shortcut:
                    # Unregister old shortcut first
                    self.parent_window.unregister_global_shortcut()
                    
                    # Try to register new shortcut
                    if self.parent_window.register_global_shortcut(new_shortcut):
                        server_manager.settings["tray_shortcut"] = new_shortcut
                        server_manager.save_settings()
                        QMessageBox.information(
                            self, "Settings Saved",
                            f"Settings saved successfully.\n\n"
                            f"New shortcut: {new_shortcut}\n"
                            f"Press the shortcut to toggle the window."
                        )
                    else:
                        # Re-register old shortcut if new one failed
                        self.parent_window.register_global_shortcut(old_shortcut)
                        QMessageBox.warning(
                            self, "Shortcut Registration Failed",
                            f"Failed to register shortcut: {new_shortcut}\n\n"
                            f"The shortcut may be in use by another application.\n"
                            f"Please try a different shortcut.\n\n"
                            f"Other settings have been saved."
                        )
                        return
                else:
                    server_manager.save_settings()
            else:
                server_manager.save_settings()
        
        self.accept()

