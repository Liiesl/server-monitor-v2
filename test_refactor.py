import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
import json
import time
from server_manager import ServerManager
from config_manager import ConfigManager
from server_instance import ServerInstance

class TestRefactoredServerManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data_refactor"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        self.config_file = os.path.join(self.test_dir, "servers.json")
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        
        # Create dummy settings
        with open(self.settings_file, 'w') as f:
            json.dump({"python_command": "python"}, f)
            
        self.manager = ServerManager(config_file=self.config_file, settings_file=self.settings_file)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_config_manager_integration(self):
        """Test that ServerManager correctly delegates to ConfigManager"""
        name = "TestServer"
        path = os.path.join(self.test_dir, "server.js")
        
        # Add server via manager
        result = self.manager.add_server(name, path)
        self.assertTrue(result)
        
        # Verify it's in config manager
        self.assertIn(name, self.manager.config_manager.servers)
        self.assertEqual(self.manager.config_manager.servers[name]["path"], path)
        
        # Verify it's exposed via manager property
        self.assertIn(name, self.manager.servers)
        
        # Update server
        self.manager.update_server(name, port=3000)
        self.assertEqual(self.manager.servers[name]["port"], 3000)
        
        # Remove server
        self.manager.remove_server(name)
        self.assertNotIn(name, self.manager.servers)

    def test_server_instance_creation(self):
        """Test that ServerManager creates ServerInstance correctly"""
        name = "TestInstance"
        path = os.path.join(self.test_dir, "server.js")
        # Create dummy file
        with open(path, 'w') as f:
            f.write("console.log('hello')")
            
        self.manager.add_server(name, path)
        
        # Mock subprocess to avoid actual execution
        with patch("subprocess.Popen") as mock_popen, \
             patch("psutil.Process"), \
             patch("ui.log_reader.LogReaderThread"):
            
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            # Fix: Mock readline to return bytes
            mock_process.stdout.readline.return_value = b""
            mock_process.stderr.readline.return_value = b""
            mock_popen.return_value = mock_process
            
            # Start server
            result = self.manager.start_server(name)
            self.assertTrue(result)
            
            # Verify instance created
            self.assertIn(name, self.manager.instances)
            self.assertIsInstance(self.manager.instances[name], ServerInstance)
            self.assertEqual(self.manager.instances[name].name, name)
            
            # Verify status
            self.assertEqual(self.manager.get_server_status(name), "running")
            
            # Stop server
            self.manager.stop_server(name)
            self.assertNotIn(name, self.manager.instances)
            self.assertEqual(self.manager.get_server_status(name), "stopped")

    def test_settings_delegation(self):
        """Test that settings methods are delegated correctly"""
        # Modify settings via manager
        self.manager.settings["python_command"] = "python3"
        self.manager.save_settings()
        
        # Verify file updated
        with open(self.settings_file, 'r') as f:
            saved = json.load(f)
        self.assertEqual(saved["python_command"], "python3")
        
        # Modify file directly
        with open(self.settings_file, 'w') as f:
            json.dump({"python_command": "py"}, f)
            
        # Load settings
        self.manager.load_settings()
        self.assertEqual(self.manager.settings["python_command"], "py")

    def test_flaresolverr_config(self):
        """Test FlareSolverr configuration with new structure"""
        name = "FlareTest"
        path = "C:/fake/path"
        
        self.manager.add_server(
            name=name, 
            path=path, 
            server_type="flaresolverr",
            flaresolverr_type="binary"
        )
        
        config = self.manager.servers[name]
        self.assertEqual(config["server_type"], "flaresolverr")
        self.assertEqual(config["flaresolverr_type"], "binary")

    def test_compatibility_methods(self):
        """Test backward compatibility methods (last_metrics, record_server_metrics)"""
        name = "CompatTest"
        path = os.path.join(self.test_dir, "server.js")
        with open(path, 'w') as f:
            f.write("console.log('hello')")
            
        self.manager.add_server(name, path)
        
        with patch("subprocess.Popen") as mock_popen, \
             patch("psutil.Process") as mock_psutil:
            
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_process.stdout.readline.return_value = b""
            mock_process.stderr.readline.return_value = b""
            mock_popen.return_value = mock_process
            
            # Mock psutil process for metrics
            mock_psutil_instance = MagicMock()
            mock_psutil_instance.is_running.return_value = True
            mock_psutil_instance.cpu_percent.return_value = 10.0
            mock_psutil_instance.memory_info.return_value.rss = 1024 * 1024 * 50 # 50MB
            mock_psutil.return_value = mock_psutil_instance
            
            self.manager.start_server(name)
            
            # Test record_server_metrics
            self.manager.record_server_metrics(name)
            
            # Verify metrics recorded in history
            self.assertIn(name, self.manager.metrics_history)
            self.assertTrue(len(self.manager.metrics_history[name]) > 0)
            
            # Test get_server_metrics (updates last_metrics)
            metrics = self.manager.get_server_metrics(name)
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics["cpu_percent"], 10.0)
            
            # Test last_metrics property
            self.assertIn(name, self.manager.last_metrics)
            self.assertEqual(self.manager.last_metrics[name]["cpu_percent"], 10.0)

if __name__ == "__main__":
    unittest.main()
