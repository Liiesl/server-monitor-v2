"""
Node.js Server Manager - PySide6 Application with System Tray
"""
import sys
from typing import Dict
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction

from server_manager import ServerManager
from ui.sidebar import SidebarWidget
from ui.dashboard import DashboardView
from ui.server_detail import ServerDetailView
from ui.server_dialog import ServerDialog
from ui.metrics_monitor import MetricsMonitor


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = ServerManager()
        self.server_views: Dict[str, ServerDetailView] = {}
        self.current_view = None
        self.init_ui()
        self.init_system_tray()
        
        # Connect signals to slot handlers
        self.server_manager.server_status_changed.connect(self.on_server_status_changed)
        self.server_manager.server_metrics_changed.connect(self.on_server_metrics_changed)
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        self.server_manager.server_log.connect(self.on_server_log)
        
        # Create and start metrics monitoring thread
        self.metrics_monitor = MetricsMonitor(self.server_manager)
        self.metrics_monitor.start()
        
        # Lightweight timer for dead process detection only (1 second)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_process_status)
        self.status_timer.start(1000)  # Check every 1 second
        
        # Initial update
        self.update_dashboard()
        self.sidebar.update_server_list(self.server_manager.get_all_servers())
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Node.js Server Manager")
        self.setMinimumSize(800, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # Sidebar
        self.sidebar = SidebarWidget(self)
        self.sidebar.item_selected.connect(self.on_sidebar_item_selected)
        self.sidebar.context_action.connect(self.on_sidebar_context_action)
        main_layout.addWidget(self.sidebar)
        
        # Stacked widget for main content area
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Dashboard view
        self.dashboard_view = DashboardView(self)
        self.stacked_widget.addWidget(self.dashboard_view)
        
        # Set Dashboard as initial view
        self.current_view = "dashboard"
    
    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a simple server/gear icon
        painter.setBrush(QColor(70, 130, 180))  # Steel blue
        painter.setPen(QColor(50, 100, 150))
        painter.drawEllipse(4, 4, 24, 24)
        
        # Draw some lines to represent a server
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(10, 10, 12, 8)
        painter.drawRect(10, 20, 12, 4)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def init_system_tray(self):
        """Initialize system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "System Tray", 
                               "System tray is not available on this system.")
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        # Create a simple icon programmatically
        icon = self.create_tray_icon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Node.js Server Manager")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide Window", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def quit_application(self):
        """Quit the application"""
        # Stop metrics monitor thread
        if hasattr(self, 'metrics_monitor'):
            self.metrics_monitor.stop()
        self.server_manager.stop_all_servers()
        QApplication.quit()
    
    def on_sidebar_item_selected(self, name: str):
        """Handle sidebar item selection - switch views"""
        if name == "dashboard":
            self.stacked_widget.setCurrentWidget(self.dashboard_view)
            self.current_view = "dashboard"
        else:
            # Server detail view
            if name not in self.server_views:
                # Create new server detail view
                server_view = ServerDetailView(name, self)
                self.server_views[name] = server_view
                self.stacked_widget.addWidget(server_view)
                
                # Update with current server data
                servers = self.server_manager.get_all_servers()
                if name in servers:
                    config = servers[name].copy()
                    config["name"] = name
                    server_view.update_server_info(config)
                    status = self.server_manager.get_server_status(name)
                    server_view.update_status(status)
                    
                    # If server is running, try to get current metrics
                    if status == "running" and name in self.server_manager.psutil_processes:
                        metrics = self.server_manager.get_server_metrics(name)
                        if metrics:
                            server_view.update_metrics(metrics)
                        else:
                            # Initialize with zero metrics if not available yet
                            server_view.update_metrics({"cpu_percent": 0, "memory_mb": 0})
                    else:
                        server_view.update_metrics({"cpu_percent": 0, "memory_mb": 0})
            
            # Switch to server view
            self.stacked_widget.setCurrentWidget(self.server_views[name])
            self.current_view = name
    
    def on_sidebar_context_action(self, action: str, server_name: str):
        """Handle context menu actions from sidebar"""
        if action == "start":
            self.start_server_by_name(server_name)
        elif action == "stop":
            self.stop_server_by_name(server_name)
        elif action == "restart":
            self.restart_server_by_name(server_name)
        elif action == "edit":
            self.edit_server_by_name(server_name)
        elif action == "remove":
            self.remove_server_by_name(server_name)
    
    def update_dashboard(self):
        """Update the dashboard view"""
        self.dashboard_view.update_table(self.server_manager)
    
    def check_process_status(self):
        """Lightweight method for timer - only checks for dead processes"""
        # Just check status for all servers (will emit signals if status changes)
        self.server_manager.get_all_servers()
    
    def on_server_status_changed(self, name: str, status: str):
        """Handle server status change signal - update both Dashboard and detail view"""
        # Update Dashboard table
        self.dashboard_view.on_server_status_changed(name, status)
        self.dashboard_view.update_summary_stats(self.server_manager)
        
        # Update sidebar status and button color
        self.sidebar.update_server_status(name, status)
        
        # Update ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].update_status(status)
    
    def on_server_metrics_changed(self, name: str, metrics: dict):
        """Handle server metrics change signal - update both Dashboard and detail view"""
        # Update Dashboard table
        self.dashboard_view.on_server_metrics_changed(name, metrics)
        self.dashboard_view.update_summary_stats(self.server_manager)
        
        # Update ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].update_metrics(metrics)
    
    def on_server_started(self, name: str):
        """Handle server started signal"""
        self.update_dashboard()
        self.sidebar.update_server_list(self.server_manager.get_all_servers())
        
        # Update ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].update_status("running")
        
        self.tray_icon.showMessage("Server Started", f"Server '{name}' has been started.")
    
    def on_server_stopped(self, name: str):
        """Handle server stopped signal"""
        # Update Dashboard table
        self.dashboard_view.on_server_stopped(name)
        self.dashboard_view.update_summary_stats(self.server_manager)
        
        # Update ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].update_status("stopped")
            self.server_views[name].update_metrics({"cpu_percent": 0, "memory_mb": 0})
        
        self.tray_icon.showMessage("Server Stopped", f"Server '{name}' has been stopped.")
    
    def on_server_log(self, name: str, log_line: str, is_error: bool):
        """Handle server log signal - save to persistent storage and forward to ServerDetailView if visible"""
        # Save log to persistent storage
        self.server_manager.save_log(name, log_line)
        # Forward to ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].append_log(log_line, is_error)
    
    def get_selected_server(self):
        """Get the name of the selected server from current view"""
        if self.current_view == "dashboard":
            return self.dashboard_view.get_selected_server()
        elif self.current_view in self.server_views:
            return self.current_view
        return None
    
    def add_server(self):
        """Add a new server"""
        dialog = ServerDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"] or not data["path"]:
                QMessageBox.warning(self, "Invalid Input", 
                                  "Server name and path are required.")
                return
            
            if self.server_manager.add_server(
                data["name"], data["path"], data["command"], 
                data["args"], data["port"],
                data.get("server_type", "nodejs"),
                data.get("python_command"),
                data.get("venv_path")
            ):
                self.update_dashboard()
                self.sidebar.update_server_list(self.server_manager.get_all_servers())
                QMessageBox.information(self, "Success", "Server added successfully.")
            else:
                QMessageBox.warning(self, "Error", "Server name already exists.")
    
    def edit_server(self):
        """Edit selected server from dashboard"""
        # Since we removed table selection, edit is now done via detail view
        # This method can be called from context menu or other places
        QMessageBox.information(self, "Edit Server", "Please click 'View Details' on a server card to edit it.")
    
    def edit_server_by_name(self, name: str):
        """Edit server by name"""
        server_config = self.server_manager.servers.get(name, {})
        server_config["name"] = name
        dialog = ServerDialog(self, server_config)
        
        if dialog.exec():
            data = dialog.get_data()
            # Handle venv_path - only pass if server_type is flask
            venv_path = None
            if data.get("server_type") == "flask":
                venv_path = data.get("venv_path", "")
            
            if self.server_manager.update_server(
                name, data["path"], data["command"], 
                data["args"], data["port"],
                data.get("server_type"), data.get("python_command"),
                venv_path
            ):
                self.update_dashboard()
                # Update detail view if visible
                if name in self.server_views:
                    config = self.server_manager.servers[name].copy()
                    config["name"] = name
                    self.server_views[name].update_server_info(config)
                QMessageBox.information(self, "Success", "Server updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to update server.")
    
    def remove_server(self):
        """Remove selected server from dashboard"""
        # Since we removed table selection, remove is now done via detail view
        QMessageBox.information(self, "Remove Server", "Please click 'View Details' on a server card to remove it.")
    
    def remove_server_by_name(self, name: str):
        """Remove server by name"""
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove server '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.server_manager.remove_server(name):
                # Remove detail view if exists
                if name in self.server_views:
                    view = self.server_views[name]
                    self.stacked_widget.removeWidget(view)
                    view.deleteLater()
                    del self.server_views[name]
                
                # If this was the current view, switch to dashboard
                if self.current_view == name:
                    self.on_sidebar_item_selected("dashboard")
                    self.sidebar.select_item("dashboard")
                
                self.update_dashboard()
                self.sidebar.update_server_list(self.server_manager.get_all_servers())
                QMessageBox.information(self, "Success", "Server removed successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to remove server.")
    
    def start_selected_server(self):
        """Start selected server from dashboard"""
        # Start is now handled via card buttons
        pass
    
    def start_server_by_name(self, name: str):
        """Start server by name"""
        if self.server_manager.start_server(name):
            # Signal will handle UI update
            pass
        else:
            QMessageBox.warning(self, "Error", "Failed to start server. Check if the path is correct.")
    
    def stop_selected_server(self):
        """Stop selected server from dashboard"""
        # Stop is now handled via card buttons
        pass
    
    def stop_server_by_name(self, name: str):
        """Stop server by name"""
        if self.server_manager.stop_server(name):
            # Signal will handle UI update
            pass
        else:
            QMessageBox.warning(self, "Error", "Server is not running.")
    
    def restart_selected_server(self):
        """Restart selected server from dashboard"""
        # Restart is now handled via card buttons
        pass
    
    def restart_server_by_name(self, name: str):
        """Restart server by name"""
        if self.server_manager.restart_server(name):
            # Signal will handle UI update
            pass
        else:
            QMessageBox.warning(self, "Error", "Failed to restart server.")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Don't quit when window is closed
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
