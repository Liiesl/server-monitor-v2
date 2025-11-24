"""
Dialog for adding/editing server configurations
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QComboBox,
    QHBoxLayout, QPushButton, QFileDialog, QWidget, QLabel
)
from .styles import get_dialog_style
from .constants import SPACING_NORMAL, SPACING_SMALL
import os


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
        self.server_type_input.addItems(["Node.js", "Flask", "FlareSolverr"])
        self.server_type_input.currentTextChanged.connect(self.on_server_type_changed)
        layout.addRow("Server Type:", self.server_type_input)
        
        # FlareSolverr type dropdown (Source/Binary)
        self.flaresolverr_type_label = QLabel("FlareSolverr Type:")
        self.flaresolverr_type_input = QComboBox()
        self.flaresolverr_type_input.addItems(["Source", "Binary"])
        self.flaresolverr_type_input.currentTextChanged.connect(self.on_flaresolverr_type_changed)
        layout.addRow(self.flaresolverr_type_label, self.flaresolverr_type_input)
        self.flaresolverr_type_label.setVisible(False)
        self.flaresolverr_type_input.setVisible(False)
        
        # Server Path with browse button
        path_widget = QWidget()
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(SPACING_SMALL)
        self.path_input = QLineEdit()
        path_browse_btn = QPushButton("Browse...")
        path_browse_btn.clicked.connect(self.browse_server_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(path_browse_btn)
        path_widget.setLayout(path_layout)
        layout.addRow("Server Path:", path_widget)
        
        # Command input (unified - changes based on server type)
        self.command_label = QLabel("Command:")
        self.command_input = QLineEdit()
        self.command_input.setText("node")
        self.command_input.setPlaceholderText("node, npm, yarn, etc.")
        layout.addRow(self.command_label, self.command_input)
        
        # Virtual environment path (for Flask only) with browse button
        self.venv_label = QLabel("Virtual Environment (optional):")
        venv_widget = QWidget()
        venv_layout = QHBoxLayout()
        venv_layout.setContentsMargins(0, 0, 0, 0)
        venv_layout.setSpacing(SPACING_SMALL)
        self.venv_input = QLineEdit()
        self.venv_input.setPlaceholderText("e.g., venv, .venv, C:\\projects\\myapp\\venv")
        venv_browse_btn = QPushButton("Browse...")
        venv_browse_btn.clicked.connect(self.browse_venv_path)
        venv_layout.addWidget(self.venv_input)
        venv_layout.addWidget(venv_browse_btn)
        venv_widget.setLayout(venv_layout)
        self.venv_input.setVisible(False)
        self.venv_label.setVisible(False)
        venv_widget.setVisible(False)
        self.venv_widget = venv_widget  # Store reference to toggle visibility
        layout.addRow(self.venv_label, venv_widget)
        
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
            elif server_type == "flaresolverr":
                self.server_type_input.setCurrentText("FlareSolverr")
                # Set FlareSolverr type
                fs_type = self.server_data.get("flaresolverr_type", "source")
                self.flaresolverr_type_input.setCurrentText(fs_type.capitalize())
            else:
                self.server_type_input.setCurrentText("Node.js")
            
            # Set command based on server type
            if server_type == "flask":
                cmd = self.server_data.get("python_command", self.default_python_command)
            elif server_type == "flaresolverr":
                if self.server_data.get("flaresolverr_type") == "source":
                    cmd = self.server_data.get("python_command", self.default_python_command)
                else:
                    cmd = "" # Not used for binary
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
        is_flaresolverr = (server_type == "FlareSolverr")
        
        # Show/hide venv field and label (only for Flask)
        self.venv_label.setVisible(is_flask)
        self.venv_input.setVisible(is_flask)
        self.venv_widget.setVisible(is_flask)
        if not is_flask:
            # Clear venv input when switching to Node.js or FlareSolverr
            self.venv_input.clear()
            
        # Show/hide FlareSolverr type dropdown
        self.flaresolverr_type_label.setVisible(is_flaresolverr)
        self.flaresolverr_type_input.setVisible(is_flaresolverr)
        
        # Update command field label and placeholder based on server type
        if is_flask:
            self.command_label.setText("Python Command:")
            self.command_input.setPlaceholderText("python, py, python3, etc.")
            self.command_input.setVisible(True)
            self.command_label.setVisible(True)
            # Set default Python command if field is empty or still has "node"
            if not self.command_input.text() or self.command_input.text() == "node":
                self.command_input.setText(self.default_python_command)
            self.path_input.setPlaceholderText("e.g., app.py, C:\\projects\\myapp\\app.py")
            self.args_input.setPlaceholderText("e.g., --host 0.0.0.0 --port 5000")
        elif is_flaresolverr:
            # Update based on FlareSolverr type
            self.on_flaresolverr_type_changed(self.flaresolverr_type_input.currentText())
        else:
            # Node.js
            self.command_label.setText("Command:")
            self.command_input.setPlaceholderText("node, npm, yarn, etc.")
            self.command_input.setVisible(True)
            self.command_label.setVisible(True)
            # Set default node command if field is empty or has Python command
            if not self.command_input.text() or self.command_input.text() in ["python", "py", "python3"]:
                self.command_input.setText("node")
            self.path_input.setPlaceholderText("e.g., server.js, C:\\projects\\myapp")
            self.args_input.setPlaceholderText("e.g., start, run dev, --port 3000")

    def on_flaresolverr_type_changed(self, fs_type: str):
        """Handle FlareSolverr type change"""
        if self.server_type_input.currentText() != "FlareSolverr":
            return
            
        if fs_type == "Source":
            self.command_label.setText("Python Command:")
            self.command_input.setPlaceholderText("python, py, python3, etc.")
            self.command_input.setVisible(True)
            self.command_label.setVisible(True)
            # Set default Python command
            if not self.command_input.text() or self.command_input.text() == "node":
                self.command_input.setText(self.default_python_command)
            self.path_input.setPlaceholderText("Path to FlareSolverr git clone directory")
        else:
            # Binary
            self.command_label.setVisible(False)
            self.command_input.setVisible(False)
            self.path_input.setPlaceholderText("Path to FlareSolverr executable")
    
    def get_data(self):
        """Get the form data"""
        server_type_text = self.server_type_input.currentText()
        if server_type_text == "Flask":
            server_type = "flask"
        elif server_type_text == "FlareSolverr":
            server_type = "flaresolverr"
        else:
            server_type = "nodejs"
        
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
        elif server_type == "flaresolverr":
            # For FlareSolverr
            flaresolverr_type = self.flaresolverr_type_input.currentText().lower()
            data["flaresolverr_type"] = flaresolverr_type
            
            if flaresolverr_type == "source":
                data["python_command"] = self.command_input.text().strip() or self.default_python_command
            else:
                data["python_command"] = None
                
            data["command"] = "" # Not used
            data["venv_path"] = "" # Not used
        else:
            # For Node.js, command field contains node/npm/yarn command
            data["command"] = self.command_input.text().strip() or "node"
            data["python_command"] = None  # Not used for Node.js
        
        return data
    
    def browse_server_path(self):
        """Browse for server path (file or directory)"""
        current_path = self.path_input.text().strip()
        
        # Determine if we should use file or directory dialog
        server_type = self.server_type_input.currentText()
        is_flask = (server_type == "Flask")
        is_flaresolverr = (server_type == "FlareSolverr")
        
        if is_flask:
            # Flask: browse for Python file
            start_dir = ""
            if current_path:
                if os.path.isfile(current_path):
                    start_dir = os.path.dirname(current_path)
                elif os.path.isdir(current_path):
                    start_dir = current_path
                else:
                    start_dir = os.path.dirname(current_path) if os.path.dirname(current_path) else ""
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Python File",
                start_dir,
                "Python Files (*.py);;All Files (*)"
            )
            if file_path:
                self.path_input.setText(file_path)
        elif is_flaresolverr:
            # FlareSolverr
            fs_type = self.flaresolverr_type_input.currentText()
            start_dir = ""
            if current_path:
                if os.path.isdir(current_path):
                    start_dir = current_path
                elif os.path.isfile(current_path):
                    start_dir = os.path.dirname(current_path)
                else:
                    start_dir = os.path.dirname(current_path) if os.path.dirname(current_path) else ""
            
            if fs_type == "Source":
                # Source: browse for directory
                dir_path = QFileDialog.getExistingDirectory(
                    self,
                    "Select FlareSolverr Directory",
                    start_dir
                )
                if dir_path:
                    self.path_input.setText(dir_path)
            else:
                # Binary: browse for executable
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select FlareSolverr Executable",
                    start_dir,
                    "Executables (*.exe);;All Files (*)" if os.name == 'nt' else "All Files (*)"
                )
                if file_path:
                    self.path_input.setText(file_path)
        else:
            # Node.js: can be either file or directory
            # Prefer file dialog, but if current path is a directory, use directory dialog
            start_dir = ""
            use_dir_dialog = False
            
            if current_path:
                if os.path.isdir(current_path):
                    start_dir = current_path
                    use_dir_dialog = True
                elif os.path.isfile(current_path):
                    start_dir = os.path.dirname(current_path)
                else:
                    start_dir = os.path.dirname(current_path) if os.path.dirname(current_path) else ""
            
            if use_dir_dialog:
                # Use directory dialog if current path is a directory
                dir_path = QFileDialog.getExistingDirectory(
                    self,
                    "Select Server Directory",
                    start_dir
                )
                if dir_path:
                    self.path_input.setText(dir_path)
            else:
                # Use file dialog for .js files
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select JavaScript File",
                    start_dir,
                    "JavaScript Files (*.js *.mjs *.cjs);;All Files (*)"
                )
                if file_path:
                    self.path_input.setText(file_path)
    
    def browse_venv_path(self):
        """Browse for virtual environment directory"""
        current_path = self.venv_input.text().strip()
        
        # Start from current path if it exists, otherwise from parent of server path
        start_dir = current_path if current_path and os.path.exists(current_path) else ""
        if not start_dir and self.path_input.text().strip():
            server_path = self.path_input.text().strip()
            if os.path.isfile(server_path):
                start_dir = os.path.dirname(server_path)
            elif os.path.isdir(server_path):
                start_dir = server_path
        
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Virtual Environment Directory",
            start_dir
        )
        if dir_path:
            self.venv_input.setText(dir_path)

