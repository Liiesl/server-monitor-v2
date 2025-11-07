"""
Server Manager - Handles Node.js server process management
"""
import subprocess
import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import psutil
import time
from PySide6.QtCore import QObject, Signal
from ui.log_reader import LogReaderThread
from log_persistence import LogPersistence
from metrics_persistence import MetricsPersistence


class ServerManager(QObject):
    """Manages Node.js server processes"""
    
    # Signals
    server_status_changed = Signal(str, str)  # (server_name, status)
    server_metrics_changed = Signal(str, dict)  # (server_name, metrics_dict)
    server_started = Signal(str)  # server_name
    server_stopped = Signal(str)  # server_name
    server_log = Signal(str, str, bool)  # (server_name, log_line, is_error)
    
    def __init__(self, config_file: str = "servers.json"):
        super().__init__()
        self.config_file = config_file
        self.servers: Dict[str, Dict] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.psutil_processes: Dict[str, psutil.Process] = {}
        self.last_metrics: Dict[str, dict] = {}
        self.cpu_history: Dict[str, list] = {}  # Moving average for CPU smoothing
        self.metrics_history: Dict[str, List[Tuple[float, float, float]]] = {}  # (timestamp, cpu, ram) for graphs
        self.log_readers: Dict[str, LogReaderThread] = {}  # Log reader threads
        self.log_persistence = LogPersistence()  # Log persistence handler
        self.metrics_persistence = MetricsPersistence()  # Metrics persistence handler
        self.last_cleanup_time: Dict[str, float] = {}  # Track last cleanup time per server
        self.load_config()
        # Cleanup old data on startup
        self.metrics_persistence.cleanup_all_old_data()
    
    def load_config(self):
        """Load server configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.servers = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.servers = {}
        else:
            self.servers = {}
    
    def save_config(self):
        """Save server configurations to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.servers, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_server(self, name: str, path: str, command: str = "node", args: str = "", port: Optional[int] = None):
        """Add a new server configuration"""
        if name in self.servers:
            return False
        
        self.servers[name] = {
            "path": path,
            "command": command,
            "args": args,
            "port": port,
            "status": "stopped",
            "created_at": datetime.now().isoformat()
        }
        self.save_config()
        return True
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            if name in self.processes:
                self.stop_server(name)
            del self.servers[name]
            # Delete log file when server is removed
            self.log_persistence.delete_logs(name)
            # Delete metrics when server is removed
            self.metrics_persistence.delete_metrics(name)
            self.save_config()
            return True
        return False
    
    def update_server(self, name: str, path: str = None, command: str = None, args: str = None, port: int = None):
        """Update server configuration"""
        if name not in self.servers:
            return False
        
        if path is not None:
            self.servers[name]["path"] = path
        if command is not None:
            self.servers[name]["command"] = command
        if args is not None:
            self.servers[name]["args"] = args
        if port is not None:
            self.servers[name]["port"] = port
        
        self.save_config()
        return True
    
    def start_server(self, name: str) -> bool:
        """Start a Node.js server"""
        if name not in self.servers:
            return False
        
        if name in self.processes:
            # Server already running
            return False
        
        server_config = self.servers[name]
        server_path = server_config["path"]
        
        if not os.path.exists(server_path):
            return False
        
        try:
            # Build command
            cmd = [server_config["command"]]
            if server_config.get("args"):
                cmd.extend(server_config["args"].split())
            cmd.append(server_path)
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(server_path) if os.path.isfile(server_path) else server_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.processes[name] = process
            # Wrap with psutil for metrics
            try:
                psutil_proc = psutil.Process(process.pid)
                self.psutil_processes[name] = psutil_proc
                # Initialize CPU percent (required for first call)
                psutil_proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            # Start log reader thread
            log_reader = LogReaderThread(name, process, self)
            log_reader.start()
            self.log_readers[name] = log_reader
            
            self.servers[name]["status"] = "running"
            self.servers[name]["started_at"] = datetime.now().isoformat()
            self.save_config()
            
            # Emit signals
            self.server_started.emit(name)
            self.server_status_changed.emit(name, "running")
            
            return True
        except Exception as e:
            print(f"Error starting server {name}: {e}")
            return False
    
    def stop_server(self, name: str) -> bool:
        """Stop a Node.js server"""
        if name not in self.processes:
            return False
        
        try:
            process = self.processes[name]
            process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            del self.processes[name]
            
            # Stop and clean up log reader thread
            if name in self.log_readers:
                self.log_readers[name].stop()
                del self.log_readers[name]
            
            # Clean up psutil tracking
            if name in self.psutil_processes:
                del self.psutil_processes[name]
            if name in self.last_metrics:
                del self.last_metrics[name]
            if name in self.cpu_history:
                del self.cpu_history[name]
            if name in self.metrics_history:
                del self.metrics_history[name]
            
            self.servers[name]["status"] = "stopped"
            if "started_at" in self.servers[name]:
                del self.servers[name]["started_at"]
            self.save_config()
            
            # Emit signals
            self.server_stopped.emit(name)
            self.server_status_changed.emit(name, "stopped")
            
            return True
        except Exception as e:
            print(f"Error stopping server {name}: {e}")
            return False
    
    def restart_server(self, name: str) -> bool:
        """Restart a Node.js server"""
        if name in self.processes:
            self.stop_server(name)
        return self.start_server(name)
    
    def get_server_status(self, name: str) -> str:
        """Get the status of a server"""
        if name not in self.servers:
            return "not_found"
        
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                status = "running"
            else:
                # Process has ended
                del self.processes[name]
                # Stop and clean up log reader thread
                if name in self.log_readers:
                    self.log_readers[name].stop()
                    del self.log_readers[name]
                # Clean up psutil tracking
                if name in self.psutil_processes:
                    del self.psutil_processes[name]
                if name in self.last_metrics:
                    del self.last_metrics[name]
                if name in self.cpu_history:
                    del self.cpu_history[name]
                if name in self.metrics_history:
                    del self.metrics_history[name]
                self.servers[name]["status"] = "stopped"
                status = "stopped"
        else:
            status = self.servers[name].get("status", "stopped")
        
        # Emit signal if status changed
        if self.servers[name].get("status") != status:
            self.servers[name]["status"] = status
            self.server_status_changed.emit(name, status)
        
        return status
    
    def _get_raw_metrics(self, name: str) -> Optional[Tuple[float, float]]:
        """Get raw CPU and RAM metrics for a server. Returns (cpu_percent, memory_mb) or None"""
        if name not in self.psutil_processes:
            return None
        
        try:
            proc = self.psutil_processes[name]
            
            # Check if process is still running
            if not proc.is_running():
                # Process died, clean up
                if name in self.processes:
                    del self.processes[name]
                # Stop and clean up log reader thread
                if name in self.log_readers:
                    self.log_readers[name].stop()
                    del self.log_readers[name]
                del self.psutil_processes[name]
                if name in self.last_metrics:
                    del self.last_metrics[name]
                if name in self.cpu_history:
                    del self.cpu_history[name]
                if name in self.metrics_history:
                    del self.metrics_history[name]
                self.servers[name]["status"] = "stopped"
                self.server_status_changed.emit(name, "stopped")
                return None
            
            # Get CPU percent (non-blocking)
            raw_cpu = proc.cpu_percent(interval=None)
            
            # Smooth CPU using moving average (keep last 5 values)
            if name not in self.cpu_history:
                self.cpu_history[name] = []
            
            cpu_history = self.cpu_history[name]
            cpu_history.append(raw_cpu)
            if len(cpu_history) > 5:
                cpu_history.pop(0)  # Keep only last 5 values
            
            # Calculate smoothed CPU (average of last 5 values)
            smoothed_cpu = sum(cpu_history) / len(cpu_history)
            
            # Get memory in MB
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            return (smoothed_cpu, memory_mb)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process died or access denied, clean up
            if name in self.processes:
                del self.processes[name]
            # Stop and clean up log reader thread
            if name in self.log_readers:
                self.log_readers[name].stop()
                del self.log_readers[name]
            if name in self.psutil_processes:
                del self.psutil_processes[name]
            if name in self.last_metrics:
                del self.last_metrics[name]
            if name in self.cpu_history:
                del self.cpu_history[name]
            if name in self.metrics_history:
                del self.metrics_history[name]
            self.servers[name]["status"] = "stopped"
            self.server_status_changed.emit(name, "stopped")
            return None
    
    def record_server_metrics(self, name: str):
        """Record server metrics to history every second, regardless of change"""
        raw_metrics = self._get_raw_metrics(name)
        if raw_metrics is None:
            return
        
        smoothed_cpu, memory_mb = raw_metrics
        current_time = time.time()
        
        # Save to persistent storage
        self.metrics_persistence.append_metric(name, current_time, smoothed_cpu, memory_mb)
        
        # Always store in history for graphs (keep last 1 hour = 3600 seconds in memory for performance)
        if name not in self.metrics_history:
            self.metrics_history[name] = []
        
        self.metrics_history[name].append((current_time, smoothed_cpu, memory_mb))
        
        # Keep only last 1 hour of data in memory (3600 seconds)
        cutoff_time = current_time - 3600
        self.metrics_history[name] = [
            (ts, cpu, ram) for ts, cpu, ram in self.metrics_history[name]
            if ts >= cutoff_time
        ]
        
        # Periodic cleanup of old data (every 5 minutes = 300 seconds)
        if name not in self.last_cleanup_time or (current_time - self.last_cleanup_time[name]) >= 300:
            self.metrics_persistence.cleanup_old_data(name)
            self.last_cleanup_time[name] = current_time
    
    def get_server_metrics(self, name: str) -> Optional[Dict]:
        """Get server metrics (CPU, RAM) - only returns if values changed (event-driven)"""
        raw_metrics = self._get_raw_metrics(name)
        if raw_metrics is None:
            return None
        
        smoothed_cpu, memory_mb = raw_metrics
        
        # Get cached values for comparison
        last_metrics = self.last_metrics.get(name, {})
        last_cpu = last_metrics.get("cpu_percent")
        last_memory = last_metrics.get("memory_mb")
        
        # Only update if change is significant (0.1% for CPU, 1MB for memory)
        cpu_changed = last_cpu is None or abs(smoothed_cpu - last_cpu) >= 0.1
        memory_changed = last_memory is None or abs(memory_mb - last_memory) >= 1.0
        
        # Only return metrics if values changed significantly (event-driven!)
        if cpu_changed or memory_changed:
            metrics = {
                "cpu_percent": smoothed_cpu,
                "memory_mb": memory_mb
            }
            # Cache the new values
            self.last_metrics[name] = metrics
            return metrics
        
        return None  # No change, don't update
    
    def get_all_servers(self) -> Dict:
        """Get all server configurations"""
        # Update status for all servers
        for name in list(self.servers.keys()):
            self.get_server_status(name)
        return self.servers
    
    def stop_all_servers(self):
        """Stop all running servers"""
        for name in list(self.processes.keys()):
            self.stop_server(name)
        
        # Ensure all log readers are stopped
        for name in list(self.log_readers.keys()):
            self.log_readers[name].stop()
            del self.log_readers[name]
    
    def save_log(self, server_name: str, log_line: str):
        """Save a log line to persistent storage"""
        self.log_persistence.append_log(server_name, log_line)
    
    def load_logs(self, server_name: str, max_lines: Optional[int] = None) -> list:
        """Load logs from persistent storage"""
        return self.log_persistence.load_logs(server_name, max_lines)
    
    def clear_logs(self, server_name: str):
        """Clear logs for a server"""
        self.log_persistence.clear_logs(server_name)
    
    def get_metrics_history(self, server_name: Optional[str] = None, 
                           time_range_seconds: Optional[float] = None) -> Dict[str, List[Tuple[float, float, float]]]:
        """
        Get metrics history for graph display
        
        Args:
            server_name: If provided, return history for that server only.
                        If None, return history for all servers.
            time_range_seconds: Optional time range in seconds. If provided, only return
                               data within this range from current time.
        
        Returns:
            Dict mapping server names to list of (timestamp, cpu_percent, memory_mb) tuples
        """
        current_time = time.time()
        start_time = None
        if time_range_seconds is not None:
            start_time = current_time - time_range_seconds
        
        if server_name:
            # Get in-memory data
            in_memory_data = self.metrics_history.get(server_name, [])
            
            # If time range exceeds in-memory window (1 hour), load from persistence
            if time_range_seconds is None or time_range_seconds > 3600:
                persisted_data = self.metrics_persistence.load_metrics(server_name, start_time=start_time)
                
                # Merge in-memory and persisted data, removing duplicates
                all_data = {}
                for ts, cpu, ram in persisted_data:
                    all_data[ts] = (ts, cpu, ram)
                for ts, cpu, ram in in_memory_data:
                    all_data[ts] = (ts, cpu, ram)
                
                # Sort by timestamp
                result = sorted(all_data.values())
            else:
                # Only use in-memory data for short time ranges
                if start_time is not None:
                    result = [(ts, cpu, ram) for ts, cpu, ram in in_memory_data if ts >= start_time]
                else:
                    result = in_memory_data
            
            return {server_name: result}
        
        # Return data for all servers
        result = {}
        server_names = list(self.servers.keys())
        for name in server_names:
            # Get in-memory data
            in_memory_data = self.metrics_history.get(name, [])
            
            # If time range exceeds in-memory window (1 hour), load from persistence
            if time_range_seconds is None or time_range_seconds > 3600:
                persisted_data = self.metrics_persistence.load_metrics(name, start_time=start_time)
                
                # Merge in-memory and persisted data, removing duplicates
                all_data = {}
                for ts, cpu, ram in persisted_data:
                    all_data[ts] = (ts, cpu, ram)
                for ts, cpu, ram in in_memory_data:
                    all_data[ts] = (ts, cpu, ram)
                
                # Sort by timestamp
                result[name] = sorted(all_data.values())
            else:
                # Only use in-memory data for short time ranges
                if start_time is not None:
                    result[name] = [(ts, cpu, ram) for ts, cpu, ram in in_memory_data if ts >= start_time]
                else:
                    result[name] = in_memory_data
        
        return result

