"""
Dialog for adding/editing server configurations
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox
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
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        layout.setSpacing(SPACING_SMALL)
        layout.setContentsMargins(SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL)
        
        self.name_input = QLineEdit()
        self.name_input.setEnabled(self.server_data is None)  # Disable editing name
        layout.addRow("Server Name:", self.name_input)
        
        self.path_input = QLineEdit()
        layout.addRow("Server Path:", self.path_input)
        
        self.command_input = QLineEdit()
        self.command_input.setText("node")
        self.command_input.setPlaceholderText("node, npm, yarn, etc.")
        layout.addRow("Command:", self.command_input)
        
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
            self.command_input.setText(self.server_data.get("command", "node"))
            self.args_input.setText(self.server_data.get("args", ""))
            port = self.server_data.get("port")
            self.port_input.setValue(port if port is not None else 0)
    
    def get_data(self):
        """Get the form data"""
        return {
            "name": self.name_input.text().strip(),
            "path": self.path_input.text().strip(),
            "command": self.command_input.text().strip() or "node",
            "args": self.args_input.text().strip(),
            "port": self.port_input.value() if self.port_input.value() > 0 else None
        }

