import json
import os
from typing import Dict, Optional
from datetime import datetime

class ConfigManager:
    """Manages application settings and server configurations"""
    
    def __init__(self, config_file: str = "servers.json", settings_file: str = "settings.json"):
        self.config_file = config_file
        self.settings_file = settings_file
        self.settings: Dict = {}
        self.servers: Dict[str, Dict] = {}
        self.stacks: Dict[str, list] = {}
        self.load_settings()
        self.load_config()
        self.load_stacks()
        
    def load_settings(self):
        """Load application settings from settings.json"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self.settings = {}
        else:
            self.settings = {}
        
        # Set defaults
        defaults = {
            "python_command": "python",
            "node_command": "node",
            "flask_command": "flask",
            "tray_shortcut": "Ctrl+Alt+S"
        }
        
        settings_changed = False
        for key, default_value in defaults.items():
            if key not in self.settings:
                self.settings[key] = default_value
                settings_changed = True
        
        if not os.path.exists(self.settings_file) or settings_changed:
            self.save_settings()

    def save_settings(self):
        """Save application settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_config(self):
        """Load server configurations"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.servers = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.servers = {}
        else:
            self.servers = {}
        
        # Backward compatibility
        default_python_cmd = self.settings.get("python_command", "python")
        for name, config in self.servers.items():
            if "server_type" not in config:
                config["server_type"] = "nodejs"
            if "python_command" not in config:
                config["python_command"] = default_python_cmd

    def save_config(self):
        """Save server configurations"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.servers, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def add_server(self, name: str, path: str, command: str = "node", args: str = "", port: Optional[int] = None,
                  server_type: str = "nodejs", python_command: Optional[str] = None, venv_path: Optional[str] = None,
                  flaresolverr_type: Optional[str] = None) -> bool:
        """Add a new server configuration"""
        if name in self.servers:
            return False
        
        if python_command is None:
            python_command = self.settings.get("python_command", "python")
        
        server_config = {
            "path": path,
            "command": command,
            "args": args,
            "port": port,
            "server_type": server_type,
            "python_command": python_command,
            "status": "stopped",
            "created_at": datetime.now().isoformat()
        }
        
        if venv_path:
            server_config["venv_path"] = venv_path
            
        if flaresolverr_type:
            server_config["flaresolverr_type"] = flaresolverr_type
        
        self.servers[name] = server_config
        self.save_config()
        return True

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration"""
        if name in self.servers:
            del self.servers[name]
            self.save_config()
            return True
        return False

    def update_server(self, name: str, path: str = None, command: str = None, args: str = None, port: int = None,
                      server_type: str = None, python_command: str = None, venv_path: str = None,
                      flaresolverr_type: str = None) -> bool:
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
        if server_type is not None:
            self.servers[name]["server_type"] = server_type
        if python_command is not None:
            self.servers[name]["python_command"] = python_command
        if venv_path is not None:
            if venv_path:
                self.servers[name]["venv_path"] = venv_path
            else:
                self.servers[name].pop("venv_path", None)
        if flaresolverr_type is not None:
            self.servers[name]["flaresolverr_type"] = flaresolverr_type
        
        self.save_config()
        return True

    # Stack Management
    
    def load_stacks(self):
        """Load stack configurations"""
        stacks_file = "stacks.json"
        if os.path.exists(stacks_file):
            try:
                with open(stacks_file, 'r') as f:
                    self.stacks = json.load(f)
            except Exception as e:
                print(f"Error loading stacks: {e}")
                self.stacks = {}
        else:
            self.stacks = {}

    def save_stacks(self):
        """Save stack configurations"""
        stacks_file = "stacks.json"
        try:
            with open(stacks_file, 'w') as f:
                json.dump(self.stacks, f, indent=2)
        except Exception as e:
            print(f"Error saving stacks: {e}")

    def add_stack(self, name: str, server_names: list) -> bool:
        """Add a new stack configuration"""
        if name in self.stacks:
            return False
        
        self.stacks[name] = server_names
        self.save_stacks()
        return True

    def remove_stack(self, name: str) -> bool:
        """Remove a stack configuration"""
        if name in self.stacks:
            del self.stacks[name]
            self.save_stacks()
            return True
        return False

    def update_stack(self, name: str, server_names: list) -> bool:
        """Update stack configuration"""
        if name not in self.stacks:
            return False
        
        self.stacks[name] = server_names
        self.save_stacks()
        return True
    
    def get_stacks(self) -> Dict:
        """Get all stacks"""
        return self.stacks

