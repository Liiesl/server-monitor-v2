"""
Performance graph widget using QPainter (no external libraries)
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QComboBox, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygon
from typing import List, Tuple
from .constants import (
    COLOR_BACKGROUND_CARD, COLOR_BACKGROUND_MEDIUM, COLOR_BORDER, 
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_TERTIARY, 
    COLOR_INFO, COLOR_SUCCESS, RADIUS_MEDIUM, RADIUS_SMALL, SPACING_SMALL
)


class PerformanceGraphWidget(QWidget):
    """Widget that draws performance graphs using QPainter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        
        # Data storage: list of (timestamp, value) tuples
        self.data_points: List[Tuple[float, float]] = []
        self.max_data_points = 300  # Keep last 5 minutes at ~1 second intervals
        self.fixed_time_range = 300.0  # Default 5 minutes in seconds
        
        # Graph settings
        self.graph_type = "cpu"  # "cpu" or "ram"
        self.line_color = QColor(COLOR_INFO)
        self.grid_color = QColor(COLOR_BORDER)
        self.text_color = QColor(COLOR_TEXT_SECONDARY)
        
        # Padding for graph area
        self.padding_left = 60
        self.padding_right = 20
        self.padding_top = 40
        self.padding_bottom = 40
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(500)  # Update every 500ms for smooth animation
    
    def set_graph_type(self, graph_type: str):
        """Set the type of graph: 'cpu' or 'ram'"""
        self.graph_type = graph_type
        if graph_type == "cpu":
            self.line_color = QColor(COLOR_INFO)
        else:  # ram
            self.line_color = QColor(COLOR_SUCCESS)
        self.update()
        
    def set_time_range(self, seconds: float):
        """Set the fixed time range for the X-axis in seconds"""
        self.fixed_time_range = float(seconds)
        self.update()
    
    def update_data(self, data_points: List[Tuple[float, float]]):
        """Update the graph data points (timestamp, value)"""
        # Keep enough data points to cover the time range (plus some buffer)
        # Assuming ~1 point per second, we need at least fixed_time_range points
        # But we'll keep a bit more just in case
        limit = max(self.max_data_points, int(self.fixed_time_range * 1.2))
        self.data_points = data_points[-limit:]
        self.update()
    
    def paintEvent(self, event):
        """Draw the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Calculate graph area
        graph_x = self.padding_left
        graph_y = self.padding_top
        graph_width = width - self.padding_left - self.padding_right
        graph_height = height - self.padding_top - self.padding_bottom
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor(COLOR_BACKGROUND_CARD))
        
        # Calculate time range based on fixed window
        import time
        current_time = time.time()
        start_time = current_time - self.fixed_time_range
        end_time = current_time
        
        # Calculate value range
        if self.data_points:
            values = [value for _, value in self.data_points]
            min_value = min(values)
            max_value = max(values)
        else:
            values = []
            min_value = 0
            max_value = 100 if self.graph_type == "cpu" else 1024
        
        # Add padding to range (10% on top and bottom)
        value_range = max_value - min_value
        if value_range == 0:
            value_range = max_value if max_value > 0 else 1
            min_value = 0
            max_value = value_range * 1.2
        else:
            padding = value_range * 0.1
            min_value = max(0, min_value - padding)
            max_value = max_value + padding
            
        # Draw grid lines
        painter.setPen(QPen(QColor(self.grid_color), 1, Qt.PenStyle.DashLine))
        
        # Horizontal grid lines (value lines)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = graph_y + (graph_height * i / num_h_lines)
            painter.drawLine(graph_x, int(y), graph_x + graph_width, int(y))
            
            # Draw value labels
            value = max_value - (max_value - min_value) * i / num_h_lines
            label_text = self._format_value(value)
            painter.setPen(QColor(self.text_color))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(5, int(y + 5), label_text)
            painter.setPen(QPen(QColor(self.grid_color), 1, Qt.PenStyle.DashLine))
        
        # Vertical grid lines (time lines)
        num_v_lines = 6
        for i in range(num_v_lines + 1):
            x = graph_x + (graph_width * i / num_v_lines)
            painter.drawLine(int(x), graph_y, int(x), graph_y + graph_height)
            
            # Draw time labels (optional, e.g. -5m, -4m...)
            # time_offset = self.fixed_time_range * (1 - i / num_v_lines)
            # label_text = f"-{int(time_offset)}s"
            # painter.drawText(int(x - 15), int(graph_y + graph_height + 15), label_text)

        if not self.data_points:
            # Draw "No data" message
            painter.setPen(QColor(COLOR_TEXT_TERTIARY))
            font = QFont("Arial", 12)
            painter.setFont(font)
            painter.drawText(
                graph_x, graph_y, graph_width, graph_height,
                Qt.AlignmentFlag.AlignCenter,
                "No data available"
            )
        else:
            # Draw graph line
            painter.setPen(QPen(self.line_color, 2))
            
            points = []
            for timestamp, value in self.data_points:
                # Filter points outside current window
                if timestamp < start_time:
                    continue
                    
                # Calculate x position (time-based)
                if self.fixed_time_range > 0:
                    x_ratio = (timestamp - start_time) / self.fixed_time_range
                else:
                    x_ratio = 0
                
                # Clamp x to graph area
                x = graph_x + graph_width * x_ratio
                
                # Calculate y position (value-based, inverted)
                if max_value > min_value:
                    y_ratio = (value - min_value) / (max_value - min_value)
                else:
                    y_ratio = 0.5
                y = graph_y + graph_height * (1 - y_ratio)
                
                points.append((int(x), int(y)))
            
            # Draw line connecting points
            if len(points) > 1:
                for i in range(len(points) - 1):
                    # Only draw if points are within bounds (simple check)
                    p1 = points[i]
                    p2 = points[i+1]
                    if p1[0] >= graph_x and p2[0] <= graph_x + graph_width:
                        painter.drawLine(p1[0], p1[1], p2[0], p2[1])
            
            # Draw filled area under the line
            if len(points) > 0:
                fill_color = QColor(self.line_color)
                fill_color.setAlpha(50)
                painter.setBrush(fill_color)
                painter.setPen(Qt.PenStyle.NoPen)
                
                # Create polygon for fill
                # Start at bottom-left of the first point's X
                first_x = points[0][0]
                last_x = points[-1][0]
                
                polygon_points = [
                    (first_x, graph_y + graph_height),  # Bottom left (at first point X)
                ]
                polygon_points.extend(points)
                polygon_points.append((last_x, graph_y + graph_height))  # Bottom right (at last point X)
                
                polygon = QPolygon([QPoint(x, y) for x, y in polygon_points])
                
                # Clip to graph area to avoid drawing outside
                painter.setClipRect(graph_x, graph_y, graph_width, graph_height)
                painter.drawPolygon(polygon)
                painter.setClipping(False)
        
        # Draw title
        title = "CPU Usage (%)" if self.graph_type == "cpu" else "RAM Usage (MB)"
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(
            graph_x, 5, graph_width, self.padding_top - 5,
            Qt.AlignmentFlag.AlignCenter,
            title
        )
    
    def _format_value(self, value: float) -> str:
        """Format value for display"""
        if self.graph_type == "cpu":
            return f"{value:.1f}%"
        else:  # ram
            return f"{value:.0f} MB"


class PerformanceGraphTabWidget(QWidget):
    """Widget with tabs for CPU and RAM graphs"""
    
    # Signal emitted when time range changes
    time_range_changed = Signal(float)  # Emits time_range_seconds
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_time_range_seconds = 300.0  # Default: 5 minutes
        self.init_ui()
    
    def init_ui(self):
        """Initialize the tab widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_SMALL)
        self.setLayout(layout)
        
        # Time range selector
        time_range_layout = QHBoxLayout()
        time_range_layout.setContentsMargins(0, 0, 0, 0)
        
        time_range_label = QLabel("Time Range:")
        time_range_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; padding: 5px;")
        time_range_layout.addWidget(time_range_label)
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems([
            "Last 5 minutes",
            "Last 15 minutes",
            "Last 30 minutes",
            "Last 1 hour",
            "Last 6 hours",
            "Last 12 hours",
            "Last 24 hours"
        ])
        self.time_range_combo.setCurrentIndex(0)  # Default to 5 minutes
        self.time_range_combo.currentIndexChanged.connect(self._on_time_range_changed)
        
        # Style the combo box
        self.time_range_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_BACKGROUND_MEDIUM};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: {RADIUS_SMALL}px;
                padding: 5px 10px;
                min-width: 150px;
            }}
            QComboBox:hover {{
                background-color: {COLOR_BORDER};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_BACKGROUND_MEDIUM};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: {RADIUS_SMALL}px;
                selection-background-color: {COLOR_BORDER};
            }}
        """)
        
        time_range_layout.addWidget(self.time_range_combo)
        time_range_layout.addStretch()
        
        layout.addLayout(time_range_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                border-radius: {RADIUS_MEDIUM}px;
                background-color: {COLOR_BACKGROUND_CARD};
            }}
            QTabBar::tab {{
                background-color: {COLOR_BACKGROUND_MEDIUM};
                color: {COLOR_TEXT_SECONDARY};
                padding: 8px 20px;
                border: none;
                border-top-left-radius: {RADIUS_SMALL}px;
                border-top-right-radius: {RADIUS_SMALL}px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_BACKGROUND_CARD};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QTabBar::tab:hover {{
                background-color: {COLOR_BORDER};
            }}
        """)
        
        # Create CPU graph
        self.cpu_graph = PerformanceGraphWidget()
        self.cpu_graph.set_graph_type("cpu")
        self.cpu_graph.set_time_range(self.current_time_range_seconds)
        self.tab_widget.addTab(self.cpu_graph, "CPU")
        
        # Create RAM graph
        self.ram_graph = PerformanceGraphWidget()
        self.ram_graph.set_graph_type("ram")
        self.ram_graph.set_time_range(self.current_time_range_seconds)
        self.tab_widget.addTab(self.ram_graph, "RAM")
        
        layout.addWidget(self.tab_widget)
    
    def update_cpu_data(self, data_points: List[Tuple[float, float]]):
        """Update CPU graph data"""
        self.cpu_graph.update_data(data_points)
    
    def update_ram_data(self, data_points: List[Tuple[float, float]]):
        """Update RAM graph data"""
        self.ram_graph.update_data(data_points)
    
    def _on_time_range_changed(self, index: int):
        """Handle time range selection change"""
        # Map index to seconds: 5min, 15min, 30min, 1h, 6h, 12h, 24h
        time_ranges = [300, 900, 1800, 3600, 21600, 43200, 86400]
        if 0 <= index < len(time_ranges):
            self.current_time_range_seconds = float(time_ranges[index])
            # Update graphs with new time range
            self.cpu_graph.set_time_range(self.current_time_range_seconds)
            self.ram_graph.set_time_range(self.current_time_range_seconds)
            
            self.time_range_changed.emit(self.current_time_range_seconds)
    
    def get_time_range_seconds(self) -> float:
        """Get the currently selected time range in seconds"""
        return self.current_time_range_seconds

