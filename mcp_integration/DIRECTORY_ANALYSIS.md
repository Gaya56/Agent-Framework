# MCP Integration Directory Analysis

## Project Goal and Summary

Our goal is to organize and create a plug-and-play MCP (Model Context Protocol) server system that works seamlessly with the existing chatbot functionality within the `mcp_integration` directory. The current system works perfectly but has all components scattered in a flat directory structure, making it difficult to add new MCP servers or manage existing ones independently. We want to reorganize this working system into a clean, plugin-based architecture where each MCP server becomes a self-contained plugin that can be easily added or removed without changing any core functionality. The Docker MCP services will continue to be hosted in the root `/workspaces/Agent-Framework/compose.yaml` file, maintaining the existing container architecture while simplifying the setup process. This reorganization should preserve 100% of the current functionality - same performance, same API calls, same UI behavior - while making it trivial for developers to extend MCP capabilities by simply dropping in new plugin folders.

## Current Directory Structure Analysis

```
/workspaces/Agent-Framework/mcp_integration/
├── CLEANUP_GUIDE.md                    # Documentation file for cleanup guidance
├── MCP_ARCHITECTURE.md                 # Architecture documentation (attached file)
├── config.py                          # Configuration management and environment variables
├── mcp_openai_bot_v2.py               # OpenAI bot integration with MCP tools
├── mcp_tab.py                         # Streamlit UI integration for MCP functionality
├── multi_mcp_client.py                # Multi-server orchestrator and manager
├── working_brave_search_client.py     # Brave Search MCP client implementation
├── working_mcp_client.py              # Filesystem MCP client implementation
└── servers/                           # Server configuration directory
    └── brave_search/
        └── server.yaml                 # Brave Search server configuration
```

## Detailed File Analysis

### 1. `config.py` - Configuration Management Hub
**Path**: `/workspaces/Agent-Framework/mcp_integration/config.py`
**Lines**: 149 total
**Purpose**: Central configuration file that manages environment variables, server definitions, and tool configurations

**Key Imports**:
```python
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
```

**Key Functions**:
- `get_enabled_servers()` → `dict[str, dict[str, Any]]` - Returns all enabled MCP servers from configuration
- `get_server_config(server_id: str)` → `dict[str, Any]` - Retrieves configuration for a specific server

**Key Variables**:
- `OPENAI_API_KEY` - OpenAI API key from environment variables
- `BRAVE_API_KEY` - Brave Search API key from environment variables
- `MCP_SERVERS` - Dictionary containing all MCP server configurations with nested tool definitions

**Server Configurations**:
- **filesystem**: Container `agent-framework-mcp-filesystem-1`, 8 tools (list_directory, read_file, write_file, create_directory, move_file, get_file_info, search_files, directory_tree)
- **brave_search**: Container `agent-framework-mcp-brave-search-1`, 5 tools (brave_web_search, brave_image_search, brave_video_search, brave_news_search, brave_local_search)

**Environment Loading**: Loads `.env` file from parent directory using `Path(__file__).parent.parent / ".env"`

### 2. `multi_mcp_client.py` - Multi-Server Orchestrator
**Path**: `/workspaces/Agent-Framework/mcp_integration/multi_mcp_client.py`
**Lines**: 155 total
**Purpose**: Central orchestrator that manages multiple MCP servers and routes tool calls to appropriate servers

**Key Imports**:
```python
from typing import Any
from config import get_enabled_servers
from working_mcp_client import WorkingMCPClient  
from working_brave_search_client import WorkingBraveSearchClient
```

**Key Classes**:

#### `MCPServerClient` - Individual Server Wrapper
**Functions**:
- `__init__(self, server_id: str, config: dict[str, Any])` - Initializes server client with configuration
- `async initialize(self) -> bool` - Establishes connection to MCP container
- `get_available_tools(self) -> dict[str, dict[str, Any]]` - Returns tools available for this server
- `async call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]` - Executes tool via working client
- `async close(self)` - Closes working client connection

#### `MultiMCPClient` - Main Orchestrator Class
**Functions**:
- `__init__(self)` - Initializes empty server dictionary
- `async initialize(self) -> bool` - Initializes all enabled MCP servers from configuration
- `get_available_servers(self) -> dict[str, dict[str, Any]]` - Returns all initialized servers with metadata
- `get_server_tools(self, server_id: str) -> dict[str, dict[str, Any]]` - Gets tools for specific server
- `async call_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]` - Routes tool calls to appropriate server
- `async close(self)` - Cleanup all server connections

