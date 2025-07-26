"""
Configuration for MCP integration.
Loads environment variables and provides default settings.
"""
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env file from parent directory (now two levels up)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Configuration settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Validate required settings
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required. Please set it in .env file.")

# Import plugin manager for dynamic server configuration
# Note: This import is after the basic config to avoid circular imports
from .plugin_manager import load_plugins

# Get enabled servers
def get_enabled_servers() -> dict[str, dict[str, Any]]:
    """Return only enabled plugins from plugin manager."""
    plugins = load_plugins()
    return {sid: cfg for sid, cfg in plugins.items() if cfg.get("enabled", False)}

# Get server configuration
def get_server_config(server_id: str) -> dict[str, Any]:
    """Return configuration for a specific server."""
    return load_plugins().get(server_id, {})

print("✅ Configuration loaded:")
try:
    enabled_servers = get_enabled_servers()
    print(f"   - Enabled MCP Servers: {len(enabled_servers)}")
    for server_id, config in enabled_servers.items():
        print(f"     • {config.get('icon', '❓')} {config.get('name', server_id)} ({server_id})")
except Exception as e:
    print(f"   - MCP Servers: Plugin manager not yet available ({e})")
print(f"   - OpenAI API Key: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
print(f"   - Brave API Key: {'✅ Set' if BRAVE_API_KEY else '❌ Missing'}")