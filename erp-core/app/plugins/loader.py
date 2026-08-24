import importlib
import os
from pathlib import Path
from typing import Dict, List, Any

class PluginLoader:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.plugin_dir = Path("app/plugins")
    
    async def load_all_plugins(self) -> List[str]:
        """Discover and load all plugins from plugin directory"""
        loaded = []
        
        if not self.plugin_dir.exists():
            print("Plugin directory not found")
            return loaded
        
        for plugin_path in self.plugin_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith("__"):
                try:
                    await self.load_plugin(plugin_path.name)
                    loaded.append(plugin_path.name)
                    print(f"Loaded plugin: {plugin_path.name}")
                except Exception as e:
                    print(f"Failed to load plugin {plugin_path.name}: {e}")
        
        return loaded
    
    async def load_plugin(self, plugin_name: str) -> None:
        """Load a single plugin by name"""
        module_path = f"app.plugins.{plugin_name}.plugin"
        
        try:
            module = importlib.import_module(module_path)
            
            # Look for register function
            if hasattr(module, "register"):
                plugin_info = await module.register()
                self.plugins[plugin_name] = plugin_info
        except ImportError as e:
            raise Exception(f"Plugin {plugin_name} not found: {e}")
    
    def get_plugin(self, plugin_name: str) -> Any:
        """Get a loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins"""
        return list(self.plugins.keys())