### 3. `working_mcp_client.py` - Filesystem MCP Client
**Path**: `/workspaces/Agent-Framework/mcp_integration/working_mcp_client.py`
**Lines**: 334 total
**Purpose**: Reliable MCP client for filesystem operations using Docker exec communication pattern

**Key Imports**:
```python
import asyncio
from typing import Any
from config import get_enabled_servers
```

**Key Class**: `WorkingMCPClient`

**Functions**:
- `__init__(self)` - Initializes with filesystem configuration from enabled servers
- `async initialize(self) -> bool` - Tests container accessibility and establishes connection
- `async _run_docker_command(self, command: list[str]) -> dict[str, Any]` - Executes commands via Docker exec
- `_safe_path(self, path: str) -> str` - Ensures path safety within server boundaries
- `async call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]` - Main tool execution dispatcher
- `get_available_tools(self) -> dict[str, dict[str, Any]]` - Returns dictionary of available filesystem tools
- `async close(self)` - Cleanup method for connection closure

**Tool Methods** (all async):
- Directory operations: `list_directory`, `create_directory`, `directory_tree`
- File operations: `read_file`, `write_file`, `move_file`, `get_file_info`, `search_files`

**Container Configuration**:
- Default container: `agent-framework-mcp-filesystem-1`
- Default server path: `/projects`
- Communication: Docker exec with JSON responses

### 4. `working_brave_search_client.py` - Brave Search MCP Client
**Path**: `/workspaces/Agent-Framework/mcp_integration/working_brave_search_client.py`
**Lines**: 258 total
**Purpose**: MCP client for Brave Search API operations using the same Docker exec pattern

**Key Imports**:
```python
import asyncio
import json
from typing import Any
from config import get_enabled_servers
```

**Key Class**: `WorkingBraveSearchClient`

**Functions**:
- `__init__(self)` - Initializes with Brave Search configuration from enabled servers
- `async initialize(self) -> bool` - Tests Brave Search container accessibility
- `async _run_docker_command(self, command: list[str]) -> dict[str, Any]` - Docker exec command execution
- `async _run_mcp_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]` - JSON-RPC MCP tool execution
- `async call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]` - Main tool dispatcher
- `get_available_tools(self) -> dict[str, dict[str, Any]]` - Returns Brave Search tools dictionary
- `async close(self)` - Connection cleanup

**Tool Methods**:
- `brave_web_search` - Web search with query, count parameters
- `brave_image_search` - Image search with searchTerm, count parameters  
- `brave_local_search` - Local business search
- `brave_news_search` - News article search with freshness filtering
- `brave_video_search` - Video search with freshness filtering

**Container Configuration**:
- Default container: `agent-framework-mcp-brave-search-1`
- Server path: `/app`
- Communication: JSON-RPC over Docker exec with Node.js server

### 5. `mcp_openai_bot_v2.py` - OpenAI Integration Bot
**Path**: `/workspaces/Agent-Framework/mcp_integration/mcp_openai_bot_v2.py`
**Lines**: 303 total
**Purpose**: OpenAI GPT integration with MCP tools, handles function calling and conversation management

**Key Imports**:
```python
import asyncio
import json
from datetime import datetime
import openai
from config import OPENAI_API_KEY
from multi_mcp_client import MultiMCPClient
```

**Key Class**: `MCPOpenAIBot`

**Functions**:
- `__init__(self, selected_server: str = "filesystem", mcp_client: MultiMCPClient | None = None)` - Initializes with optional external MCP client
- `async initialize(self)` - Sets up MCP connection and validates tools
- `get_available_tools(self)` - Retrieves tools from selected server
- `_create_openai_tools(self)` - Converts MCP tools to OpenAI function calling format
- `async _execute_mcp_function(self, function_name: str, arguments: dict) -> str` - Executes MCP tool and formats response
- `async chat(self, message: str, conversation_history: list = None) -> str` - Main chat interface with function calling
- `async process_message(self, message: str) -> str` - Process user message with MCP tools
- `async close(self)` - Cleanup connections (only if bot owns MCP client)

**Key Features**:
- Supports external MCP client injection for persistence
- Automatic OpenAI function schema generation from MCP tools
- Conversation history management
- Resource ownership tracking (`_owns_mcp_client`)

### 6. `mcp_tab.py` - Streamlit UI Integration
**Path**: `/workspaces/Agent-Framework/mcp_integration/mcp_tab.py`
**Lines**: 312 total
**Purpose**: Streamlit web interface for MCP functionality with server selection and chat interface

