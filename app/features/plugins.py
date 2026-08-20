"""
Plugin Architecture Module
Provides a modular plugin system for extending functionality.
"""

from typing import Dict, Any, Callable, List, Optional
import importlib
import inspect
from pathlib import Path
import json

from core.logger import get_logger
from data.event_bus import event_bus


logger = get_logger(__name__)


class Plugin:
    """
    Base class for all plugins.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize the plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
        """
        self.name = name
        self.version = version
        self.enabled = True
        self.config = {}
        logger.info(f"Plugin {name} v{version} initialized")
    
    def enable(self):
        """Enable the plugin."""
        self.enabled = True
        logger.info(f"Plugin {self.name} enabled")
    
    def disable(self):
        """Disable the plugin."""
        self.enabled = False
        logger.info(f"Plugin {self.name} disabled")
    
    def configure(self, config: Dict[str, Any]):
        """Configure the plugin."""
        self.config.update(config)
        logger.info(f"Plugin {self.name} configured")
    
    def initialize(self):
        """Initialize plugin (override in subclass)."""
        pass
    
    def on_tick(self, tick):
        """Handle tick event (override in subclass)."""
        pass
    
    def on_analysis(self, analysis):
        """Handle analysis event (override in subclass)."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.
        
        Returns:
            Dict[str, Any]: Plugin info
        """
        return {
            'name': self.name,
            'version': self.version,
            'enabled': self.enabled,
            'config': self.config
        }


class PluginManager:
    """
    Manages plugins and their lifecycle.
    Provides plugin discovery, loading, and execution.
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dir: Directory containing plugins
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Plugin] = {}
        self._loaded = False
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Subscribe to events
        event_bus.subscribe('processed_tick', self._handle_tick, async_handler=False)
        event_bus.subscribe('window_updated', self._handle_analysis, async_handler=False)
        
        logger.info("PluginManager initialized")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins.
        
        Returns:
            List[str]: Names of discovered plugins
        """
        discovered = []
        
        try:
            for plugin_file in self.plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                
                # Import plugin module
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}", plugin_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin class
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and 
                            obj != Plugin):
                            discovered.append(module_name)
                            break
            
            logger.info(f"Discovered {len(discovered)} plugins")
            
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        Load a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Optional[Plugin]: Loaded plugin instance
        """
        try:
            plugin_path = self.plugin_dir / f"{plugin_name}.py"
            if not plugin_path.exists():
                logger.warning(f"Plugin {plugin_name} not found")
                return None
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", plugin_path
            )
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin = obj()
                    self.plugins[plugin_name] = plugin
                    plugin.initialize()
                    logger.info(f"Loaded plugin: {plugin_name}")
                    return plugin
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return None
    
    def load_all_plugins(self):
        """Load all discovered plugins."""
        discovered = self.discover_plugins()
        loaded = 0
        
        for plugin_name in discovered:
            if self.load_plugin(plugin_name):
                loaded += 1
        
        logger.info(f"Loaded {loaded}/{len(discovered)} plugins")
        self._loaded = True
    
    def _handle_tick(self, event):
        """Handle tick events for all enabled plugins."""
        tick = event.data
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    plugin.on_tick(tick)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}")
    
    def _handle_analysis(self, event):
        """Handle analysis events for all enabled plugins."""
        analysis = event.data
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    plugin.on_analysis(analysis)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Optional[Plugin]: Plugin instance or None
        """
        return self.plugins.get(name)
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if successful
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enable()
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if successful
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.disable()
            return True
        return False
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """
        Get information about all plugins.
        
        Returns:
            List[Dict[str, Any]]: Plugin information
        """
        return [p.get_info() for p in self.plugins.values()]
    
    def create_plugin_template(self, name: str) -> str:
        """
        Create a plugin template file.
        
        Args:
            name: Plugin name
            
        Returns:
            str: Plugin template content
        """
        template = f'''
"""
{name} Plugin for Project Alpha
"""

from app.features.plugins import Plugin
from app.core.logger import get_logger

logger = get_logger(__name__)


class {name.capitalize()}Plugin(Plugin):
    """Plugin implementation."""
    
    def __init__(self):
        super().__init__("{name}", "1.0.0")
    
    def initialize(self):
        """Initialize plugin."""
        logger.info(f"{{self.name}} plugin initialized")
    
    def on_tick(self, tick):
        """Handle tick events."""
        pass
    
    def on_analysis(self, analysis):
        """Handle analysis events."""
        pass
'''
        
        # Save template
        plugin_path = self.plugin_dir / f"{name}.py"
        with open(plugin_path, 'w') as f:
            f.write(template)
        
        logger.info(f"Created plugin template: {name}")
        return template
