# MCP Integration - Multi-Server Architecture

This directory contains a **production-ready MCP (Model Context Protocol) integration** that demonstrates how to connect AI agents to multiple MCP servers using a plug-and-play architecture.

## 🚀 **Current Status: WORKING**

✅ **Streamlit Integration** - MCP tab fully integrated into main app  
✅ **Filesystem Server** - 8 tools working perfectly  
✅ **Docker Exec Approach** - Reliable, no asyncio issues  
✅ **Multi-Server Ready** - Architecture supports unlimited servers  

## 📁 **Files**

### **Core Components:**
- **`multi_mcp_client.py`** - Multi-server MCP client manager ✅ PRODUCTION READY
- **`config.py`** - Dynamic server configuration system ✅ PRODUCTION READY  
- **`mcp_tab.py`** - Streamlit UI tab for MCP functionality ✅ PRODUCTION READY

### **Legacy/Reference:**
- **`working_mcp_client.py`** - Single-server reference implementation
- **`mcp_openai_bot_v2.py`** - OpenAI bot integration example  

## 🏗️ **Architecture Overview**

```
Streamlit App
├── 💬 Chat Tab (LangGraph Agents)
└── 📁 MCP Tab (Multi-Server Interface)
    ├── 📁 Filesystem Server (agent-framework-mcp-filesystem-1)
    ├── 🧠 Memory Server (future: agent-framework-mcp-memory-1)  
    ├── 🔍 Search Server (future: agent-framework-mcp-search-1)
    └── 🔌 Custom Servers (plug-and-play)
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the MCP server container:**
   ```bash
   # From the parent directory
   cd ..
   docker compose up -d mcp-filesystem
   ```

3. **Set environment variables:**
   - The integration loads `.env` from the parent directory
   - Required: `OPENAI_API_KEY`
   - Optional: `MCP_CONTAINER_NAME`, `MCP_SERVER_PATH`

## Testing

Run the test suite:
```bash
python test_mcp.py
```

## Usage Examples

### MCP Client Only
```python
from mcp_client import MCPClient

client = MCPClient()
await client.initialize()

# List directory
result = await client.call_tool("list_directory", {"path": "/projects"})
print(result)
```

### OpenAI Bot with MCP Tools
```python
from mcp_openai_bot import MCPOpenAIBot

bot = MCPOpenAIBot()
await bot.initialize_mcp()

# Chat with AI that can use filesystem tools
response = await bot.chat("What files are in the /projects directory?")
print(response)
```

### Streamlit UI
```python
# This requires the full Streamlit environment
import streamlit as st
from mcp_tab import render_mcp_tab

# In a Streamlit app
await render_mcp_tab()
```

## Docker Container

The integration connects to MCP containers defined in the parent `compose.yaml`:

- **Current:** `agent-framework-mcp-filesystem-1` 
  - Filesystem path: `/projects`
  - Available tools: 8 filesystem operations
- **Future:** Additional servers will follow the same pattern

## Configuration

Environment variables (loaded from parent `.env`):

- `OPENAI_API_KEY` - Required for OpenAI bot
- `MCP_CONTAINER_NAME` - Docker container name pattern
- `MCP_SERVER_PATH` - Server filesystem path (default: /projects)

## 🎯 **Next: Plug & Play Architecture**

**Goal:** Add new MCP servers by simply:
1. Creating a new directory in `/servers/`
2. Adding Docker container config
3. Server auto-discovered and available immediately

**Target Servers:**
- 🧠 **Memory Server** - Knowledge graph and embeddings
- 🔍 **Search Server** - Web search and information retrieval  
- 💾 **Database Server** - SQL operations and queries
- 📧 **Email Server** - Send/receive email functionality