**Key Imports**:
```python
import asyncio
import sys
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
import streamlit as st
from multi_mcp_client import MultiMCPClient
# Dynamic import from src directory
from schema import ChatMessage
```

**Key Functions**:
- `async render_mcp_tab() -> None` - Main UI rendering function
- `async draw_mcp_messages(messages_agen: AsyncGenerator[ChatMessage, None]) -> None` - Message display handler
- `async process_mcp_message(user_input: str, mcp_client: MultiMCPClient, selected_server: str, conversation_history: list[ChatMessage] | None = None) -> str` - Message processing with MCP integration

**UI Components**:
- Server selection dropdown with icons and descriptions
- Tool listing with expandable server information
- Quick action buttons for common operations
- Chat interface with message history
- Session state management for persistent connections

**Session State Variables**:
- `mcp_client` - Persistent MultiMCPClient instance
- `mcp_messages` - Chat message history
- `mcp_thread_id` - Conversation thread identifier
- `selected_mcp_server` - Currently selected MCP server

**Quick Actions** (dynamically generated based on available tools):
- Filesystem: List directory, Create directory, Read file, Write file, Move file, Get file info, Search files
- Brave Search: Web search, Image search, Video search, News search, Local search

### 7. `servers/brave_search/server.yaml` - Server Configuration
**Path**: `/workspaces/Agent-Framework/mcp_integration/servers/brave_search/server.yaml`
**Lines**: 57 total
**Purpose**: YAML configuration file defining Brave Search server metadata and tool specifications

**Configuration Structure**:
```yaml
name: "brave-search"
version: "1.0.0"
description: "Web, image, video and news search via Brave API"
icon: "🔍"
enabled: true
priority: 2
container:
  name: "agent-framework-mcp-brave-search-1"
  image: "mcp/brave-search:latest"
  environment:
    - "BRAVE_API_KEY=${BRAVE_API_KEY}"
tools: [5 tool definitions with parameters]
```

**Tool Definitions**:
- `brave_web_search` - Web search with query, count, safesearch, freshness parameters
- `brave_image_search` - Image search with query, count, safesearch parameters
- `brave_video_search` - Video search with query, count, freshness parameters
- `brave_news_search` - News search with query, count, freshness parameters
- `brave_local_search` - Local search with query, count parameters

## Import Dependencies and Relationships

### Dependency Graph:
```
config.py (base configuration)
    ↓
working_mcp_client.py → config.get_enabled_servers()
working_brave_search_client.py → config.get_enabled_servers()
    ↓
multi_mcp_client.py → config.get_enabled_servers(), WorkingMCPClient, WorkingBraveSearchClient
    ↓
mcp_openai_bot_v2.py → config.OPENAI_API_KEY, MultiMCPClient
mcp_tab.py → MultiMCPClient, schema.ChatMessage (from src/)
```

### External Dependencies:
- `openai` - OpenAI API client library
- `streamlit` - Web UI framework
- `dotenv` - Environment variable loading
- `asyncio` - Asynchronous programming
- `docker` - Docker container management (implicit via subprocess)
- `pathlib` - Path manipulation
- `typing` - Type hints

## Current Functionality Flow

1. **Initialization**: `config.py` loads environment variables and server configurations
2. **Server Setup**: `multi_mcp_client.py` initializes working clients for enabled servers
3. **Tool Execution**: User requests route through MultiMCPClient to appropriate working client
4. **UI Interaction**: `mcp_tab.py` provides web interface with server selection and chat
5. **AI Integration**: `mcp_openai_bot_v2.py` connects OpenAI GPT with MCP tools via function calling
6. **Container Communication**: All clients use Docker exec for reliable container communication

## Files for Plugin Organization Target

### Keep As-Is (Core Infrastructure):
- `config.py` - Central configuration (modify to support plugin discovery)
- `mcp_tab.py` - UI integration (minimal changes for plugin support)

### Reorganize Into Plugin Structure:
- `working_mcp_client.py` → `plugins/filesystem/client.py`
- `working_brave_search_client.py` → `plugins/brave_search/client.py`
- `multi_mcp_client.py` → Simplify to plugin manager
- `mcp_openai_bot_v2.py` → Update to work with plugin system

### Configuration Migration:
- Extract server configs from `config.py` to individual `plugins/*/config.yaml` files
- Create plugin discovery mechanism
- Maintain backward compatibility

This analysis shows a well-structured, working MCP integration system that can be cleanly reorganized into a plugin-based architecture while preserving all existing functionality.
