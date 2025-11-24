"""
Dialog for creating and editing server stacks
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from .styles import get_dialog_style, get_input_style, get_primary_button_style

class StackDialog(QDialog):
    """Dialog for adding or editing a server stack"""
    
    def __init__(self, parent=None, server_manager=None, stack_name=None):
        super().__init__(parent)
        self.server_manager = server_manager
        self.stack_name = stack_name
        self.server_items = {}  # Map server name to checkbox
        
        self.init_ui()
        
        if stack_name:
            self.load_stack_data()
            
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Add Stack" if not self.stack_name else "Edit Stack")
        self.setMinimumWidth(400)
        self.setStyleSheet(get_dialog_style())
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Stack Name
        name_label = QLabel("Stack Name:")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter stack name")
        self.name_input.setStyleSheet(get_input_style())
        layout.addWidget(self.name_input)
        
        # Server Selection
        servers_label = QLabel("Select Servers:")
        layout.addWidget(servers_label)
        
        self.servers_list = QListWidget()
        self.servers_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #cccccc;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        layout.addWidget(self.servers_list)
        
        # Populate server list
        if self.server_manager:
            servers = self.server_manager.get_all_servers()
            for name in sorted(servers.keys()):
                item = QListWidgetItem(self.servers_list)
                checkbox = QCheckBox(name)
                checkbox.setStyleSheet("color: #cccccc;")
                self.servers_list.setItemWidget(item, checkbox)
                self.server_items[name] = checkbox
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e42;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4e4e52;
            }
        """)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.validate_and_accept)
        save_btn.setStyleSheet(get_primary_button_style())
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def load_stack_data(self):
        """Load existing stack data for editing"""
        self.name_input.setText(self.stack_name)
        self.name_input.setEnabled(False)  # Cannot rename stack for now to keep it simple
        
        stacks = self.server_manager.get_stacks()
        if self.stack_name in stacks:
            selected_servers = stacks[self.stack_name]
            for name, checkbox in self.server_items.items():
                if name in selected_servers:
                    checkbox.setChecked(True)
                    
    def validate_and_accept(self):
        """Validate input and accept dialog"""
        stack_name = self.name_input.text().strip()
        if not stack_name:
            QMessageBox.warning(self, "Validation Error", "Stack name is required.")
            return
            
        selected_servers = []
        for server_name, checkbox in self.server_items.items():
            if checkbox.isChecked():
                selected_servers.append(server_name)
                
        if not selected_servers:
            QMessageBox.warning(self, "Validation Error", "Please select at least one server.")
            return
            
        self.accept()
        
    def get_data(self):
        """Get dialog data"""
        selected_servers = []
        for server_name, checkbox in self.server_items.items():
            if checkbox.isChecked():
                selected_servers.append(server_name)
                
        return {
            "name": self.name_input.text().strip(),
            "servers": selected_servers
        }
