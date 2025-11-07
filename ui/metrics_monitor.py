"""
Background thread that monitors server metrics
"""
from PySide6.QtCore import QThread
from server_manager import ServerManager
import time


class MetricsMonitor(QThread):
    """Background thread that monitors server metrics and emits signals when values change"""
    
    def __init__(self, server_manager: ServerManager):
        super().__init__()
        self.server_manager = server_manager
        self.running = False
    
    def run(self):
        """Main monitoring loop"""
        self.running = True
        last_record_time = {}  # Track when we last recorded metrics for each server
        
        while self.running:
            current_time = time.time()
            
            # Iterate through all psutil processes
            for name in list(self.server_manager.psutil_processes.keys()):
                if not self.running:
                    break
                
                # Record metrics to history every second (for graphs)
                if name not in last_record_time or (current_time - last_record_time[name]) >= 1.0:
                    self.server_manager.record_server_metrics(name)
                    last_record_time[name] = current_time
                
                # Get metrics (only returns if changed) - for UI updates
                metrics = self.server_manager.get_server_metrics(name)
                if metrics:
                    # Emit signal via server_manager
                    self.server_manager.server_metrics_changed.emit(name, metrics)
            
            # Sleep 200ms between checks
            time.sleep(0.2)
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        self.wait()  # Wait for thread to finish

