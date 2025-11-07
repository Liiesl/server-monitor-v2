"""
Sidebar navigation widget with collapsible functionality
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QPalette, QColor
from typing import Dict
from .constants import SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH, BUTTON_HEIGHT_LARGE, BUTTON_HEIGHT_STANDARD
from .styles import get_sidebar_style


class SidebarWidget(QWidget):
    """Sidebar navigation widget with collapsible functionality"""
    
    item_selected = Signal(str)  # Emits "dashboard" or server name
    context_action = Signal(str, str)  # Emits (action, server_name) - action: "start", "stop", "restart", "edit", "remove"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed = False
        self.expanded_width = SIDEBAR_EXPANDED_WIDTH
        self.collapsed_width = SIDEBAR_COLLAPSED_WIDTH
        self.selected_item = "dashboard"
        self.server_buttons: Dict[str, QPushButton] = {}
        self.server_statuses: Dict[str, str] = {}  # Track server statuses
        self.init_ui()
    
    def init_ui(self):
        """Initialize the sidebar UI"""
        self.setStyleSheet(get_sidebar_style())
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        self.setLayout(layout)
        
        # Toggle button for collapse/expand
        self.toggle_btn = QPushButton("☰" if not self.collapsed else "→")
        self.toggle_btn.setFixedHeight(BUTTON_HEIGHT_STANDARD)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.toggle_btn)
        
        # Dashboard button
        self.dashboard_btn = QPushButton("Dashboard")
        self.dashboard_btn.setFixedHeight(BUTTON_HEIGHT_LARGE)
        self.dashboard_btn.clicked.connect(lambda: self.select_item("dashboard"))
        layout.addWidget(self.dashboard_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Server list label (hidden when collapsed)
        self.servers_label = QLabel("Servers")
        layout.addWidget(self.servers_label)
        
        # Server buttons container
        self.server_container = QWidget()
        self.server_layout = QVBoxLayout()
        self.server_layout.setContentsMargins(0, 0, 0, 0)
        self.server_layout.setSpacing(3)
        self.server_container.setLayout(self.server_layout)
        layout.addWidget(self.server_container)
        
        # Stretch to push items to top
        layout.addStretch()
        
        # Set initial width
        self.setFixedWidth(self.expanded_width)
        
        # Highlight dashboard initially
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True)
    
    def toggle_collapse(self):
        """Toggle sidebar collapsed/expanded state"""
        self.collapsed = not self.collapsed
        
        if self.collapsed:
            self.setFixedWidth(self.collapsed_width)
            self.toggle_btn.setText("→")
            # Hide text, show only icons or first letter
            self.dashboard_btn.setText("D")
            self.servers_label.hide()
            for name, btn in self.server_buttons.items():
                # Show first letter or icon
                original_text = btn.property("original_text")
                if original_text:
                    btn.setText(original_text[0] if len(original_text) > 0 else "S")
                # Reapply color to maintain status indication
                self.update_server_button_color(name)
        else:
            self.setFixedWidth(self.expanded_width)
            self.toggle_btn.setText("☰")
            # Show full text
            self.dashboard_btn.setText("Dashboard")
            self.servers_label.show()
            for name, btn in self.server_buttons.items():
                original_text = btn.property("original_text")
                if original_text:
                    btn.setText(original_text)
                # Reapply color to maintain status indication
                self.update_server_button_color(name)
    
    def update_server_list(self, servers: Dict):
        """Update the server list in sidebar"""
        # Get current statuses before removing buttons
        parent = self.parent()
        if hasattr(parent, 'server_manager'):
            for name in servers.keys():
                self.server_statuses[name] = parent.server_manager.get_server_status(name)
        
        # Remove old buttons
        for btn in list(self.server_buttons.values()):
            self.server_layout.removeWidget(btn)
            btn.deleteLater()
        self.server_buttons.clear()
        
        # Add new server buttons
        for name in servers.keys():
            btn = QPushButton(name)
            btn.setProperty("original_text", name)
            btn.setFixedHeight(BUTTON_HEIGHT_STANDARD)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.select_item(n))
            # Enable context menu
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, n=name: self.show_context_menu(pos, n, btn))
            self.server_buttons[name] = btn
            self.server_layout.addWidget(btn)
            # Update button color based on status
            self.update_server_button_color(name)
        
        # Update collapsed state if needed
        if self.collapsed:
            for btn in self.server_buttons.values():
                original_text = btn.property("original_text")
                if original_text:
                    btn.setText(original_text[0] if len(original_text) > 0 else "S")
    
    def update_server_status(self, server_name: str, status: str):
        """Update server status and button color"""
        self.server_statuses[server_name] = status
        self.update_server_button_color(server_name)
    
    def update_server_button_color(self, server_name: str):
        """Update button text color based on server status"""
        if server_name not in self.server_buttons:
            return
        
        btn = self.server_buttons[server_name]
        status = self.server_statuses.get(server_name, "stopped")
        
        # Set color based on status
        if status == "running":
            text_color = "#4caf50"  # Green for running
        else:
            text_color = "#cccccc"  # Default gray for stopped
        
        # Use palette to set text color - this overrides stylesheet
        palette = btn.palette()
        color = QColor(text_color)
        palette.setColor(QPalette.ColorRole.ButtonText, color)
        palette.setColor(QPalette.ColorRole.WindowText, color)
        btn.setPalette(palette)
        
        # Also set stylesheet to ensure all states use the color
        button_style = f"""
            QPushButton {{
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: #2a2d2e;
                color: {text_color};
            }}
            QPushButton:checked {{
                background-color: #094771;
                color: {text_color};
            }}
            QPushButton:pressed {{
                color: {text_color};
            }}
        """
        
        # Apply style directly to button
        btn.setStyleSheet(button_style)
    
    def show_context_menu(self, position, server_name: str, button: QPushButton):
        """Show context menu for a server button"""
        menu = QMenu(self)
        
        # Get the latest server status - check both cached and fresh
        parent = self.parent()
        server_status = self.server_statuses.get(server_name, "stopped")
        # Also get fresh status from server_manager to ensure it's up to date
        if hasattr(parent, 'server_manager'):
            fresh_status = parent.server_manager.get_server_status(server_name)
            server_status = fresh_status
            # Update cached status
            self.server_statuses[server_name] = fresh_status
        
        # Start action
        start_action = QAction("Start Server", self)
        start_action.setEnabled(server_status != "running")
        start_action.triggered.connect(lambda: self.context_action.emit("start", server_name))
        menu.addAction(start_action)
        
        # Stop action
        stop_action = QAction("Stop Server", self)
        stop_action.setEnabled(server_status == "running")
        stop_action.triggered.connect(lambda: self.context_action.emit("stop", server_name))
        menu.addAction(stop_action)
        
        # Restart action
        restart_action = QAction("Restart Server", self)
        restart_action.setEnabled(server_status == "running")
        restart_action.triggered.connect(lambda: self.context_action.emit("restart", server_name))
        menu.addAction(restart_action)
        
        menu.addSeparator()
        
        # Edit action
        edit_action = QAction("Edit Server", self)
        edit_action.triggered.connect(lambda: self.context_action.emit("edit", server_name))
        menu.addAction(edit_action)
        
        # Remove action
        remove_action = QAction("Remove Server", self)
        remove_action.triggered.connect(lambda: self.context_action.emit("remove", server_name))
        menu.addAction(remove_action)
        
        # Show menu at cursor position
        menu.exec(button.mapToGlobal(position))
    
    def select_item(self, name: str):
        """Select an item and emit signal"""
        # Uncheck previous selection
        if self.selected_item == "dashboard":
            self.dashboard_btn.setChecked(False)
        elif self.selected_item in self.server_buttons:
            self.server_buttons[self.selected_item].setChecked(False)
        
        # Check new selection
        self.selected_item = name
        if name == "dashboard":
            self.dashboard_btn.setChecked(True)
        elif name in self.server_buttons:
            self.server_buttons[name].setChecked(True)
        
        # Emit signal
        self.item_selected.emit(name)

