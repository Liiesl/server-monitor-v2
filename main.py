"""
Node.js Server Manager - PySide6 Application with System Tray
"""
import sys
import ctypes
from ctypes import wintypes
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QAbstractNativeEventFilter
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction

from server_manager import ServerManager
from ui.sidebar import SidebarWidget
from ui.dashboard import DashboardView
from ui.server_detail import ServerDetailView
from ui.server_dialog import ServerDialog
from ui.settings_dialog import SettingsDialog
from ui.metrics_monitor import MetricsMonitor
from ui.stack_dialog import StackDialog
from ui.stack_detail import StackDetailView

# Windows API constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008


class GlobalShortcutFilter(QAbstractNativeEventFilter):
    """Native event filter to catch global hotkey messages"""
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    def nativeEventFilter(self, eventType, message):
        """Filter native events for hotkey messages"""
        if sys.platform == "win32":
            # eventType can be bytes or string depending on PySide6 version
            try:
                event_type_str = eventType if isinstance(eventType, str) else (eventType.decode('utf-8') if isinstance(eventType, bytes) else str(eventType))
            except:
                event_type_str = str(eventType)
            
            if "windows" in event_type_str.lower() or "win32" in event_type_str.lower():
                try:
                    # Convert VoidPtr to integer, then to ctypes pointer
                    msg_ptr = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG))
                    msg = msg_ptr.contents
                    if msg.message == WM_HOTKEY:
                        self.callback()
                        return True, 0
                except (ValueError, TypeError, AttributeError, OverflowError) as e:
                    # Silently ignore conversion errors
                    pass
        return False, 0


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = ServerManager()
        self.server_views: Dict[str, ServerDetailView] = {}
        self.stack_views: Dict[str, StackDetailView] = {}
        self.current_view = None
        self.hotkey_id = 1  # Unique ID for the hotkey
        self.shortcut_filter = None
        self.init_ui()
        self.init_system_tray()
        self.init_global_shortcut()
        
        # Connect signals to slot handlers
        self.server_manager.server_status_changed.connect(self.on_server_status_changed)
        self.server_manager.server_metrics_changed.connect(self.on_server_metrics_changed)
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        self.server_manager.server_log.connect(self.on_server_log)
        self.server_manager.port_detected.connect(self.on_port_detected)
        
        # Stack signals
        self.server_manager.stack_added.connect(self.on_stack_changed)
        self.server_manager.stack_removed.connect(self.on_stack_changed)
        self.server_manager.stack_updated.connect(self.on_stack_changed)
        
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
        self.sidebar.update_stack_list(self.server_manager.get_stacks())
    
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
        self.sidebar.stack_selected.connect(self.on_sidebar_stack_selected)
        self.sidebar.context_action.connect(self.on_sidebar_context_action)
        self.sidebar.stack_context_action.connect(self.on_sidebar_stack_context_action)
        self.sidebar.add_server_requested.connect(self.add_server)
        self.sidebar.add_stack_requested.connect(self.add_stack)
        self.sidebar.settings_requested.connect(self.open_settings)
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
        self.tray_menu = QMenu()
        self.update_tray_menu()
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def update_tray_menu(self):
        """Update the tray menu (useful when settings change)"""
        self.tray_menu.clear()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        self.tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide Window", self)
        hide_action.triggered.connect(self.hide)
        self.tray_menu.addAction(hide_action)
        
        self.tray_menu.addSeparator()
        
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)
        self.tray_menu.addAction(settings_action)
        
        self.tray_menu.addSeparator()
        
        # Show current shortcut in menu
        shortcut_str = self.server_manager.settings.get("tray_shortcut", "Ctrl+Alt+S")
        shortcut_info = QAction(f"Shortcut: {shortcut_str}", self)
        shortcut_info.setEnabled(False)  # Make it non-clickable
        self.tray_menu.addAction(shortcut_info)
        
        self.tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(quit_action)
    
    def init_global_shortcut(self):
        """Initialize global keyboard shortcut to show/hide window"""
        if sys.platform != "win32":
            # Global shortcuts only supported on Windows for now
            return
        
        shortcut_str = self.server_manager.settings.get("tray_shortcut", "Ctrl+Alt+S")
        if self.register_global_shortcut(shortcut_str):
            # Install native event filter to catch hotkey messages
            self.shortcut_filter = GlobalShortcutFilter(self.toggle_window_from_tray)
            QApplication.instance().installNativeEventFilter(self.shortcut_filter)
    
    def parse_shortcut(self, shortcut_str: str) -> Optional[tuple]:
        """
        Parse shortcut string like "Ctrl+Alt+S" into (modifiers, vk_code)
        Returns (modifiers, vk_code) or None if invalid
        """
        if sys.platform != "win32":
            return None
        
        parts = shortcut_str.upper().split('+')
        modifiers = 0
        key = None
        
        for part in parts:
            part = part.strip()
            if part == "CTRL" or part == "CONTROL":
                modifiers |= MOD_CONTROL
            elif part == "ALT":
                modifiers |= MOD_ALT
            elif part == "SHIFT":
                modifiers |= MOD_SHIFT
            elif part == "WIN" or part == "WINDOWS":
                modifiers |= MOD_WIN
            else:
                # Assume it's the key
                if len(part) == 1:
                    # Single character key
                    key = ord(part)
                else:
                    # Named key - map common keys
                    key_map = {
                        "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
                        "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
                        "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
                        "SPACE": 0x20, "ENTER": 0x0D, "TAB": 0x09,
                        "ESC": 0x1B, "ESCAPE": 0x1B,
                    }
                    key = key_map.get(part)
                    if key is None:
                        return None
        
        if key is None:
            return None
        
        return (modifiers, key)
    
    def register_global_shortcut(self, shortcut_str: str) -> bool:
        """
        Register a global hotkey using Windows API
        Returns True if successful, False otherwise
        """
        if sys.platform != "win32":
            return False
        
        parsed = self.parse_shortcut(shortcut_str)
        if parsed is None:
            print(f"Invalid shortcut format: {shortcut_str}")
            return False
        
        modifiers, vk_code = parsed
        
        # Get user32.dll functions
        user32 = ctypes.windll.user32
        
        # Get window handle
        hwnd = int(self.winId())
        
        # Unregister existing hotkey if already registered
        user32.UnregisterHotKey(hwnd, self.hotkey_id)
        
        # Register the hotkey
        # RegisterHotKey(hwnd, id, modifiers, vk)
        result = user32.RegisterHotKey(hwnd, self.hotkey_id, modifiers, vk_code)
        
        if result == 0:
            error = ctypes.get_last_error()
            if error == 1409:  # ERROR_HOTKEY_ALREADY_REGISTERED
                print(f"Hotkey {shortcut_str} is already registered by another application")
            else:
                print(f"Failed to register hotkey {shortcut_str}: error {error}")
            return False
        
        return True
    
    def unregister_global_shortcut(self):
        """Unregister the global hotkey"""
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.UnregisterHotKey(hwnd, self.hotkey_id)
            except:
                pass
        if self.shortcut_filter:
            QApplication.instance().removeNativeEventFilter(self.shortcut_filter)
    
    def toggle_window_from_tray(self):
        """Toggle window visibility when shortcut is pressed"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Update tray menu to reflect any changes
            self.update_tray_menu()
    
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
        # Unregister global shortcut
        self.unregister_global_shortcut()
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
                    
                    # Check for detected port
                    detected_port = self.server_manager.get_detected_port(name)
                    if detected_port:
                        server_view.update_detected_port(detected_port)
            
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
            
        # Update StackDetailViews (they might contain this server)
        for view in self.stack_views.values():
            view.update_status()
    
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
            
        # Update StackDetailViews (they might contain this server)
        for view in self.stack_views.values():
            view.update_status()
        
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
            
        # Update StackDetailViews (they might contain this server)
        for view in self.stack_views.values():
            view.update_status()
        
        self.tray_icon.showMessage("Server Stopped", f"Server '{name}' has been stopped.")
    
    def on_server_log(self, name: str, log_line: str, is_error: bool):
        """Handle server log signal - save to persistent storage and forward to ServerDetailView if visible"""
        # Save log to persistent storage
        self.server_manager.save_log(name, log_line)
        # Forward to ServerDetailView if visible
        if name in self.server_views:
            self.server_views[name].append_log(log_line, is_error)
        # Try to detect port from new log (non-blocking, quick check)
        # Only check if we don't already have a detected port
        if name not in self.server_manager.detected_ports or self.server_manager.detected_ports[name] is None:
            self.server_manager.detect_port(name)
    
    def on_port_detected(self, name: str, port: int):
        """Handle port detection signal - update ServerDetailView if visible"""
        if name in self.server_views:
            self.server_views[name].update_detected_port(port)
    
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
                data.get("venv_path"),
                data.get("flaresolverr_type")
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
                venv_path,
                data.get("flaresolverr_type")
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

    # Stack Handlers
    
    def on_sidebar_stack_selected(self, name: str):
        """Handle sidebar stack selection - switch to stack view"""
        if name not in self.stack_views:
            # Create new stack detail view
            stack_view = StackDetailView(name, self)
            self.stack_views[name] = stack_view
            self.stacked_widget.addWidget(stack_view)
            
        # Switch to stack view
        self.stacked_widget.setCurrentWidget(self.stack_views[name])
        self.current_view = f"stack:{name}"
        
    def on_sidebar_stack_context_action(self, action: str, stack_name: str):
        """Handle context menu actions for stacks"""
        if action == "start":
            self.server_manager.start_stack(stack_name)
        elif action == "stop":
            self.server_manager.stop_stack(stack_name)
        elif action == "edit":
            self.edit_stack(stack_name)
        elif action == "remove":
            self.remove_stack(stack_name)
            
    def add_stack(self):
        """Add a new stack"""
        dialog = StackDialog(self, self.server_manager)
        if dialog.exec():
            data = dialog.get_data()
            if self.server_manager.add_stack(data["name"], data["servers"]):
                QMessageBox.information(self, "Success", "Stack added successfully.")
            else:
                QMessageBox.warning(self, "Error", "Stack name already exists.")
                
    def edit_stack(self, name: str):
        """Edit an existing stack"""
        dialog = StackDialog(self, self.server_manager, stack_name=name)
        if dialog.exec():
            data = dialog.get_data()
            if self.server_manager.update_stack(name, data["servers"]):
                QMessageBox.information(self, "Success", "Stack updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to update stack.")
                
    def remove_stack(self, name: str):
        """Remove a stack"""
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove stack '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.server_manager.remove_stack(name):
                # Remove view if exists
                if name in self.stack_views:
                    view = self.stack_views[name]
                    self.stacked_widget.removeWidget(view)
                    view.deleteLater()
                    del self.stack_views[name]
                
                # If this was the current view, switch to dashboard
                if self.current_view == f"stack:{name}":
                    self.sidebar.select_item("dashboard")
                
                QMessageBox.information(self, "Success", "Stack removed successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to remove stack.")
                
    def on_stack_changed(self):
        """Handle stack added/removed/updated"""
        self.sidebar.update_stack_list(self.server_manager.get_stacks())
        # Update any active stack views
        for view in self.stack_views.values():
            view.update_stack_info()
            



def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Don't quit when window is closed
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
