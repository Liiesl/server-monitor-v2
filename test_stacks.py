"""
Tests for Server Stacks feature
"""
import os
import json
import unittest
import shutil
from config_manager import ConfigManager
from server_manager import ServerManager

class TestServerStacks(unittest.TestCase):
    def setUp(self):
        # Create temporary config files
        self.test_dir = "test_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
        self.config_file = os.path.join(self.test_dir, "servers.json")
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        self.stacks_file = "stacks.json" # ConfigManager uses relative path for now, we might need to patch it or just use it
        
        # Backup existing stacks.json if it exists
        if os.path.exists(self.stacks_file):
            shutil.copy(self.stacks_file, self.stacks_file + ".bak")
            
        # Create dummy servers
        with open(self.config_file, 'w') as f:
            json.dump({
                "server1": {"path": "/tmp/s1", "command": "node", "status": "stopped"},
                "server2": {"path": "/tmp/s2", "command": "node", "status": "stopped"}
            }, f)
            
        with open(self.settings_file, 'w') as f:
            json.dump({}, f)
            
        # Clear stacks.json
        with open(self.stacks_file, 'w') as f:
            json.dump({}, f)
            
        self.server_manager = ServerManager(self.config_file, self.settings_file)
        
    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        # Restore stacks.json
        if os.path.exists(self.stacks_file + ".bak"):
            shutil.move(self.stacks_file + ".bak", self.stacks_file)
        elif os.path.exists(self.stacks_file):
            os.remove(self.stacks_file)
            
    def test_add_stack(self):
        """Test adding a stack"""
        result = self.server_manager.add_stack("test_stack", ["server1", "server2"])
        self.assertTrue(result)
        
        stacks = self.server_manager.get_stacks()
        self.assertIn("test_stack", stacks)
        self.assertEqual(stacks["test_stack"], ["server1", "server2"])
        
    def test_remove_stack(self):
        """Test removing a stack"""
        self.server_manager.add_stack("test_stack", ["server1"])
        result = self.server_manager.remove_stack("test_stack")
        self.assertTrue(result)
        
        stacks = self.server_manager.get_stacks()
        self.assertNotIn("test_stack", stacks)
        
    def test_update_stack(self):
        """Test updating a stack"""
        self.server_manager.add_stack("test_stack", ["server1"])
        result = self.server_manager.update_stack("test_stack", ["server1", "server2"])
        self.assertTrue(result)
        
        stacks = self.server_manager.get_stacks()
        self.assertEqual(stacks["test_stack"], ["server1", "server2"])
        
    def test_get_stack_status(self):
        """Test stack status calculation"""
        self.server_manager.add_stack("test_stack", ["server1", "server2"])
        
        # Both stopped
        status = self.server_manager.get_stack_status("test_stack")
        self.assertEqual(status, "stopped")
        
        # Mock server1 running
        # We need to manually update status in servers dict since we are not actually running processes
        self.server_manager.servers["server1"]["status"] = "running"
        
        status = self.server_manager.get_stack_status("test_stack")
        self.assertEqual(status, "partial")
        
        # Both running
        self.server_manager.servers["server2"]["status"] = "running"
        status = self.server_manager.get_stack_status("test_stack")
        self.assertEqual(status, "running")

if __name__ == '__main__':
    unittest.main()
