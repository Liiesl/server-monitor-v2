"""
Server Manager - Handles Node.js and Flask server process management
Refactored to use ConfigManager and ServerInstance
"""
import time
from typing import Dict, Optional, List, Tuple
from PySide6.QtCore import QObject, Signal
from config_manager import ConfigManager
from server_instance import ServerInstance
from log_persistence import LogPersistence
from metrics_persistence import MetricsPersistence

class ServerManager(QObject):
    """Manages Node.js and Flask server processes"""
    
    # Signals
    server_status_changed = Signal(str, str)  # (server_name, status)
    server_metrics_changed = Signal(str, dict)  # (server_name, metrics_dict)
    server_started = Signal(str)  # server_name
    server_stopped = Signal(str)  # server_name
    server_log = Signal(str, str, bool)  # (server_name, log_line, is_error)
    port_detected = Signal(str, int)  # (server_name, port)
    
    def __init__(self, config_file: str = "servers.json", settings_file: str = "settings.json"):
        super().__init__()
        self.config_manager = ConfigManager(config_file, settings_file)
        self.instances: Dict[str, ServerInstance] = {}
        
        self.log_persistence = LogPersistence()
        self.metrics_persistence = MetricsPersistence()
        self.metrics_history: Dict[str, List[Tuple[float, float, float]]] = {}
        self.last_cleanup_time: Dict[str, float] = {}
        
        # Expose properties for backward compatibility/UI access
        self.settings = self.config_manager.settings
        self.servers = self.config_manager.servers
        self.psutil_processes = {} # Shim for UI access if needed, but better to remove dependency
        self.detected_ports = {} # Shim
        
        # Cleanup old data on startup
        self.metrics_persistence.cleanup_all_old_data()
    
    def save_settings(self):
        self.config_manager.save_settings()
        
    def load_settings(self):
        self.config_manager.load_settings()
        # Update reference
        self.settings = self.config_manager.settings

    @property
    def last_metrics(self):
        """Aggregate last metrics from all instances"""
        metrics = {}
        for name, instance in self.instances.items():
            if instance.last_metrics:
                metrics[name] = instance.last_metrics
        return metrics

    def record_server_metrics(self, name: str):
        """Record metrics for a specific server (called by MetricsMonitor)"""
        if name not in self.instances:
            return
            
        instance = self.instances[name]
        raw_metrics = instance.get_metrics()
        
        if raw_metrics:
            cpu, ram = raw_metrics
            self._record_metrics(name, cpu, ram)
    
    def add_server(self, *args, **kwargs):
        return self.config_manager.add_server(*args, **kwargs)
    
    def remove_server(self, name: str):
        if name in self.instances:
            self.stop_server(name)
        
        if self.config_manager.remove_server(name):
            self.log_persistence.delete_logs(name)
            self.metrics_persistence.delete_metrics(name)
            return True
        return False
    
    def update_server(self, *args, **kwargs):
        return self.config_manager.update_server(*args, **kwargs)
    
    def start_server(self, name: str) -> bool:
        if name not in self.servers:
            return False
        
        if name in self.instances:
            if self.instances[name].process:
                return False # Already running
        
        instance = ServerInstance(name, self.servers[name], self.settings)
        
        # Connect signals
        instance.status_changed.connect(lambda s: self._on_status_changed(name, s))
        instance.log_received.connect(lambda l, e: self._on_log_received(name, l, e))
        instance.port_detected.connect(lambda p: self._on_port_detected(name, p))
        
        if instance.start():
            self.instances[name] = instance
            # Shim for psutil_processes
            if instance.psutil_process:
                self.psutil_processes[name] = instance.psutil_process
            
            self.server_started.emit(name)
            return True
        return False
    
    def stop_server(self, name: str) -> bool:
        if name in self.instances:
            instance = self.instances[name]
            if instance.stop():
                del self.instances[name]
                if name in self.psutil_processes:
                    del self.psutil_processes[name]
                self.server_stopped.emit(name)
                return True
        return False
    
    def restart_server(self, name: str) -> bool:
        self.stop_server(name)
        return self.start_server(name)
    
    def get_server_status(self, name: str) -> str:
        if name in self.instances:
            # Check if process is still alive
            instance = self.instances[name]
            if instance.process and instance.process.poll() is not None:
                # Died
                self.stop_server(name)
                return "stopped"
            return "running"
        return self.servers.get(name, {}).get("status", "stopped")
    
    def get_server_metrics(self, name: str) -> Optional[Dict]:
        if name not in self.instances:
            return None
            
        instance = self.instances[name]
        raw_metrics = instance.get_metrics()
        
        if raw_metrics:
            cpu, ram = raw_metrics
            # Record metrics logic (simplified from original)
            self._record_metrics(name, cpu, ram)
            
            # Check if changed significantly (logic from original)
            last = instance.last_metrics
            if (not last or 
                abs(cpu - last.get("cpu_percent", 0)) >= 0.1 or 
                abs(ram - last.get("memory_mb", 0)) >= 1.0):
                
                metrics = {"cpu_percent": cpu, "memory_mb": ram}
                instance.last_metrics = metrics
                self.server_metrics_changed.emit(name, metrics)
                return metrics
        
        return None

    def _record_metrics(self, name, cpu, ram):
        current_time = time.time()
        self.metrics_persistence.append_metric(name, current_time, cpu, ram)
        
        if name not in self.metrics_history:
            self.metrics_history[name] = []
        
        self.metrics_history[name].append((current_time, cpu, ram))
        
        # Prune memory history (1 hour)
        cutoff = current_time - 3600
        self.metrics_history[name] = [x for x in self.metrics_history[name] if x[0] >= cutoff]
        
        # Cleanup persistence (every 5 mins)
        if name not in self.last_cleanup_time or (current_time - self.last_cleanup_time[name]) >= 300:
            self.metrics_persistence.cleanup_old_data(name)
            self.last_cleanup_time[name] = current_time

    def get_all_servers(self) -> Dict:
        # Update status check
        for name in list(self.instances.keys()):
            self.get_server_status(name)
        return self.servers
        
    def stop_all_servers(self):
        for name in list(self.instances.keys()):
            self.stop_server(name)

    def save_log(self, server_name: str, log_line: str):
        self.log_persistence.append_log(server_name, log_line)
        
    def load_logs(self, server_name: str, max_lines: Optional[int] = None) -> list:
        return self.log_persistence.load_logs(server_name, max_lines)
        
    def clear_logs(self, server_name: str):
        self.log_persistence.clear_logs(server_name)

    def get_metrics_history(self, server_name: Optional[str] = None, time_range_seconds: Optional[float] = None):
        # Re-implement logic using self.metrics_history and persistence
        # This is largely same as before, just using self.metrics_history which we populate in _record_metrics
        current_time = time.time()
        start_time = current_time - time_range_seconds if time_range_seconds else None
        
        result = {}
        names = [server_name] if server_name else list(self.servers.keys())
        
        for name in names:
            in_memory = self.metrics_history.get(name, [])
            
            if time_range_seconds is None or time_range_seconds > 3600:
                persisted = self.metrics_persistence.load_metrics(name, start_time=start_time)
                # Merge
                data_map = {ts: (ts, c, r) for ts, c, r in persisted}
                for item in in_memory:
                    data_map[item[0]] = item
                
                result[name] = sorted(data_map.values())
            else:
                if start_time:
                    result[name] = [x for x in in_memory if x[0] >= start_time]
                else:
                    result[name] = in_memory
                    
        return result if not server_name else {server_name: result.get(server_name, [])}

    def get_detected_port(self, name: str) -> Optional[int]:
        return self.detected_ports.get(name)
        
    def detect_port(self, name: str):
        if name in self.instances:
            self.instances[name].detect_port()

    # Signal handlers
    def _on_status_changed(self, name, status):
        self.servers[name]["status"] = status
        self.config_manager.save_config()
        self.server_status_changed.emit(name, status)
        
    def _on_log_received(self, name, line, is_error):
        self.server_log.emit(name, line, is_error)
        
    def _on_port_detected(self, name, port):
        self.detected_ports[name] = port
        self.port_detected.emit(name, port)
