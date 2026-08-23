"""
ERP-Core Plugin System
Cold-start plugin architecture for modular ERP extensions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from sqlalchemy.orm import DeclarativeMeta
import importlib
import os
import yaml


class ERPPlugin(ABC):
    """Base class for all ERP plugins."""
    
    @abstractmethod
    def name(self) -> str:
        """Return plugin name."""
        pass
    
    @abstractmethod
    def version(self) -> str:
        """Return plugin version."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return plugin description."""
        pass
    
    @abstractmethod
    def register_routes(self, app: FastAPI, prefix: str = "/api/v1") -> None:
        """Register FastAPI routes."""
        pass
    
    @abstractmethod
    def register_models(self) -> List:
        """Return list of SQLAlchemy models to register."""
        pass
    
    def initialize(self) -> None:
        """Initialize plugin (optional)."""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {}


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugin_dir: str = "plugins/cold-start"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, ERPPlugin] = {}
        self.enabled_plugins: List[str] = []
        self.config: Dict[str, Any] = {}
        
    def load_config(self, config_path: str = "plugins_config.yaml") -> None:
        """Load plugin configuration from YAML file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {"enabled": [], "disabled": [], "config": {}}
            
        self.enabled_plugins = self.config.get("enabled", [])
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugin directory."""
        available = []
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            return available
            
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "plugin.py")):
                available.append(item)
        return available
    
    def load_plugin(self, plugin_name: str) -> Optional[ERPPlugin]:
        """Load a single plugin by name."""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        
        plugin_path = os.path.join(self.plugin_dir, plugin_name, "plugin.py")
        if not os.path.exists(plugin_path):
            print(f"Plugin {plugin_name} not found")
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}.plugin", plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin()
                self.plugins[plugin_name] = plugin_instance
                
                # Load plugin-specific config
                plugin_config = self.config.get("config", {}).get(plugin_name, {})
                if hasattr(plugin_instance, "configure"):
                    plugin_instance.configure(plugin_config)
                
                return plugin_instance
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
        
        return None
    
    def load_all_enabled(self) -> None:
        """Load all enabled plugins."""
        available = self.discover_plugins()
        
        for plugin_name in self.enabled_plugins:
            if plugin_name in available:
                plugin = self.load_plugin(plugin_name)
                if plugin:
                    print(f"Loaded plugin: {plugin.name()} v{plugin.version()}")
            else:
                print(f"Plugin {plugin_name} requested but not found")
    
    def register_all(self, app: FastAPI) -> None:
        """Register all loaded plugins with the FastAPI app."""
        for name, plugin in self.plugins.items():
            try:
                prefix = f"/api/v1/{name}"
                plugin.register_routes(app, prefix=prefix)
                print(f"Registered routes for plugin: {name}")
            except Exception as e:
                print(f"Failed to register routes for {name}: {e}")
    
    def get_all_models(self) -> List:
        """Collect all models from loaded plugins."""
        models = []
        for name, plugin in self.plugins.items():
            try:
                plugin_models = plugin.register_models()
                models.extend(plugin_models)
            except Exception as e:
                print(f"Failed to get models from {name}: {e}")
        return models
    
    def initialize_all(self) -> None:
        """Initialize all loaded plugins."""
        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
            except Exception as e:
                print(f"Failed to initialize {name}: {e}")


# Default plugin slots (ready for implementation)
PLUGIN_SLOTS = {
    "ecommerce": "E-commerce module (products, cart, orders)",
    "mrp": "Material Requirements Planning",
    "pos": "Point of Sale system",
    "bi": "Business Intelligence & Analytics",
    "supply_chain": "Supply Chain Management",
    "manufacturing": "Manufacturing Execution",
    "quality": "Quality Management",
    "assets": "Asset Management"
}


def create_plugin_template(plugin_name: str, output_dir: str = "plugins/cold-start") -> None:
    """Create a plugin template structure."""
    plugin_dir = os.path.join(output_dir, plugin_name)
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Create plugin.py
    plugin_code = f'''"""
{plugin_name.title()} Plugin for ERP-Core
Auto-generated plugin template
"""

from typing import List, Dict, Any
from fastapi import FastAPI, APIRouter, Depends
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Import base plugin class (adjust import path as needed)
try:
    from erp_core.plugins.base import ERPPlugin
except ImportError:
    from abc import ABC, abstractmethod
    class ERPPlugin(ABC):
        @abstractmethod
        def name(self) -> str: pass
        @abstractmethod
        def version(self) -> str: pass
        @abstractmethod
        def description(self) -> str: pass
        @abstractmethod
        def register_routes(self, app: FastAPI, prefix: str = "/api/v1") -> None: pass
        @abstractmethod
        def register_models(self) -> List: pass


class Plugin(ERPPlugin):
    """{plugin_name.title()} Plugin Implementation"""
    
    def __init__(self):
        self.config = {{}}
    
    def name(self) -> str:
        return "{plugin_name}"
    
    def version(self) -> str:
        return "0.1.0"
    
    def description(self) -> str:
        return "{plugin_name.title()} module for ERP-Core"
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure plugin with provided settings."""
        self.config.update(config)
    
    def register_routes(self, app: FastAPI, prefix: str = "/api/v1") -> None:
        """Register FastAPI routes for {plugin_name}."""
        router = APIRouter(prefix=prefix, tags=["{plugin_name.title()}"])
        
        @router.get("/")
        async def list_items():
            return {{"message": "{plugin_name.title()} API", "status": "active"}}
        
        @router.get("/status")
        async def get_status():
            return {{"plugin": self.name(), "version": self.version(), "enabled": True}}
        
        # TODO: Add more routes here
        # Example:
        # @router.post("/orders")
        # async def create_order(...):
        #     ...
        
        app.include_router(router)
    
    def register_models(self) -> List:
        """Return SQLAlchemy models for {plugin_name}."""
        # Define models here
        # Example:
        # class Order(Base):
        #     __tablename__ = "{plugin_name}_orders"
        #     id = Column(Integer, primary_key=True)
        #     ...
        
        return []  # Return list of model classes
    
    def initialize(self) -> None:
        """Initialize plugin resources."""
        print(f"Initializing {{self.name()}} plugin...")
        # TODO: Add initialization logic
'''
    
    with open(os.path.join(plugin_dir, "plugin.py"), 'w') as f:
        f.write(plugin_code)
    
    # Create __init__.py
    with open(os.path.join(plugin_dir, "__init__.py"), 'w') as f:
        f.write(f'"""{plugin_name.title()} Plugin Package"""\\n')
    
    # Create README.md
    readme = f'''# {plugin_name.title()} Plugin

## Overview
{plugin_name.title()} plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - {plugin_name}
  config:
    {plugin_name}:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/{plugin_name}/` - List items
- `GET /api/v1/{plugin_name}/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
'''
    
    with open(os.path.join(plugin_dir, "README.md"), 'w') as f:
        f.write(readme)
    
    print(f"Created plugin template: {plugin_dir}")
