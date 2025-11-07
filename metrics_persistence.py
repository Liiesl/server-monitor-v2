"""
Metrics persistence module - saves and loads server metrics to/from files
"""
import os
import json
import threading
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta
import time


class MetricsPersistence:
    """Handles persistent storage of server metrics"""
    
    def __init__(self, metrics_dir: str = "metrics"):
        """
        Initialize metrics persistence
        
        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        self.locks = {}  # Per-server file locks
        self._lock = threading.Lock()  # Lock for managing locks dict
        self.max_age_seconds = 86400  # 24 hours
    
    def _get_metrics_file_path(self, server_name: str) -> Path:
        """Get the metrics file path for a server"""
        # Sanitize server name for filename
        safe_name = "".join(c for c in server_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return self.metrics_dir / f"{safe_name}.json"
    
    def _get_lock(self, server_name: str) -> threading.Lock:
        """Get or create a lock for a server's metrics file"""
        with self._lock:
            if server_name not in self.locks:
                self.locks[server_name] = threading.Lock()
            return self.locks[server_name]
    
    def append_metric(self, server_name: str, timestamp: float, cpu: float, ram: float):
        """
        Append a metric data point to the server's metrics file
        
        Args:
            server_name: Name of the server
            timestamp: Unix timestamp (float)
            cpu: CPU usage percentage
            ram: RAM usage in MB
        """
        metrics_file = self._get_metrics_file_path(server_name)
        lock = self._get_lock(server_name)
        
        try:
            with lock:
                # Load existing data
                metrics = []
                if metrics_file.exists():
                    try:
                        with open(metrics_file, 'r', encoding='utf-8') as f:
                            metrics = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        # File corrupted or empty, start fresh
                        metrics = []
                
                # Append new metric [timestamp, cpu, ram]
                metrics.append([timestamp, cpu, ram])
                
                # Cleanup old data periodically (every 100 records to avoid frequent rewrites)
                if len(metrics) % 100 == 0:
                    current_time = time.time()
                    cutoff_time = current_time - self.max_age_seconds
                    metrics = [m for m in metrics if m[0] >= cutoff_time]
                
                # Save back to file
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f)
        except Exception as e:
            print(f"Error writing metrics for {server_name}: {e}")
    
    def load_metrics(self, server_name: str, start_time: Optional[float] = None, 
                     end_time: Optional[float] = None) -> List[Tuple[float, float, float]]:
        """
        Load metrics from file for a server, optionally filtered by time range
        
        Args:
            server_name: Name of the server
            start_time: Optional start timestamp (inclusive)
            end_time: Optional end timestamp (inclusive)
        
        Returns:
            List of (timestamp, cpu, ram) tuples
        """
        metrics_file = self._get_metrics_file_path(server_name)
        
        if not metrics_file.exists():
            return []
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            # Convert from [[ts, cpu, ram], ...] to [(ts, cpu, ram), ...]
            result = [(m[0], m[1], m[2]) for m in metrics]
            
            # Filter by time range if specified
            if start_time is not None:
                result = [(ts, cpu, ram) for ts, cpu, ram in result if ts >= start_time]
            if end_time is not None:
                result = [(ts, cpu, ram) for ts, cpu, ram in result if ts <= end_time]
            
            return result
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading metrics for {server_name}: {e}")
            return []
    
    def cleanup_old_data(self, server_name: str, max_age_seconds: Optional[int] = None):
        """
        Remove data older than max_age_seconds (default 24 hours) for a server
        
        Args:
            server_name: Name of the server
            max_age_seconds: Maximum age in seconds (default: 24 hours)
        """
        if max_age_seconds is None:
            max_age_seconds = self.max_age_seconds
        
        metrics_file = self._get_metrics_file_path(server_name)
        lock = self._get_lock(server_name)
        
        if not metrics_file.exists():
            return
        
        try:
            with lock:
                # Load existing data
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                except (json.JSONDecodeError, IOError):
                    return
                
                # Filter out old data
                current_time = time.time()
                cutoff_time = current_time - max_age_seconds
                filtered_metrics = [m for m in metrics if m[0] >= cutoff_time]
                
                # Only rewrite if data was removed
                if len(filtered_metrics) < len(metrics):
                    with open(metrics_file, 'w', encoding='utf-8') as f:
                        json.dump(filtered_metrics, f)
        except Exception as e:
            print(f"Error cleaning up metrics for {server_name}: {e}")
    
    def delete_metrics(self, server_name: str):
        """
        Delete all metrics for a server (when server is removed)
        
        Args:
            server_name: Name of the server
        """
        metrics_file = self._get_metrics_file_path(server_name)
        lock = self._get_lock(server_name)
        
        try:
            with lock:
                if metrics_file.exists():
                    metrics_file.unlink()
        except Exception as e:
            print(f"Error deleting metrics for {server_name}: {e}")
    
    def cleanup_all_old_data(self, max_age_seconds: Optional[int] = None):
        """
        Cleanup old data for all servers in the metrics directory
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)
        """
        if max_age_seconds is None:
            max_age_seconds = self.max_age_seconds
        
        if not self.metrics_dir.exists():
            return
        
        # Get all JSON files in metrics directory
        for metrics_file in self.metrics_dir.glob("*.json"):
            # Extract server name from filename (reverse of sanitization)
            server_name = metrics_file.stem.replace('_', ' ')
            self.cleanup_old_data(server_name, max_age_seconds)

