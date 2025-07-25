"""
Configuration for MCP integration.
Loads environment variables and provides default settings.
"""
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env file from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# MCP Server configurations
MCP_SERVERS = {
    "filesystem": {
        "name": "Filesystem Server",
        "description": "File and directory operations",
        "container_name": os.getenv("MCP_CONTAINER_NAME", "agent-framework-mcp-filesystem-1"),
        "server_path": os.getenv("MCP_SERVER_PATH", "/projects"),
        "icon": "📁",
        "enabled": True,
        "tools": {
            "list_directory": {
                "description": "List contents of a directory",
                "parameters": {"path": "Directory path to list"}
            },
            "read_file": {
                "description": "Read contents of a text file",
                "parameters": {"path": "File path to read"}
            },
            "write_file": {
                "description": "Write content to a file",
                "parameters": {"path": "File path to write", "content": "Content to write"}
            },
            "create_directory": {
                "description": "Create a new directory",
                "parameters": {"path": "Directory path to create"}
            },
            "move_file": {
                "description": "Move or rename a file",
                "parameters": {"source": "Source path", "destination": "Destination path"}
            },
            "get_file_info": {
                "description": "Get file metadata and information",
                "parameters": {"path": "File path to inspect"}
            },
            "search_files": {
                "description": "Search for files matching a pattern",
                "parameters": {"pattern": "Search pattern", "path": "Directory to search in"}
            },
            "directory_tree": {
                "description": "Get directory tree structure",
                "parameters": {"path": "Root directory path", "max_depth": "Maximum depth (optional)"}
            }
        }
    },
    # Future servers will be added here
    # "memory": {
    #     "name": "Memory Server", 
    #     "description": "Knowledge graph and memory operations",
    #     "container_name": "agent-service-toolkit-mcp-memory-1",
    #     "server_path": "/memory",
    #     "icon": "🧠",
    #     "enabled": False,
    #     "tools": {...}
    # }
    "brave_search": {
        "name": "Brave Search",
        "description": "Web, image, video and news search via Brave Search API",
        "container_name": os.getenv("MCP_BRAVE_CONTAINER_NAME", "agent-framework-mcp-brave-search-1"),
        "server_path": "/",  # not used for search, but required
        "icon": "🔍",
        "enabled": True,
        "tools": {
            "brave_web_search": {
                "description": "Perform a web search using Brave Search API",
                "parameters": {
                    "query": "Search query (required)",
                    "count": "Number of results (optional, default 10)",
                    "safesearch": "off | moderate | strict (optional)",
                    "freshness": "pd | pw | pm | py for past day/week/month/year (optional)"
                }
            },
            "brave_image_search": {
                "description": "Search for images using Brave Search API",
                "parameters": {
                    "query": "Search query (required)",
                    "count": "Number of results (optional, default 3)",
                    "safesearch": "off | strict (optional)"
                }
            },
            "brave_video_search": {
                "description": "Search for videos using Brave Search API",
                "parameters": {
                    "query": "Search query (required)",
                    "count": "Number of results (optional, default 10)",
                    "freshness": "pd | pw | pm | py for past day/week/month/year (optional)"
                }
            },
            "brave_news_search": {
                "description": "Search for news articles using Brave Search API",
                "parameters": {
                    "query": "Search query (required)",
                    "count": "Number of results (optional, default 10)",
                    "freshness": "pd | pw | pm | py for past day/week/month/year (optional)"
                }
            },
            "brave_local_search": {
                "description": "Search for local businesses and places",
                "parameters": {
                    "query": "Local search query (required)",
                    "count": "Number of results (optional, default 10)"
                }
            }
        }
    }
}

# Validate required settings
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required. Please set it in .env file.")

# Validate Brave API key if Brave Search is enabled
if MCP_SERVERS.get("brave_search", {}).get("enabled", False) and not BRAVE_API_KEY:
    print("⚠️ Warning: BRAVE_API_KEY is not set but Brave Search is enabled. Please set it in .env file.")

# Get enabled servers
def get_enabled_servers() -> dict[str, dict[str, Any]]:
    """Get all enabled MCP servers"""
    return {k: v for k, v in MCP_SERVERS.items() if v.get("enabled", False)}

# Get server configuration
def get_server_config(server_id: str) -> dict[str, Any]:
    """Get configuration for a specific server"""
    return MCP_SERVERS.get(server_id, {})

print("✅ Configuration loaded:")
enabled_servers = get_enabled_servers()
print(f"   - Enabled MCP Servers: {len(enabled_servers)}")
for server_id, config in enabled_servers.items():
    print(f"     • {config['icon']} {config['name']} ({server_id})")
print(f"   - OpenAI API Key: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
print(f"   - Brave API Key: {'✅ Set' if BRAVE_API_KEY else '❌ Missing'}")