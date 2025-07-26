"""
Plugin manager for MCP integration.
Dynamically discovers and loads plugin configurations and their corresponding client classes.
"""
from pathlib import Path
import yaml
import importlib
import logging
from typing import Dict, Any, Optional

# Global cache for loaded plugins
_PLUGINS: Optional[Dict[str, Dict[str, Any]]] = None

def load_plugins() -> Dict[str, Dict[str, Any]]:
    """
    Discover and load all plugins. Returns a dictionary keyed by server_id.
    Each plugin config includes a reference to its client class.
    
    Returns:
        Dict mapping server_id to plugin configuration with client_class loaded
    """
    global _PLUGINS
    if _PLUGINS is not None:
        return _PLUGINS

    plugins_dir = Path(__file__).parent.parent / "plugins"
    plugins = {}

    if not plugins_dir.exists():
        print(f"⚠️ Warning: Plugins directory not found at {plugins_dir}")
        _PLUGINS = {}
        return _PLUGINS

    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir() and not plugin_path.name.startswith('.'):
            try:
                config_file = plugin_path / "config.yaml"
                if not config_file.exists():
                    print(f"⚠️ Warning: No config.yaml found in plugin {plugin_path.name}")
                    continue

                # Load YAML configuration
                try:
                    config = yaml.safe_load(config_file.read_text())
                    if not config:
                        print(f"⚠️ Warning: Empty config.yaml in plugin {plugin_path.name}")
                        continue
                except yaml.YAMLError as e:
                    print(f"❌ Error: Invalid YAML in plugin {plugin_path.name}: {e}")
                    continue

                server_id = plugin_path.name

                # Load client class
                client_path = config.get("client_class", None)
                try:
                    if client_path:
                        # Use explicit client_class from config
                        module_name, class_name = client_path.rsplit(".", 1)
                        module = importlib.import_module(module_name)
                        client_class = getattr(module, class_name)
                    else:
                        # Fallback: use naming convention
                        module_name = f"mcp_integration.clients.{server_id}_client"
                        class_name = f"{server_id.title().replace('_', '')}Client"
                        module = importlib.import_module(module_name)
                        client_class = getattr(module, class_name)
                        print(f"ℹ️ Using naming convention for {server_id}: {module_name}.{class_name}")

                except (ImportError, AttributeError) as e:
                    print(f"❌ Error: Cannot load client class for {server_id}: {e}")
                    continue

                # Add resolved client class and server_id to config
                config["client_class"] = client_class
                config["server_id"] = server_id
                plugins[server_id] = config

                print(f"✅ Loaded plugin: {config.get('name', server_id)} ({server_id})")

            except Exception as e:
                print(f"❌ Error loading plugin {plugin_path.name}: {e}")
                continue

    _PLUGINS = plugins
    print(f"🔌 Plugin manager loaded {len(plugins)} plugins")
    return plugins


def reload_plugins() -> Dict[str, Dict[str, Any]]:
    """
    Force reload of all plugins, clearing the cache.
    Useful for development or when plugin configurations change.
    
    Returns:
        Dict mapping server_id to plugin configuration with client_class loaded
    """
    global _PLUGINS
    _PLUGINS = None
    return load_plugins()


def get_plugin(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific plugin by server_id.
    
    Args:
        server_id: The ID of the server/plugin to retrieve
        
    Returns:
        Plugin configuration dict or None if not found
    """
    plugins = load_plugins()
    return plugins.get(server_id)


def list_available_plugins() -> Dict[str, str]:
    """
    List all available plugins with their names.
    
    Returns:
        Dict mapping server_id to plugin name
    """
    plugins = load_plugins()
    return {
        server_id: config.get("name", server_id) 
        for server_id, config in plugins.items()
    }