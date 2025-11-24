"""
Stack Detail View - Shows details and controls for a server stack
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from .styles import (
    get_card_style, get_label_style, get_primary_button_style,
    get_danger_button_style, get_success_button_style
)
from .constants import SPACING_LARGE, SPACING_MEDIUM, SPACING_NORMAL

class StackDetailView(QWidget):
    """View showing details of a specific server stack"""
    
    def __init__(self, stack_name: str, parent=None):
        super().__init__(parent)
        self.stack_name = stack_name
        self.parent_window = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(SPACING_LARGE, SPACING_LARGE, SPACING_LARGE, SPACING_LARGE)
        main_layout.setSpacing(SPACING_LARGE)
        self.setLayout(main_layout)
        
        # Header Section
        header_layout = QHBoxLayout()
        
        # Title and Status
        title_layout = QVBoxLayout()
        self.title_label = QLabel(f"Stack: {self.stack_name}")
        self.title_label.setStyleSheet(get_label_style("title", "primary"))
        title_layout.addWidget(self.title_label)
        
        self.status_label = QLabel("Status: Unknown")
        self.status_label.setStyleSheet(get_label_style("normal", "tertiary"))
        title_layout.addWidget(self.status_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Stack Controls
        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.setStyleSheet(get_success_button_style())
        self.start_all_btn.clicked.connect(self.on_start_all)
        header_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.setStyleSheet(get_danger_button_style())
        self.stop_all_btn.clicked.connect(self.on_stop_all)
        header_layout.addWidget(self.stop_all_btn)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #3e3e42;")
        main_layout.addWidget(separator)
        
        # Servers List Section
        servers_header = QLabel("Servers in Stack")
        servers_header.setStyleSheet(get_label_style("large", "primary"))
        main_layout.addWidget(servers_header)
        
        # Scroll area for server cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")
        
        self.servers_container = QWidget()
        self.servers_container.setStyleSheet("background-color: transparent;")
        self.servers_layout = QVBoxLayout()
        self.servers_layout.setSpacing(SPACING_NORMAL)
        self.servers_layout.addStretch() # Push items to top
        self.servers_container.setLayout(self.servers_layout)
        
        scroll_area.setWidget(self.servers_container)
        main_layout.addWidget(scroll_area)
        
        # Initial update
        self.update_stack_info()
        
    def update_stack_info(self):
        """Update stack information and server list"""
        if not self.parent_window or not hasattr(self.parent_window, 'server_manager'):
            return
            
        server_manager = self.parent_window.server_manager
        stacks = server_manager.get_stacks()
        
        if self.stack_name not in stacks:
            return
            
        server_names = stacks[self.stack_name]
        
        # Update Status
        status = server_manager.get_stack_status(self.stack_name)
        color = "#cccccc"
        if status == "running":
            color = "#4caf50"
        elif status == "partial":
            color = "#ff9800"
            
        self.status_label.setText(f"Status: {status.title()}")
        self.status_label.setStyleSheet(f"font-size: 14px; color: {color};")
        
        # Update Server List
        # Clear existing items (except stretch)
        while self.servers_layout.count() > 1:
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Add server cards
        for name in server_names:
            card = self._create_server_card(name, server_manager)
            self.servers_layout.insertWidget(self.servers_layout.count() - 1, card)
            
    def _create_server_card(self, name: str, server_manager) -> QWidget:
        """Create a mini card for a server"""
        card = QWidget()
        card.setStyleSheet(get_card_style())
        layout = QHBoxLayout()
        layout.setContentsMargins(SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL, SPACING_NORMAL)
        card.setLayout(layout)
        
        # Status Indicator
        status = server_manager.get_server_status(name)
        status_color = "#4caf50" if status == "running" else "#f44336"
        indicator = QLabel("●")
        indicator.setStyleSheet(f"color: {status_color}; font-size: 16px;")
        layout.addWidget(indicator)
        
        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet(get_label_style("normal", "primary") + "font-weight: bold;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Controls
        if status == "running":
            stop_btn = QPushButton("Stop")
            stop_btn.setFixedSize(60, 24)
            stop_btn.setStyleSheet(get_danger_button_style())
            stop_btn.clicked.connect(lambda checked, n=name: self.parent_window.stop_server_by_name(n))
            layout.addWidget(stop_btn)
        else:
            start_btn = QPushButton("Start")
            start_btn.setFixedSize(60, 24)
            start_btn.setStyleSheet(get_success_button_style())
            start_btn.clicked.connect(lambda checked, n=name: self.parent_window.start_server_by_name(n))
            layout.addWidget(start_btn)
            
        return card
        
    def on_start_all(self):
        """Start all servers in stack"""
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.start_stack(self.stack_name)
            
    def on_stop_all(self):
        """Stop all servers in stack"""
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.stop_stack(self.stack_name)
            
    def update_status(self):
        """Update status display (called by signals)"""
        self.update_stack_info()
