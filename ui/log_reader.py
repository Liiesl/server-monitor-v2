"""
Background thread that reads server process logs
"""
from PySide6.QtCore import QThread, QObject, Signal
import subprocess
import sys


class LogReaderThread(QThread):
    """Background thread that reads from process stdout/stderr and emits log signals"""
    
    def __init__(self, server_name: str, process: subprocess.Popen, server_manager: QObject):
        super().__init__()
        self.server_name = server_name
        self.process = process
        self.server_manager = server_manager
        self.running = False
    
    def run(self):
        """Main log reading loop"""
        self.running = True
        
        # Use select for non-blocking reads (works on Unix)
        # On Windows, we'll use a different approach
        if sys.platform == 'win32':
            self._read_windows()
        else:
            self._read_unix()
    
    def _read_windows(self):
        """Read logs on Windows (using threading for non-blocking reads)"""
        import time
        import threading
        
        stdout_buffer = b''
        stderr_buffer = b''
        stdout_lock = threading.Lock()
        stderr_lock = threading.Lock()
        stdout_done = False
        stderr_done = False
        
        def read_stdout():
            nonlocal stdout_buffer, stdout_done
            try:
                while self.running and self.process.poll() is None:
                    try:
                        # readline() will block, but that's okay in a separate thread
                        line = self.process.stdout.readline()
                        if line:
                            with stdout_lock:
                                stdout_buffer += line
                        else:
                            # EOF
                            break
                    except (OSError, ValueError, AttributeError):
                        break
            except Exception:
                pass
            finally:
                stdout_done = True
        
        def read_stderr():
            nonlocal stderr_buffer, stderr_done
            try:
                while self.running and self.process.poll() is None:
                    try:
                        line = self.process.stderr.readline()
                        if line:
                            with stderr_lock:
                                stderr_buffer += line
                        else:
                            # EOF
                            break
                    except (OSError, ValueError, AttributeError):
                        break
            except Exception:
                pass
            finally:
                stderr_done = True
        
        # Start reader threads
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        # Process buffers in main thread
        while self.running and (self.process.poll() is None or not (stdout_done and stderr_done)):
            try:
                # Process stdout buffer
                with stdout_lock:
                    while b'\n' in stdout_buffer:
                        line, stdout_buffer = stdout_buffer.split(b'\n', 1)
                        if line:
                            log_line = line.decode('utf-8', errors='replace').rstrip()
                            if log_line:
                                # stdout is not an error
                                self.server_manager.server_log.emit(self.server_name, log_line, False)
                
                # Process stderr buffer
                with stderr_lock:
                    while b'\n' in stderr_buffer:
                        line, stderr_buffer = stderr_buffer.split(b'\n', 1)
                        if line:
                            log_line = line.decode('utf-8', errors='replace').rstrip()
                            if log_line:
                                # stderr is an error
                                self.server_manager.server_log.emit(self.server_name, log_line, True)
                
                time.sleep(0.05)
            except Exception:
                if not self.running:
                    break
        
        # Process any remaining data in buffers
        with stdout_lock:
            if stdout_buffer:
                log_line = stdout_buffer.decode('utf-8', errors='replace').rstrip()
                if log_line:
                    self.server_manager.server_log.emit(self.server_name, log_line, False)
        with stderr_lock:
            if stderr_buffer:
                log_line = stderr_buffer.decode('utf-8', errors='replace').rstrip()
                if log_line:
                    self.server_manager.server_log.emit(self.server_name, log_line, True)
    
    def _read_unix(self):
        """Read logs on Unix/Linux/Mac (using select)"""
        import select
        import time
        
        while self.running and self.process.poll() is None:
            try:
                # Use select to check if data is available
                if self.process.stdout and self.process.stderr:
                    ready, _, _ = select.select(
                        [self.process.stdout, self.process.stderr],
                        [],
                        [],
                        0.1  # timeout
                    )
                    
                    for stream in ready:
                        line = stream.readline()
                        if line:
                            log_line = line.decode('utf-8', errors='replace').rstrip()
                            if log_line:
                                # Check if it's stderr (error) or stdout (normal)
                                is_error = (stream == self.process.stderr)
                                self.server_manager.server_log.emit(self.server_name, log_line, is_error)
                else:
                    time.sleep(0.1)
            except Exception as e:
                if self.running:
                    break
    
    def stop(self):
        """Stop the log reading thread"""
        self.running = False
        self.wait()  # Wait for thread to finish

