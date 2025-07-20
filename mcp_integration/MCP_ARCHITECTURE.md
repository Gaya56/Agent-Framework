# MCP Integration Architecture Guide

## Overview

This document outlines the complete Model Context Protocol (MCP) integration architecture, including all files, functions, imports, and workflows. This guide will help you understand the current implementation and add new MCP servers in the future.

## 🎯 What We Achieved

### ✅ Successfully Implemented
- **Persistent MCP Connections**: Fixed connection drops between requests
- **Multi-Server Support**: Filesystem, Brave Search, and GitHub MCP servers
- **Session State Management**: Bot instances cached to maintain connections
- **Separate Working Clients**: Individual client classes for each MCP server
- **Docker Container Communication**: JSON-RPC over stdio with Docker exec
- **Streamlit UI Integration**: Full MCP functionality through web interface

### ✅ Key Breakthrough
The main issue was **connection persistence**. Previously, `MCPOpenAIBot` created new `MultiMCPClient` instances for each request and closed them immediately, causing connection drops. We fixed this by:

1. **External Client Injection**: Modified `MCPOpenAIBot` to accept external MCP client instances
2. **Session State Caching**: Cached bot instances by server type in Streamlit session state
3. **Resource Ownership**: Only close MCP clients that the bot owns

## 📁 Architecture Overview

```
mcp_integration/
├── config.py                      # Configuration and environment variables
├── multi_mcp_client.py           # Main orchestrator for all MCP servers
├── mcp_openai_bot_v2.py          # OpenAI bot with MCP tool integration
├── mcp_tab.py                    # Streamlit UI with persistent connections
├── working_mcp_client.py         # Filesystem MCP client (original pattern)
├── working_brave_search_client.py # Brave Search MCP client
├── working_github_client.py      # GitHub MCP client
├── test_github_functionality.py  # GitHub testing script
└── servers/                      # MCP server configurations
    ├── filesystem/
    │   └── server.yaml
    ├── brave_search/
    │   ├── server.yaml
    │   └── docker-compose.yml
    └── github/
        ├── server.yaml
        └── docker-compose.yml
```

## 🔄 Core Architecture Components

### 1. Configuration Layer (`config.py`)

```python
# Key imports and settings
import os
from pathlib import Path
from dotenv import load_dotenv

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")  
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

# MCP Server configurations
MCP_SERVERS = {
    "filesystem": {
        "name": "Filesystem Server",
        "container": "agent-framework-mcp-filesystem-1",
        "enabled": True
    },
    "brave_search": {
        "name": "Brave Search",
        "container": "agent-framework-mcp-brave-search-1", 
        "enabled": True
    },
    "github": {
        "name": "GitHub",
        "container": "agent-framework-mcp-github-1",
        "enabled": True
    }
}
```

### 2. Working Client Pattern

Each MCP server has its own dedicated client class following this pattern:

```python
class WorkingMCPClient:
    def __init__(self, container_name: str, base_path: str = "/"):
        self.container_name = container_name
        self.base_path = base_path
        self.request_id = 0
    
    def _execute_command(self, command: List[str]) -> str:
        # Docker exec communication
    
    def _send_mcp_request(self, method: str, params: dict = None) -> dict:
        # JSON-RPC protocol implementation
    
    def close(self):
        # Cleanup connections
```

### 3. Multi-Server Orchestrator (`multi_mcp_client.py`)

```python
class MultiMCPClient:
    def __init__(self):
        self.mcp_clients = {}
        self.working_mcp_client = None
        self.brave_search_client = None  
        self.github_client = None
    
    def initialize_servers(self):
        # Initialize all enabled MCP servers
    
    def get_available_tools(self) -> List[str]:
        # Aggregate tools from all servers
    
    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        # Route tool calls to appropriate server
```

### 4. OpenAI Bot Integration (`mcp_openai_bot_v2.py`)

```python
class MCPOpenAIBot:
    def __init__(self, mcp_client=None, openai_api_key=None):
        # Accept external MCP client for persistence
        if mcp_client:
            self.mcp_client = mcp_client
            self.owns_mcp_client = False
        else:
            self.mcp_client = MultiMCPClient()
            self.owns_mcp_client = True
    
    def close(self):
        # Only close owned MCP clients
        if self.owns_mcp_client and self.mcp_client:
            self.mcp_client.close()
```

### 5. Streamlit UI with Persistence (`mcp_tab.py`)

```python
def mcp_tab():
    # Session state management for persistent connections
    if 'mcp_bots' not in st.session_state:
        st.session_state.mcp_bots = {}
    
    # Get or create persistent bot instance
    bot_key = f"{selected_server}_bot"
    if bot_key not in st.session_state.mcp_bots:
        mcp_client = MultiMCPClient()
        mcp_client.initialize_servers()
        st.session_state.mcp_bots[bot_key] = MCPOpenAIBot(
            mcp_client=mcp_client,
            openai_api_key=config.OPENAI_API_KEY
        )
    
    bot = st.session_state.mcp_bots[bot_key]
```

## 🔧 Tool Call Workflow

### Request Flow
1. **User Input** → Streamlit UI (`mcp_tab.py`)
2. **Bot Lookup** → Session state cache check
3. **Tool Routing** → `MultiMCPClient.call_tool()`
4. **Server Selection** → Route to appropriate working client
5. **Docker Communication** → JSON-RPC over stdio
6. **Response Processing** → Format and return results

