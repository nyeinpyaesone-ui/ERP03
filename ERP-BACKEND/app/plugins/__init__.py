"""
ERP Core Plugin System

Cold-start plugin architecture for modular ERP functionality.
Core modules are built-in; additional domains load as plugins.
"""
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI

logger = logging.getLogger("erp03.plugins")


class PluginMetadata:
    """Metadata for a plugin."""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        domain: str,
        author: str = "ERP03",
        dependencies: List[str] = None,
        router_prefix: str = None,
        auto_register: bool = True
    ):
        self.name = name
        self.version = version
        self.description = description
        self.domain = domain
        self.author = author
        self.dependencies = dependencies or []
        self.router_prefix = router_prefix or f"/api/v1/{domain}"
        self.auto_register = auto_register


class PluginBase:
    """Base class for all ERP plugins."""
    
    metadata: PluginMetadata = None
    
    def __init__(self, app: FastAPI, config: Dict[str, Any] = None):
        """
        Initialize the plugin.
        
        Args:
            app: FastAPI application instance
            config: Plugin-specific configuration
        """
        self.app = app
        self.config = config or {}
        self.initialized = False
    
    def on_load(self) -> bool:
        """
        Called when plugin is loaded. Return False to abort loading.
        
        Returns:
            bool: True if loading should continue, False to abort
        """
        return True
    
    def on_register(self) -> None:
        """Called when plugin routes are being registered."""
        pass
    
    def on_startup(self) -> None:
        """Called when application starts."""
        pass
    
    def on_shutdown(self) -> None:
        """Called when application shuts down."""
        pass
    
    def get_router(self):
        """Return the APIRouter for this plugin."""
        raise NotImplementedError("Plugins must implement get_router()")


class PluginManager:
    """Manages plugin lifecycle and registration."""
    
    def __init__(self, app: FastAPI, plugins_dir: str = None):
        """
        Initialize the plugin manager.
        
        Args:
            app: FastAPI application instance
            plugins_dir: Directory containing plugin packages
        """
        self.app = app
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent / "plugins"
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def register_plugin_config(self, name: str, config: Dict[str, Any]) -> None:
        """Register configuration for a plugin."""
        self.plugin_configs[name] = config
    
    def discover_plugins(self) -> List[Path]:
        """
        Discover available plugins in the plugins directory.
        
        Returns:
            List of paths to plugin directories
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return []
        
        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "plugin.py").exists():
                plugins.append(item)
            elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                # Single-file plugins
                plugins.append(item)
        
        return plugins
    
    def load_plugin(self, plugin_path: Path) -> Optional[PluginBase]:
        """
        Load a single plugin from path.
        
        Args:
            plugin_path: Path to plugin directory or file
            
        Returns:
            Loaded plugin instance or None if loading failed
        """
        try:
            if plugin_path.is_dir():
                # Package plugin
                module_name = f"app.plugins.{plugin_path.name}.plugin"
                spec = importlib.util.spec_from_file_location(
                    module_name, 
                    plugin_path / "plugin.py"
                )
            else:
                # Single-file plugin
                module_name = f"app.plugins.{plugin_path.stem}"
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            
            if spec is None or spec.loader is None:
                logger.error(f"Could not load spec for {plugin_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Plugin class
            if not hasattr(module, 'Plugin'):
                logger.warning(f"No Plugin class found in {plugin_path}")
                return None
            
            PluginClass = module.Plugin
            config = self.plugin_configs.get(module_name, {})
            plugin_instance = PluginClass(self.app, config)
            
            # Validate metadata
            if not hasattr(plugin_instance, 'metadata') or plugin_instance.metadata is None:
                logger.error(f"Plugin {module_name} missing metadata")
                return None
            
            # Check dependencies
            for dep in plugin_instance.metadata.dependencies:
                if dep not in self.plugins:
                    logger.error(f"Plugin {plugin_instance.metadata.name} requires {dep}")
                    return None
            
            # Call on_load hook
            if not plugin_instance.on_load():
                logger.info(f"Plugin {plugin_instance.metadata.name} aborted loading")
                return None
            
            self.plugins[plugin_instance.metadata.name] = plugin_instance
            logger.info(f"Loaded plugin: {plugin_instance.metadata.name} v{plugin_instance.metadata.version}")
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}", exc_info=True)
            return None
    
    def register_all(self) -> int:
        """
        Register all discovered plugins with the application.
        
        Returns:
            Number of successfully registered plugins
        """
        count = 0
        for plugin_path in self.discover_plugins():
            plugin = self.load_plugin(plugin_path)
            if plugin and plugin.metadata.auto_register:
                try:
                    router = plugin.get_router()
                    self.app.include_router(
                        router,
                        prefix=plugin.metadata.router_prefix,
                        tags=[plugin.metadata.domain]
                    )
                    plugin.on_register()
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to register plugin {plugin.metadata.name}: {e}")
        
        self._loaded = True
        logger.info(f"Registered {count} plugins")
        return count
    
    def startup(self) -> None:
        """Call startup hooks for all loaded plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.on_startup()
            except Exception as e:
                logger.error(f"Plugin {plugin.metadata.name} startup failed: {e}")
    
    def shutdown(self) -> None:
        """Call shutdown hooks for all loaded plugins."""
        for plugin in reversed(list(self.plugins.values())):
            try:
                plugin.on_shutdown()
            except Exception as e:
                logger.error(f"Plugin {plugin.metadata.name} shutdown failed: {e}")
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with their metadata."""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "domain": p.metadata.domain,
                "description": p.metadata.description,
                "author": p.metadata.author,
                "initialized": p.initialized
            }
            for p in self.plugins.values()
        ]


# Built-in core modules (always available, not loaded as plugins)
CORE_MODULES = [
    "auth",
    "users", 
    "permissions",
    "crm",
    "hr",
    "finance",
    "inventory",
    "regulated_inventory",
    "projects",
    "documents",
    "workflows",
    "payments",
    "analytics",
    "search",
    "integrations",
    "websocket",
    "health",
    "admin"
]


def setup_plugins(app: FastAPI, plugins_dir: str = None) -> PluginManager:
    """
    Setup plugin system for the application.
    
    Args:
        app: FastAPI application
        plugins_dir: Optional plugins directory path
        
    Returns:
        Configured PluginManager instance
    """
    manager = PluginManager(app, plugins_dir)
    
    @app.on_event("startup")
    async def startup_plugins():
        manager.register_all()
        manager.startup()
    
    @app.on_event("shutdown")
    async def shutdown_plugins():
        manager.shutdown()
    
    return manager
