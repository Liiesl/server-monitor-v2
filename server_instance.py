import subprocess
import os
import time
import psutil
import re
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from ui.log_reader import LogReaderThread

class ServerInstance(QObject):
    """Represents a single running server instance"""
    
    # Signals
    status_changed = Signal(str)  # status
    log_received = Signal(str, bool)  # log_line, is_error
    metrics_updated = Signal(dict)  # metrics_dict
    port_detected = Signal(int)  # port
    
    def __init__(self, name: str, config: Dict, settings: Dict):
        super().__init__()
        self.name = name
        self.config = config
        self.settings = settings
        self.process: Optional[subprocess.Popen] = None
        self.psutil_process: Optional[psutil.Process] = None
        self.log_reader: Optional[LogReaderThread] = None
        self.cpu_history: List[float] = []
        self.last_metrics: Dict = {}
        self.detected_port: Optional[int] = None
        
    def start(self) -> bool:
        """Start the server process"""
        if self.process:
            return False
            
        server_path = self.config["path"]
        if not os.path.exists(server_path):
            return False
            
        try:
            cmd = self._build_command()
            if not cmd:
                return False
                
            cwd = os.path.dirname(server_path) if os.path.isfile(server_path) else server_path
            
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wrap with psutil
            try:
                self.psutil_process = psutil.Process(self.process.pid)
                self.psutil_process.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
            # Start log reader
            self.log_reader = LogReaderThread(self.name, self.process, self)
            # LogReaderThread takes 'manager' and calls 'manager.server_log.emit'.
            # We pass 'self' as the manager.
            
            self.log_reader.start()
            
            self.config["status"] = "running"
            self.config["started_at"] = datetime.now().isoformat()
            
            self.status_changed.emit("running")
            self.detect_port()
            
            return True
        except Exception as e:
            print(f"Error starting server {self.name}: {e}")
            return False

    # Shim for LogReaderThread
    class _SignalShim:
        def __init__(self, callback):
            self.callback = callback
        def emit(self, name, line, is_error):
            self.callback(line, is_error)

    @property
    def server_log(self):
        return self._SignalShim(self._on_log_received)

    def _on_log_received(self, line, is_error):
        self.log_received.emit(line, is_error)
        # Try to detect port from logs
        if not self.detected_port:
            self._detect_port_from_log(line)

    def stop(self) -> bool:
        """Stop the server process"""
        if not self.process:
            return False
            
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
            self.process = None
            self.psutil_process = None
            
            if self.log_reader:
                self.log_reader.stop()
                self.log_reader = None
                
            self.config["status"] = "stopped"
            if "started_at" in self.config:
                del self.config["started_at"]
                
            self.status_changed.emit("stopped")
            return True
        except Exception as e:
            print(f"Error stopping server {self.name}: {e}")
            return False

    def _build_command(self) -> Optional[List[str]]:
        """Build the command line arguments based on server type"""
        server_type = self.config.get("server_type", "nodejs")
        server_path = self.config["path"]
        
        if server_type == "flask":
            venv_path = self.config.get("venv_path")
            python_cmd = self.config.get("python_command") or self.settings.get("python_command", "python")
            
            if venv_path:
                server_dir = os.path.dirname(server_path) if os.path.isfile(server_path) else server_path
                if not os.path.isabs(venv_path):
                    venv_path = os.path.join(server_dir, venv_path)
                
                if os.name == 'nt':
                    python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                    if not os.path.exists(python_exe):
                        python_exe = os.path.join(venv_path, "python.exe")
                else:
                    python_exe = os.path.join(venv_path, "bin", "python")
                
                if os.path.exists(python_exe):
                    python_cmd = python_exe
            
            cmd = [python_cmd, server_path]
            if self.config.get("args"):
                cmd.extend(self.config["args"].split())
            return cmd
            
        elif server_type == "flaresolverr":
            flaresolverr_type = self.config.get("flaresolverr_type", "source")
            if flaresolverr_type == "source":
                python_cmd = self.config.get("python_command") or self.settings.get("python_command", "python")
                script_path = os.path.join(server_path, "src", "flaresolverr.py")
                if not os.path.exists(script_path):
                    return None
                cmd = [python_cmd, script_path]
            else:
                cmd = [server_path]
            
            if self.config.get("args"):
                cmd.extend(self.config["args"].split())
            return cmd
            
        else: # nodejs
            cmd = [self.config.get("command", "node")]
            if self.config.get("args"):
                cmd.extend(self.config["args"].split())
            cmd.append(server_path)
            return cmd

    def get_metrics(self) -> Optional[Tuple[float, float]]:
        """Get current metrics (cpu, ram). Returns raw values."""
        if not self.psutil_process or not self.psutil_process.is_running():
            if self.process: # Process died unexpectedly
                self.stop()
            return None
            
        try:
            raw_cpu = self.psutil_process.cpu_percent(interval=None)
            
            self.cpu_history.append(raw_cpu)
            if len(self.cpu_history) > 5:
                self.cpu_history.pop(0)
            
            smoothed_cpu = sum(self.cpu_history) / len(self.cpu_history)
            
            memory_info = self.psutil_process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            return (smoothed_cpu, memory_mb)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            self.stop()
            return None

    def detect_port(self):
        """Attempt to detect port"""
        # 1. Configured port
        configured_port = self.config.get("port")
        if configured_port:
            self._set_detected_port(configured_port)
            return

        # 2. Psutil connections
        if self.psutil_process:
            try:
                for conn in self.psutil_process.connections(kind='inet'):
                    if conn.status == psutil.CONN_LISTEN:
                        port = conn.laddr.port
                        if port >= 1024:
                            self._set_detected_port(port)
                            return
            except:
                pass

    def _detect_port_from_log(self, line: str):
        """Parse log line for port"""
        port_patterns = [
            r'(?:listening|running|started|bound).*?(?:on|at).*?port\s+(\d+)',
            r'(?:listening|running|started|bound).*?port\s+(\d+)',
            r'http://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::\]):(\d+)',
            r'https://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::\]):(\d+)',
            r'(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d+)(?:\s|$|/|\?|,)',
        ]
        
        for pattern in port_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    port = int(match.group(1))
                    if 1024 <= port <= 65535:
                        self._set_detected_port(port)
                        return
                except:
                    continue

    def _set_detected_port(self, port: int):
        if self.detected_port != port:
            self.detected_port = port
            self.port_detected.emit(port)
