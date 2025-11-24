import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
import json
from server_manager import ServerManager

class TestFlareSolverr(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        self.config_file = os.path.join(self.test_dir, "servers.json")
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        
        self.manager = ServerManager(config_file=self.config_file, settings_file=self.settings_file)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_flaresolverr_source(self):
        name = "FlareSource"
        path = os.path.join(self.test_dir, "flaresolverr_src")
        os.makedirs(os.path.join(path, "src"))
        # Create dummy flaresolverr.py
        with open(os.path.join(path, "src", "flaresolverr.py"), "w") as f:
            f.write("print('Hello')")
            
        self.manager.add_server(
            name=name,
            path=path,
            server_type="flaresolverr",
            flaresolverr_type="source",
            python_command="python"
        )
        
        # Verify config
        self.assertIn(name, self.manager.servers)
        server = self.manager.servers[name]
        self.assertEqual(server["server_type"], "flaresolverr")
        self.assertEqual(server["flaresolverr_type"], "source")
        self.assertEqual(server["python_command"], "python")
        
        # Test start command construction
        with patch("subprocess.Popen") as mock_popen, \
             patch("psutil.Process") as mock_psutil, \
             patch("ui.log_reader.LogReaderThread") as mock_log_reader:
            
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            self.manager.start_server(name)
            
            # Verify command
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            expected_script = os.path.join(path, "src", "flaresolverr.py")
            self.assertEqual(cmd, ["python", expected_script])
            self.assertEqual(kwargs["cwd"], path)

    def test_add_flaresolverr_binary(self):
        name = "FlareBinary"
        path = os.path.join(self.test_dir, "flaresolverr.exe")
        with open(path, "w") as f:
            f.write("dummy exe")
            
        self.manager.add_server(
            name=name,
            path=path,
            server_type="flaresolverr",
            flaresolverr_type="binary"
        )
        
        # Verify config
        self.assertIn(name, self.manager.servers)
        server = self.manager.servers[name]
        self.assertEqual(server["server_type"], "flaresolverr")
        self.assertEqual(server["flaresolverr_type"], "binary")
        
        # Test start command construction
        with patch("subprocess.Popen") as mock_popen, \
             patch("psutil.Process") as mock_psutil, \
             patch("ui.log_reader.LogReaderThread") as mock_log_reader:
            
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            self.manager.start_server(name)
            
            # Verify command
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            self.assertEqual(cmd, [path])
            # CWD should be dir of executable
            self.assertEqual(kwargs["cwd"], self.test_dir)

if __name__ == "__main__":
    unittest.main()
