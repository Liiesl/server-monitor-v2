"""
Dialog for adding/editing server configurations
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QComboBox
)
from .styles import get_dialog_style
from .constants import SPACING_NORMAL, SPACING_SMALL


class ServerDialog(QDialog):
    """Dialog for adding/editing server configurations"""
    
    def __init__(self, parent=None, server_data=None):
        super().__init__(parent)
        self.server_data = server_data
        self.setWindowTitle("Add Server" if server_data is None else "Edit Server")
        self.setMinimumWidth(400)
        self.setStyleSheet(get_dialog_style())
        # Get default Python command from parent's server_manager if available
        self.default_python_command = "python"
        if parent and hasattr(parent, 'server_manager'):
            self.default_python_command = parent.server_manager.settings.get("python_command", "python")
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        layout.setSpacing(SPACING_SMALL)
        layout.setContentsMargins(SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL)
        
        self.name_input = QLineEdit()
        self.name_input.setEnabled(self.server_data is None)  # Disable editing name
        layout.addRow("Server Name:", self.name_input)
        
        # Server type dropdown
        self.server_type_input = QComboBox()
        self.server_type_input.addItems(["Node.js", "Flask"])
        self.server_type_input.currentTextChanged.connect(self.on_server_type_changed)
        layout.addRow("Server Type:", self.server_type_input)
        
        self.path_input = QLineEdit()
        layout.addRow("Server Path:", self.path_input)
        
        # Command input (unified - changes based on server type)
        from PySide6.QtWidgets import QLabel
        self.command_label = QLabel("Command:")
        self.command_input = QLineEdit()
        self.command_input.setText("node")
        self.command_input.setPlaceholderText("node, npm, yarn, etc.")
        layout.addRow(self.command_label, self.command_input)
        
        # Virtual environment path (for Flask only)
        from PySide6.QtWidgets import QLabel
        self.venv_label = QLabel("Virtual Environment (optional):")
        self.venv_input = QLineEdit()
        self.venv_input.setPlaceholderText("e.g., venv, .venv, C:\\projects\\myapp\\venv")
        self.venv_input.setVisible(False)
        self.venv_label.setVisible(False)
        layout.addRow(self.venv_label, self.venv_input)
        
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("e.g., start, run dev, --port 3000")
        layout.addRow("Arguments:", self.args_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(0, 65535)
        self.port_input.setValue(0)
        self.port_input.setSpecialValueText("Auto")
        layout.addRow("Port (optional):", self.port_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
        # Populate fields if editing
        if self.server_data:
            self.name_input.setText(self.server_data.get("name", ""))
            self.path_input.setText(self.server_data.get("path", ""))
            
            # Set server type
            server_type = self.server_data.get("server_type", "nodejs")
            if server_type == "flask":
                self.server_type_input.setCurrentText("Flask")
            else:
                self.server_type_input.setCurrentText("Node.js")
            
            # Set command based on server type
            server_type = self.server_data.get("server_type", "nodejs")
            if server_type == "flask":
                cmd = self.server_data.get("python_command", self.default_python_command)
            else:
                cmd = self.server_data.get("command", "node")
            self.command_input.setText(cmd)
            
            # Set venv if present
            venv_path = self.server_data.get("venv_path", "")
            self.venv_input.setText(venv_path)
            
            self.args_input.setText(self.server_data.get("args", ""))
            port = self.server_data.get("port")
            self.port_input.setValue(port if port is not None else 0)
        else:
            # Set default server type to Node.js
            self.server_type_input.setCurrentText("Node.js")
        
        # Update UI based on initial server type
        self.on_server_type_changed(self.server_type_input.currentText())
    
    def on_server_type_changed(self, server_type: str):
        """Handle server type change - show/hide relevant fields and update labels"""
        is_flask = (server_type == "Flask")
        
        # Show/hide venv field and label (only for Flask)
        self.venv_label.setVisible(is_flask)
        self.venv_input.setVisible(is_flask)
        if not is_flask:
            # Clear venv input when switching to Node.js
            self.venv_input.clear()
        
        # Update command field label and placeholder based on server type
        if is_flask:
            self.command_label.setText("Python Command:")
            self.command_input.setPlaceholderText("python, py, python3, etc.")
            # Set default Python command if field is empty or still has "node"
            if not self.command_input.text() or self.command_input.text() == "node":
                self.command_input.setText(self.default_python_command)
            self.path_input.setPlaceholderText("e.g., app.py, C:\\projects\\myapp\\app.py")
            self.args_input.setPlaceholderText("e.g., --host 0.0.0.0 --port 5000")
        else:
            self.command_label.setText("Command:")
            self.command_input.setPlaceholderText("node, npm, yarn, etc.")
            # Set default node command if field is empty or has Python command
            if not self.command_input.text() or self.command_input.text() in ["python", "py", "python3"]:
                self.command_input.setText("node")
            self.path_input.setPlaceholderText("e.g., server.js, C:\\projects\\myapp")
            self.args_input.setPlaceholderText("e.g., start, run dev, --port 3000")
    
    def get_data(self):
        """Get the form data"""
        server_type = "flask" if self.server_type_input.currentText() == "Flask" else "nodejs"
        
        data = {
            "name": self.name_input.text().strip(),
            "path": self.path_input.text().strip(),
            "args": self.args_input.text().strip(),
            "port": self.port_input.value() if self.port_input.value() > 0 else None,
            "server_type": server_type
        }
        
        if server_type == "flask":
            # For Flask, command field contains Python command
            data["python_command"] = self.command_input.text().strip() or self.default_python_command
            data["command"] = ""  # Not used for Flask
            # Get venv path (always include, even if empty, to allow clearing)
            venv_path = self.venv_input.text().strip()
            data["venv_path"] = venv_path if venv_path else ""
        else:
            # For Node.js, command field contains node/npm/yarn command
            data["command"] = self.command_input.text().strip() or "node"
            data["python_command"] = None  # Not used for Node.js
        
        return data

