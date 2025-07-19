# MCP Integration - Standalone

This directory contains a standalone MCP (Model Context Protocol) integration that demonstrates how to connect AI agents to MCP servers.

## Files

- `mcp_client.py` - Simple MCP client for connecting to filesystem server
- `mcp_openai_bot.py` - OpenAI bot that can use MCP filesystem tools  
- `mcp_tab.py` - Streamlit UI tab for MCP functionality
- `schema.py` - Standalone schema definitions (ChatMessage, etc.)
- `config.py` - Configuration and environment variable loading
- `test_mcp.py` - Test script for the integration
- `requirements.txt` - Python dependencies

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

The integration connects to the `mcp-filesystem` container defined in the parent `compose.yaml`:
- Container name: `agent-service-toolkit-mcp-filesystem-1`
- Filesystem path: `/projects`
- Available tools: 11 filesystem operations

## Configuration

Environment variables (loaded from parent `.env`):
- `OPENAI_API_KEY` - Required for OpenAI bot
- `MCP_CONTAINER_NAME` - Docker container name (default: agent-service-toolkit-mcp-filesystem-1)
- `MCP_SERVER_PATH` - Server filesystem path (default: /projects)