### Example Tool Call Chain
```python
# User: "Search for Python repositories"
user_input → mcp_tab.py
    ↓
bot.process_message() → mcp_openai_bot_v2.py  
    ↓
mcp_client.call_tool("search_repositories", {...}) → multi_mcp_client.py
    ↓ 
github_client.search_repositories(...) → working_github_client.py
    ↓
docker exec agent-framework-mcp-github-1 → JSON-RPC
    ↓
GitHub API response ← MCP Server
```

## 🐳 Docker Container Configuration

### compose.yaml MCP Services
```yaml
mcp-filesystem:
  container_name: agent-framework-mcp-filesystem-1
  image: mcp/filesystem:latest
  volumes:
    - .:/projects
  command: ["/projects"]
  stdin_open: true
  tty: true

mcp-brave-search:
  container_name: agent-framework-mcp-brave-search-1
  image: mcp/brave-search:latest
  environment:
    - BRAVE_API_KEY=${BRAVE_API_KEY}
  stdin_open: true
  tty: true

mcp-github:
  container_name: agent-framework-mcp-github-1
  image: mcp/github:latest
  environment:
    - GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}
  stdin_open: true
  tty: true
```

## 📝 Key Functions and Methods

### Core MCP Communication
- `_send_mcp_request()` - JSON-RPC protocol implementation
- `_execute_command()` - Docker exec wrapper
- `initialize_servers()` - Multi-server startup
- `call_tool()` - Tool routing and execution

### Session Management  
- `get_or_create_bot()` - Persistent bot instances
- `close()` - Resource cleanup
- Session state caching in Streamlit

### Tool Integration
- `get_available_tools()` - Tool discovery
- OpenAI function calling integration
- Dynamic tool registration

## 🚀 Adding New MCP Servers

### Step 1: Create Working Client
```python
# working_newserver_client.py
class WorkingNewServerClient:
    def __init__(self, container_name: str):
        self.container_name = container_name
        # Follow existing pattern...
    
    def your_tool_method(self, param1: str) -> dict:
        return self._send_mcp_request("tools/call", {
            "name": "your_tool_name", 
            "arguments": {"param1": param1}
        })
```

### Step 2: Add to Configuration
```python
# config.py
MCP_SERVERS["newserver"] = {
    "name": "New Server",
    "container": "agent-framework-mcp-newserver-1",
    "enabled": True
}
```

### Step 3: Update Multi-Client
```python
# multi_mcp_client.py
from .working_newserver_client import WorkingNewServerClient

class MultiMCPClient:
    def __init__(self):
        self.newserver_client = None
    
    def initialize_servers(self):
        if config.MCP_SERVERS["newserver"]["enabled"]:
            self.newserver_client = WorkingNewServerClient(
                config.MCP_SERVERS["newserver"]["container"]
            )
```

### Step 4: Add Docker Service
```yaml
# compose.yaml
mcp-newserver:
  container_name: agent-framework-mcp-newserver-1
  image: mcp/newserver:latest
  environment:
    - API_KEY=${NEW_SERVER_API_KEY}
  stdin_open: true
  tty: true
```

### Step 5: Create Server Configuration
```yaml
# servers/newserver/server.yaml
name: "newserver"
version: "1.0.0"
description: "New Server Description"
icon: "🆕"
enabled: true
priority: 4

container:
  name: "agent-framework-mcp-newserver-1"
  image: "mcp/newserver:latest"
  environment:
    - "API_KEY=${NEW_SERVER_API_KEY}"

tools:
  - name: "your_tool_name"
    description: "Tool description"
```

## 🧹 Files to Clean Up

### Files We No Longer Need:

1. **Legacy Client Files** (if any direct MCP implementations exist):
   - Any files ending in `_client.py` that don't follow the working client pattern
   - Old MCP connection attempts

2. **Debugging/Test Files** (keep test_github_functionality.py for reference):
   - Any temporary test files you created during debugging
   - Old connection test scripts

3. **Unused Configuration Files**:
   - Duplicate server configurations
   - Old environment variable definitions

### Files to Keep:
- ✅ All `working_*_client.py` files (they work!)
- ✅ `multi_mcp_client.py` (orchestrator)
- ✅ `mcp_openai_bot_v2.py` (persistent bot)
- ✅ `mcp_tab.py` (UI integration)
- ✅ `config.py` (configuration)
- ✅ `test_github_functionality.py` (for reference)
- ✅ All server configurations in `servers/` directory

## 🔍 Troubleshooting Guide

### Common Issues:
1. **Connection Drops**: Check session state management
2. **Tool Not Found**: Verify server initialization  
3. **Authentication Errors**: Check environment variables in containers
4. **Container Communication**: Ensure `stdin_open: true` and `tty: true`

### Debugging Commands:
```bash
# Check container status
docker ps | grep mcp

# Test MCP server directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | \
  docker exec -i agent-framework-mcp-github-1 node dist/index.js

# Check environment variables
docker exec agent-framework-mcp-github-1 env | grep API
```

## 📊 Success Metrics

- ✅ **Brave Search**: Working with persistent connections
- ⏳ **GitHub**: MCP server responding, needs valid API token
- ✅ **Filesystem**: Working with persistent connections  
- ✅ **Multi-Request Support**: No connection drops between requests
- ✅ **Session State**: Bot instances properly cached
- ✅ **Container Communication**: JSON-RPC over Docker exec working

---

This architecture provides a robust, scalable foundation for adding new MCP servers while maintaining persistent connections and clean separation of concerns.
