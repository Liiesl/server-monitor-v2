"""
Dashboard view showing summary statistics
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from server_manager import ServerManager
from .constants import (
    SPACING_LARGE, SPACING_MEDIUM, SPACING_NORMAL, SPACING_SMALL, SPACING_MINIMAL
)
from .styles import (
    get_dashboard_style, get_card_style, get_success_button_style,
    get_label_style
)
from .performance_graph import PerformanceGraphTabWidget


class DashboardView(QWidget):
    """Modern dashboard view showing only summary statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
        
        # Timer to update graphs
        self.graph_update_timer = QTimer()
        self.graph_update_timer.timeout.connect(self.update_graphs)
        self.graph_update_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize dashboard UI"""
        self.setStyleSheet(get_dashboard_style())
        
        # Main layout for the widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet(get_dashboard_style())
        # Set size policy to prevent horizontal expansion
        content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(SPACING_LARGE, SPACING_LARGE, SPACING_LARGE, SPACING_LARGE)
        content_layout.setSpacing(SPACING_MEDIUM)
        content_widget.setLayout(content_layout)
        
        # Title
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet(get_label_style("title", "primary"))
        content_layout.addWidget(title_label)
        
        # Summary stats cards section
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(SPACING_NORMAL)
        
        # Create stat cards
        self.total_label = self._create_stat_card("Total Servers", "0", stats_layout)
        self.running_label = self._create_stat_card("Running", "0", stats_layout, color="success")
        self.stopped_label = self._create_stat_card("Stopped", "0", stats_layout, color="error")
        self.cpu_label = self._create_stat_card("Total CPU", "--", stats_layout, color="info")
        self.ram_label = self._create_stat_card("Total RAM", "-- MB", stats_layout, color="info")
        
        stats_layout.addStretch()
        content_layout.addLayout(stats_layout)
        
        # Performance graphs section
        graphs_label = QLabel("Performance Graphs")
        graphs_label.setStyleSheet(get_label_style("normal", "primary") + " font-weight: bold;")
        content_layout.addWidget(graphs_label)
        
        self.performance_graphs = PerformanceGraphTabWidget()
        self.performance_graphs.setMinimumHeight(350)
        # Connect time range change signal to update graphs
        self.performance_graphs.time_range_changed.connect(self.update_graphs)
        content_layout.addWidget(self.performance_graphs)
        
        # Add Server button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.add_btn = QPushButton("+ Add Server")
        self.add_btn.setStyleSheet(get_success_button_style())
        self.add_btn.clicked.connect(self.add_server)
        button_layout.addWidget(self.add_btn)
        content_layout.addLayout(button_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set content widget as scroll area's widget
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Initial graph update
        self.update_graphs()
    
    def _create_stat_card(self, title: str, value: str, parent_layout: QHBoxLayout, 
                         color: str = "primary") -> QLabel:
        """Create a stat card widget and add it to the layout"""
        card = QWidget()
        card.setStyleSheet(get_card_style())
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(SPACING_MINIMAL)
        card.setLayout(card_layout)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(get_label_style("small", "tertiary"))
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(get_label_style("large", color))
        card_layout.addWidget(value_label)
        
        parent_layout.addWidget(card)
        return value_label
    
    def get_selected_server(self):
        """Get the name of the selected server - not applicable for dashboard"""
        return None
    
    def update_table(self, server_manager: ServerManager):
        """Update the summary statistics"""
        servers = server_manager.get_all_servers()
        
        running_count = 0
        stopped_count = 0
        total_cpu = 0.0
        total_ram = 0.0
        
        for name, config in servers.items():
            status = server_manager.get_server_status(name)
            
            if status == "running":
                running_count += 1
                # Get metrics if available
                if name in server_manager.psutil_processes:
                    if name in server_manager.last_metrics:
                        metrics = server_manager.last_metrics[name]
                        total_cpu += metrics.get("cpu_percent", 0)
                        total_ram += metrics.get("memory_mb", 0)
                    else:
                        metrics = server_manager.get_server_metrics(name)
                        if metrics:
                            total_cpu += metrics.get("cpu_percent", 0)
                            total_ram += metrics.get("memory_mb", 0)
            else:
                stopped_count += 1
        
        # Update summary stats
        self.total_label.setText(str(len(servers)))
        self.running_label.setText(str(running_count))
        self.stopped_label.setText(str(stopped_count))
        
        if running_count > 0:
            self.cpu_label.setText(f"{total_cpu:.1f}%")
            self.ram_label.setText(f"{total_ram:.1f} MB")
        else:
            self.cpu_label.setText("--")
            self.ram_label.setText("-- MB")
    
    def update_summary_stats(self, server_manager: ServerManager):
        """Update only the summary statistics"""
        servers = server_manager.get_all_servers()
        running_count = 0
        total_cpu = 0.0
        total_ram = 0.0
        
        for name in servers.keys():
            status = server_manager.get_server_status(name)
            if status == "running":
                running_count += 1
                if name in server_manager.psutil_processes:
                    # Get cached metrics or calculate directly
                    if name in server_manager.last_metrics:
                        metrics = server_manager.last_metrics[name]
                        total_cpu += metrics.get("cpu_percent", 0)
                        total_ram += metrics.get("memory_mb", 0)
                    else:
                        # Try to get metrics (may return None if no change)
                        metrics = server_manager.get_server_metrics(name)
                        if metrics:
                            total_cpu += metrics.get("cpu_percent", 0)
                            total_ram += metrics.get("memory_mb", 0)
        
        stopped_count = len(servers) - running_count
        
        self.total_label.setText(str(len(servers)))
        self.running_label.setText(str(running_count))
        self.stopped_label.setText(str(stopped_count))
        
        if running_count > 0:
            self.cpu_label.setText(f"{total_cpu:.1f}%")
            self.ram_label.setText(f"{total_ram:.1f} MB")
        else:
            self.cpu_label.setText("--")
            self.ram_label.setText("-- MB")
    
    def on_server_status_changed(self, name: str, status: str):
        """Handle server status change - update summary stats"""
        self.update_summary_stats(self.parent_window.server_manager)
    
    def on_server_metrics_changed(self, name: str, metrics: dict):
        """Handle server metrics change - update summary stats"""
        self.update_summary_stats(self.parent_window.server_manager)
    
    def on_server_stopped(self, name: str):
        """Handle server stopped - update summary stats"""
        self.update_summary_stats(self.parent_window.server_manager)
    
    def update_graphs(self):
        """Update performance graphs with aggregated data from all servers"""
        if not self.parent_window or not hasattr(self.parent_window, 'server_manager'):
            return
        
        server_manager = self.parent_window.server_manager
        # Get selected time range from the graph widget
        time_range_seconds = self.performance_graphs.get_time_range_seconds()
        history = server_manager.get_metrics_history(time_range_seconds=time_range_seconds)
        
        # Aggregate data from all servers
        cpu_data_points = []
        ram_data_points = []
        
        # Collect all timestamps from all servers
        all_timestamps = set()
        for server_name, server_history in history.items():
            for ts, cpu, ram in server_history:
                all_timestamps.add(ts)
        
        if not all_timestamps:
            # No data, clear graphs
            self.performance_graphs.update_cpu_data([])
            self.performance_graphs.update_ram_data([])
            return
        
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # For each timestamp, aggregate CPU and RAM from all running servers
        for timestamp in sorted_timestamps:
            total_cpu = 0.0
            total_ram = 0.0
            count = 0
            
            for server_name, server_history in history.items():
                # Find the closest data point for this timestamp (within 1 second)
                for ts, cpu, ram in server_history:
                    if abs(ts - timestamp) <= 1.0:
                        total_cpu += cpu
                        total_ram += ram
                        count += 1
                        break
            
            if count > 0:
                cpu_data_points.append((timestamp, total_cpu))
                ram_data_points.append((timestamp, total_ram))
        
        # Update graphs
        self.performance_graphs.update_cpu_data(cpu_data_points)
        self.performance_graphs.update_ram_data(ram_data_points)
    
    # Delegate button actions to parent window
    def add_server(self):
        if self.parent_window:
            self.parent_window.add_server()
    
    def edit_server(self):
        # Edit is handled via card's view details button or context menu
        pass
    
    def remove_server(self):
        # Remove is handled via server detail view
        pass
    
    def start_selected_server(self):
        # Start is handled via card buttons
        pass
    
    def stop_selected_server(self):
        # Stop is handled via card buttons
        pass
    
    def restart_selected_server(self):
        # Restart is handled via card buttons
        pass

