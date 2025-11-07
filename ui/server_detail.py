"""
Server detail view showing information, status, metrics, and logs
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFormLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QColor
from datetime import datetime, timezone, timedelta
import re
from typing import Dict
from .constants import SPACING_MEDIUM, SPACING_NORMAL, SPACING_SMALL
from .styles import (
    get_server_detail_style, get_info_group_style, get_primary_button_style,
    get_error_button_style, get_label_style
)
from .performance_graph import PerformanceGraphTabWidget


class ServerDetailView(QWidget):
    """Detail view for individual server showing info, status, metrics, and logs"""
    
    def __init__(self, server_name: str, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.parent_window = parent
        self.init_ui()
        # Load persistent logs after UI is initialized
        self.load_persistent_logs()
        
        # Timer to update graphs
        self.graph_update_timer = QTimer()
        self.graph_update_timer.timeout.connect(self.update_graphs)
        self.graph_update_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize server detail UI"""
        self.setStyleSheet(get_server_detail_style())
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget that will hold all the content
        content_widget = QWidget()
        content_widget.setStyleSheet(get_server_detail_style())
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM, SPACING_MEDIUM)
        layout.setSpacing(SPACING_NORMAL)
        content_widget.setLayout(layout)
        
        # Title
        title_label = QLabel(self.server_name)
        title_label.setStyleSheet(get_label_style("large", "primary"))
        layout.addWidget(title_label)
        
        # Status and metrics section (moved to top for quick overview)
        status_group = QWidget()
        status_group.setStyleSheet(get_info_group_style())
        status_layout = QHBoxLayout()
        status_layout.setSpacing(SPACING_NORMAL)
        status_group.setLayout(status_layout)
        
        self.status_label = QLabel("Status: --")
        self.status_label.setStyleSheet(get_label_style("medium", "primary") + " padding: 10px;")
        status_layout.addWidget(self.status_label)
        
        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setStyleSheet(get_label_style("medium", "info") + " padding: 10px;")
        status_layout.addWidget(self.cpu_label)
        
        self.ram_label = QLabel("RAM: -- MB")
        self.ram_label.setStyleSheet(get_label_style("medium", "info") + " padding: 10px;")
        status_layout.addWidget(self.ram_label)
        
        status_layout.addStretch()
        layout.addWidget(status_group)
        
        # Action buttons section (controls right after status)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING_SMALL)
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet(get_primary_button_style())
        self.start_btn.clicked.connect(self.start_server)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(get_primary_button_style())
        self.stop_btn.clicked.connect(self.stop_server)
        button_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setStyleSheet(get_primary_button_style())
        self.restart_btn.clicked.connect(self.restart_server)
        button_layout.addWidget(self.restart_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet(get_primary_button_style())
        self.edit_btn.clicked.connect(self.edit_server)
        button_layout.addWidget(self.edit_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setStyleSheet(get_primary_button_style() + get_error_button_style())
        self.remove_btn.clicked.connect(self.remove_server)
        button_layout.addWidget(self.remove_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Server information section (details below controls)
        info_group = QWidget()
        info_group.setStyleSheet(get_info_group_style())
        info_layout = QFormLayout()
        info_layout.setSpacing(SPACING_SMALL)
        info_group.setLayout(info_layout)
        
        # Create form fields
        self.name_label = self._create_form_field("Name:", info_layout)
        self.path_label = self._create_form_field("Path:", info_layout)
        self.command_label = self._create_form_field("Command:", info_layout)
        self.args_label = self._create_form_field("Arguments:", info_layout)
        self.port_label = self._create_form_field("Port:", info_layout)
        
        self.path_label.setWordWrap(True)
        layout.addWidget(info_group)
        
        # Performance graphs section
        graphs_label = QLabel("Performance Graphs")
        graphs_label.setStyleSheet(get_label_style("normal", "primary") + " font-weight: bold;")
        layout.addWidget(graphs_label)
        
        self.performance_graphs = PerformanceGraphTabWidget()
        self.performance_graphs.setMinimumHeight(350)
        # Connect time range change signal to update graphs
        self.performance_graphs.time_range_changed.connect(self.update_graphs)
        layout.addWidget(self.performance_graphs)
        
        # Logs/output area
        logs_label = QLabel("Logs:")
        logs_label.setStyleSheet(get_label_style("normal", "primary") + " font-weight: bold;")
        layout.addWidget(logs_label)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        font = QFont("Courier", 10)
        self.logs_text.setFont(font)
        self.logs_text.setPlaceholderText("Server logs will appear here...")
        self.logs_text.setMinimumHeight(400)  # Set minimum height to make it taller
        
        # Set up text formats for color coding
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor(150, 150, 150))  # Dimmer gray for timestamps
        
        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor(200, 200, 200))  # Light gray for normal logs
        
        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(QColor(255, 200, 100))  # Orange/yellow for warnings
        
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(255, 100, 100))  # Red for errors
        
        layout.addWidget(self.logs_text, stretch=1)  # Give it stretch factor to take available space
        
        # Log control buttons
        log_buttons_layout = QHBoxLayout()
        log_buttons_layout.setSpacing(SPACING_SMALL)
        
        # Toggle timestamp button
        self.toggle_timestamp_btn = QPushButton("Hide Timestamps")
        self.toggle_timestamp_btn.setStyleSheet(get_primary_button_style())
        self.toggle_timestamp_btn.clicked.connect(self.toggle_timestamps)
        self.show_timestamps = True  # Show timestamps by default
        log_buttons_layout.addWidget(self.toggle_timestamp_btn)
        
        # Clear logs button
        clear_btn = QPushButton("Clear Logs")
        clear_btn.setStyleSheet(get_primary_button_style())
        clear_btn.clicked.connect(self.clear_logs)
        log_buttons_layout.addWidget(clear_btn)
        
        log_buttons_layout.addStretch()
        layout.addLayout(log_buttons_layout)
        
        # Add stretch at the end to push content to top when scrollable
        layout.addStretch()
        
        # Set content widget as scroll area's widget
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
    
    def _create_form_field(self, label_text: str, form_layout: QFormLayout) -> QLabel:
        """Create a form field with label and value"""
        label = QLabel(label_text)
        label.setStyleSheet(get_label_style("small", "tertiary"))
        value_label = QLabel("--")
        value_label.setStyleSheet(get_label_style("small", "primary"))
        form_layout.addRow(label, value_label)
        return value_label
    
    def update_server_info(self, server_config: Dict):
        """Update displayed server information"""
        self.name_label.setText(server_config.get("name", self.server_name))
        self.path_label.setText(server_config.get("path", "--"))
        self.command_label.setText(server_config.get("command", "node"))
        self.args_label.setText(server_config.get("args", "--") or "--")
        port = server_config.get("port")
        self.port_label.setText(str(port) if port else "Auto")
    
    def update_status(self, status: str):
        """Update status display and button states"""
        self.status_label.setText(f"Status: {status}")
        if status == "running":
            self.status_label.setStyleSheet(
                get_label_style("medium", "success") + " padding: 10px;"
            )
        else:
            self.status_label.setStyleSheet(
                get_label_style("medium", "error") + " padding: 10px;"
            )
        
        # Update button states based on status
        is_running = (status == "running")
        self.start_btn.setEnabled(not is_running)
        self.stop_btn.setEnabled(is_running)
        self.restart_btn.setEnabled(is_running)
    
    def update_metrics(self, metrics: Dict):
        """Update CPU and RAM display"""
        self.cpu_label.setText(f"CPU: {metrics.get('cpu_percent', 0):.1f}%")
        self.ram_label.setText(f"RAM: {metrics.get('memory_mb', 0):.1f} MB")
    
    def set_server_name(self, name: str):
        """Change the displayed server"""
        self.server_name = name
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in UTC+7 format"""
        utc_plus_7 = timezone(timedelta(hours=7))
        now = datetime.now(utc_plus_7)
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def _parse_log_line(line: str) -> tuple[str, str]:
        """
        Parse a log line to extract timestamp and message
        
        Returns:
            Tuple of (timestamp, message) or (None, original_line) if no timestamp
        """
        # Pattern: YYYY-MM-DD HH:MM:SS message (also support old format with brackets for backward compatibility)
        pattern_with_brackets = r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(.+)$'
        pattern_without_brackets = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.+)$'
        
        match = re.match(pattern_with_brackets, line)
        if match:
            return match.group(1), match.group(2)
        
        match = re.match(pattern_without_brackets, line)
        if match:
            return match.group(1), match.group(2)
        
        return None, line
    
    def _is_warning_log(self, text: str) -> bool:
        """Check if log line contains warning keywords"""
        warning_keywords = ['warning', 'Warning', 'WARNING', 'warn', 'Warn', 'WARN']
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in warning_keywords)
    
    def _is_error_log(self, text: str) -> bool:
        """Check if log line contains error keywords (excluding warnings)"""
        error_keywords = ['error', 'Error', 'ERROR', 'exception', 'Exception', 'EXCEPTION',
                         'fail', 'Fail', 'FAIL', 'fatal', 'Fatal', 'FATAL',
                         'critical', 'Critical', 'CRITICAL']
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in error_keywords)
    
    def append_log(self, text: str, is_error: bool = False):
        """Append text to logs area with color coding and timestamp"""
        # Parse timestamp and message
        timestamp, message = self._parse_log_line(text)
        
        # Extract the actual message for error/warning detection (without timestamp)
        detection_text = message if message != text else text
        
        # Determine format based on content analysis and stderr flag
        # Priority: warning detection > error detection > stderr flag > normal
        if self._is_warning_log(detection_text):
            message_format = self.warning_format
        elif self._is_error_log(detection_text) or is_error:
            # Treat as error (stderr or contains error keywords)
            message_format = self.error_format
        else:
            message_format = self.normal_format
        
        # Move cursor to end and insert text with formatting
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        if self.show_timestamps:
            # Add timestamp if not present
            if not timestamp:
                timestamp = self._get_timestamp()
            
            # Insert timestamp with timestamp format
            cursor.setCharFormat(self.timestamp_format)
            cursor.insertText(f"{timestamp} ")
            
            # Insert message with appropriate color format
            cursor.setCharFormat(message_format)
            cursor.insertText(message)
        else:
            # Insert only message without timestamp
            cursor.setCharFormat(message_format)
            cursor.insertText(message)
        
        cursor.insertText('\n')
        
        # Auto-scroll to bottom
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Clear the logs area and persistent storage"""
        self.logs_text.clear()
        # Clear persistent logs
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            self.parent_window.server_manager.clear_logs(self.server_name)
    
    def load_persistent_logs(self):
        """Load logs from persistent storage with color coding"""
        if self.parent_window and hasattr(self.parent_window, 'server_manager'):
            # Load last 10000 lines to avoid loading too much at once
            logs = self.parent_window.server_manager.load_logs(self.server_name, max_lines=10000)
            if logs:
                # Clear and add logs with color coding
                self.logs_text.clear()
                cursor = self.logs_text.textCursor()
                for log_line in logs:
                    # Parse timestamp and message
                    timestamp, message = self._parse_log_line(log_line)
                    
                    # Extract message for error/warning detection
                    detection_text = message if message != log_line else log_line
                    
                    # Determine format based on content analysis
                    if self._is_warning_log(detection_text):
                        message_format = self.warning_format
                    elif self._is_error_log(detection_text):
                        message_format = self.error_format
                    else:
                        message_format = self.normal_format
                    
                    if self.show_timestamps:
                        # Add timestamp if not present (for backward compatibility)
                        if not timestamp:
                            timestamp = self._get_timestamp()
                        
                        # Insert timestamp with timestamp format
                        cursor.setCharFormat(self.timestamp_format)
                        cursor.insertText(f"{timestamp} ")
                        
                        # Insert message with appropriate color format
                        cursor.setCharFormat(message_format)
                        cursor.insertText(message)
                    else:
                        # Insert only message without timestamp
                        cursor.setCharFormat(message_format)
                        cursor.insertText(message)
                    
                    cursor.insertText('\n')
                
                # Auto-scroll to bottom
                scrollbar = self.logs_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
    
    def toggle_timestamps(self):
        """Toggle showing/hiding timestamps"""
        self.show_timestamps = not self.show_timestamps
        self.toggle_timestamp_btn.setText("Show Timestamps" if not self.show_timestamps else "Hide Timestamps")
        # Reload logs with new timestamp setting
        self.load_persistent_logs()
    
    # Delegate actions to parent window
    def start_server(self):
        if self.parent_window:
            self.parent_window.start_server_by_name(self.server_name)
    
    def stop_server(self):
        if self.parent_window:
            self.parent_window.stop_server_by_name(self.server_name)
    
    def restart_server(self):
        if self.parent_window:
            self.parent_window.restart_server_by_name(self.server_name)
    
    def edit_server(self):
        if self.parent_window:
            self.parent_window.edit_server_by_name(self.server_name)
    
    def remove_server(self):
        if self.parent_window:
            self.parent_window.remove_server_by_name(self.server_name)
    
    def update_graphs(self):
        """Update performance graphs with data for this server"""
        if not self.parent_window or not hasattr(self.parent_window, 'server_manager'):
            return
        
        server_manager = self.parent_window.server_manager
        # Get selected time range from the graph widget
        time_range_seconds = self.performance_graphs.get_time_range_seconds()
        history = server_manager.get_metrics_history(self.server_name, time_range_seconds=time_range_seconds)
        
        if self.server_name not in history or not history[self.server_name]:
            # No data, clear graphs
            self.performance_graphs.update_cpu_data([])
            self.performance_graphs.update_ram_data([])
            return
        
        server_history = history[self.server_name]
        
        # Extract CPU and RAM data points
        cpu_data_points = [(ts, cpu) for ts, cpu, ram in server_history]
        ram_data_points = [(ts, ram) for ts, cpu, ram in server_history]
        
        # Update graphs
        self.performance_graphs.update_cpu_data(cpu_data_points)
        self.performance_graphs.update_ram_data(ram_data_points)

