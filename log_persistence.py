"""
Log persistence module - saves and loads server logs to/from files
"""
import os
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone, timedelta


class LogPersistence:
    """Handles persistent storage of server logs"""
    
    def __init__(self, logs_dir: str = "logs"):
        """
        Initialize log persistence
        
        Args:
            logs_dir: Directory to store log files
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.locks = {}  # Per-server file locks
        self._lock = threading.Lock()  # Lock for managing locks dict
    
    def _get_log_file_path(self, server_name: str) -> Path:
        """Get the log file path for a server"""
        # Sanitize server name for filename
        safe_name = "".join(c for c in server_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return self.logs_dir / f"{safe_name}.log"
    
    def _get_lock(self, server_name: str) -> threading.Lock:
        """Get or create a lock for a server's log file"""
        with self._lock:
            if server_name not in self.locks:
                self.locks[server_name] = threading.Lock()
            return self.locks[server_name]
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in UTC+7 format"""
        utc_plus_7 = timezone(timedelta(hours=7))
        now = datetime.now(utc_plus_7)
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    def append_log(self, server_name: str, log_line: str):
        """
        Append a log line to the server's log file with timestamp
        
        Args:
            server_name: Name of the server
            log_line: Log line to append (without timestamp)
        """
        log_file = self._get_log_file_path(server_name)
        lock = self._get_lock(server_name)
        
        try:
            with lock:
                timestamp = self._get_timestamp()
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{timestamp} {log_line}\n")
        except Exception as e:
            print(f"Error writing log for {server_name}: {e}")
    
    def load_logs(self, server_name: str, max_lines: Optional[int] = None) -> list[str]:
        """
        Load logs from file for a server
        
        Args:
            server_name: Name of the server
            max_lines: Maximum number of lines to load (None = all)
        
        Returns:
            List of log lines (with timestamps if they were saved)
        """
        log_file = self._get_log_file_path(server_name)
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove trailing newlines
            lines = [line.rstrip('\n\r') for line in lines]
            
            # Return last N lines if max_lines is specified
            if max_lines is not None and len(lines) > max_lines:
                return lines[-max_lines:]
            
            return lines
        except Exception as e:
            print(f"Error reading log for {server_name}: {e}")
            return []
    
    def clear_logs(self, server_name: str):
        """
        Clear logs for a server
        
        Args:
            server_name: Name of the server
        """
        log_file = self._get_log_file_path(server_name)
        lock = self._get_lock(server_name)
        
        try:
            with lock:
                if log_file.exists():
                    log_file.unlink()
        except Exception as e:
            print(f"Error clearing log for {server_name}: {e}")
    
    def delete_logs(self, server_name: str):
        """Delete log file for a server (when server is removed)"""
        self.clear_logs(server_name)

