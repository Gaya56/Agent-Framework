---
applyTo: '**'
---

# MCP Integration Implementation Guide for Agent Framework

## 🎯 Project Context & Objectives

This project implements a **plug-and-play MCP (Model Context Protocol) architecture** in the `/workspaces/Agent-Framework/mcp_integration` directory. The integration is designed to:

- **Isolation First**: Keep all MCP functionality separate from `/src` to avoid breaking existing code
- **Multi-Server Support**: Support unlimited MCP servers through a unified client interface  
- **Production Ready**: Use Docker exec transport for reliability (avoiding asyncio/stdio issues)
- **Plug-and-Play**: Add new servers by creating server directories with YAML configs

## ✅ Current Implementation Status

### **Successfully Integrated Servers:**
- ✅ **Filesystem Server** (`mcp/filesystem:latest`) - 8 tools working perfectly
- ✅ **Brave Search Server** (`mcp/brave-search:latest`) - 5 search tools working perfectly

### **Architecture Components:**
- ✅ **`multi_mcp_client.py`** - Multi-server client manager with Docker exec transport
- ✅ **`config.py`** - Dynamic server configuration system with environment validation
- ✅ **`mcp_tab.py`** - Streamlit UI integration with server selection and tool execution
- ✅ **`mcp_openai_bot_v2.py`** - OpenAI function calling integration with MCP tools
- ✅ **`servers/`** directory with plug-and-play server definitions

### **Current Working Directory Structure:**
```
/workspaces/Agent-Framework/mcp_integration/
├── config.py                    # ✅ Server registry & validation
├── multi_mcp_client.py          # ✅ Multi-server client manager  
├── mcp_tab.py                   # ✅ Streamlit UI integration
├── mcp_openai_bot_v2.py         # ✅ OpenAI bot with MCP tools
├── working_mcp_client.py        # 📝 Legacy reference implementation
├── servers/                     # ✅ Plug-and-play server directory
│   └── brave_search/           # ✅ Successfully integrated
│       ├── server.yaml         # ✅ Server definition
│       └── docker-compose.yml  # ✅ Container configuration
└── documentation/              # 📚 Research and guides
    ├── README.MD
    ├── PLUGIN_ARCHITECTURE_RESEARCH.md
    └── SOLUTION_SUMMARY.MD
```

## 🚀 Proven Integration Pattern - How Brave Search Was Added

The Brave Search integration demonstrates the complete plug-and-play workflow:

### 1. **Server Directory Creation**
Created `/workspaces/Agent-Framework/mcp_integration/servers/brave_search/` with:
- `server.yaml` - Defines server metadata, container config, and tool specifications
- `docker-compose.yml` - Standalone container service definition

### 2. **Configuration Registration**  
Extended `config.py` with `brave_search` entry containing:
- Server metadata (name, description, icon)
- Container configuration (name, environment variables)
- Tool definitions (5 search tools with parameters)
- Environment validation for `BRAVE_API_KEY`

### 3. **Client Implementation**
Extended `multi_mcp_client.py` with:
- `_call_brave_search_tool()` method for HTTP API calls
- JSON request/response handling via curl in Docker container
- Result formatting for different search types (web, image, video, news, local)
- Error handling and validation

### 4. **UI Integration**
Updated `mcp_tab.py` with:
- Automatic server discovery from config
- Quick actions for search operations
- Tool parameter forms and result display

### 5. **Container Integration**
Added to main `compose.yaml`:
- `mcp-brave-search` service with official image
- Environment variable injection from `.env`
- Health checks and restart policies

## 📋 Step-by-Step Guide for Adding New MCP Servers

### **Step 1: Create Server Directory Structure**

```bash
# Create server directory
mkdir -p /workspaces/Agent-Framework/mcp_integration/servers/{SERVER_NAME}/

# Example for GitHub server
mkdir -p /workspaces/Agent-Framework/mcp_integration/servers/github/
```

### **Step 2: Define Server Configuration (`server.yaml`)**

Create a comprehensive server definition following the proven pattern:

```yaml
name: "{server-name}"
version: "1.0.0"
description: "Brief description of server functionality"
icon: "🔧"  # Appropriate emoji
enabled: true
priority: 3  # Order in UI (filesystem=1, brave_search=2, etc.)

container:
  name: "agent-framework-mcp-{server-name}-1"
  image: "mcp/{server-name}:latest"  # Official image
  ports:
    - "8112:8080"  # Adjust port as needed
  environment:
    - "API_KEY=${API_KEY_ENV_VAR}"
    - "OTHER_CONFIG=${OTHER_ENV_VAR}"

tools:
  - name: "tool_name"
    description: "What this tool does"
    parameters:
      param1: "Parameter description (required/optional)"
      param2: "Another parameter"
  # Add all tools the server supports

dependencies: []
health_check:
  endpoint: "/health"  # If server provides health endpoint
  interval: 30
  timeout: 10
  retries: 3
```

### **Step 3: Create Docker Compose Service (`docker-compose.yml`)**

```yaml
version: '3.8'

services:
  mcp-{server-name}:
    container_name: agent-framework-mcp-{server-name}-1
    image: mcp/{server-name}:latest
    environment:
      - API_KEY=${API_KEY_ENV_VAR}
      - OTHER_CONFIG=${OTHER_ENV_VAR}
    ports:
      - "8112:8080"  # Adjust port
    restart: unless-stopped
    stdin_open: true
    tty: true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### **Step 4: Register Server in `config.py`**

Add new server entry to `MCP_SERVERS` dictionary:

```python
"{server_id}": {
    "name": "Server Display Name",
    "description": "What the server does",
    "container_name": os.getenv("MCP_{UPPER}_CONTAINER_NAME", "agent-framework-mcp-{server-name}-1"),
    "server_path": "/",  # Base path if applicable
    "icon": "🔧",
    "enabled": True,
    "tools": {
        "tool_name": {
            "description": "Tool description",
            "parameters": {
                "param1": "Parameter description",
                "param2": "Another parameter"
            }
        },
        # Add all tools
    }
}
```

Add environment validation:
```python
# Validate API key if server is enabled
if MCP_SERVERS.get("{server_id}", {}).get("enabled", False) and not API_KEY:
    print("⚠️ Warning: API_KEY is not set but {Server Name} is enabled. Please set it in .env file.")
```

### **Step 5: Implement Client Methods in `multi_mcp_client.py`**

Add server-specific tool execution method:

```python
async def _call_{server_name}_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute {server-name}-specific tools"""
    import json
    
    # Build MCP request payload
    mcp_request = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    json_payload = json.dumps(mcp_request)
    
    # Execute via HTTP (if server has HTTP interface)
    curl_cmd = [
        "sh", "-c",
        f"curl -s -X POST http://localhost:8080 -H 'Content-Type: application/json' -d '{json_payload}'"
    ]
    
    # OR execute via stdin (if server uses stdio protocol)
    # stdin_cmd = [
    #     "sh", "-c", 
    #     f"echo '{json_payload}' | docker exec -i {self.container_name} /app/server"
    # ]
    
    result = await self._run_docker_command(curl_cmd)
    
    if result["success"]:
        try:
            response_data = json.loads(result["output"])
            
            if "error" in response_data:
                return {"error": f"{Server Name} API error: {response_data['error']}"}
            
            if "result" in response_data:
                formatted_results = self._format_{server_name}_results(tool_name, response_data["result"])
                return {
                    "content": [{
                        "type": "text",
                        "text": formatted_results
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Tool completed: {result['output']}"
                    }]
                }
                
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse response: {e}\nRaw output: {result['output']}"}
    else:
        return {"error": f"Failed to call {Server Name} API: {result['error']}"}

def _format_{server_name}_results(self, tool_name: str, results: dict) -> str:
    """Format server results for display"""
    # Implement tool-specific formatting
    if tool_name == "specific_tool":
        return f"Formatted results for {tool_name}: {results}"
    
    # Default formatting
    return f"Results: {str(results)}"
```

Update the main `call_tool` routing:

```python
async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute MCP tool via docker commands"""
    if not self.is_initialized:
        return {"error": f"{self.config['name']} not initialized"}
    
    available_tools = self.get_available_tools()
    if tool_name not in available_tools:
        return {"error": f"Unknown tool '{tool_name}' for {self.config['name']}"}
    
    try:
        if self.server_id == "filesystem":
            return await self._call_filesystem_tool(tool_name, arguments)
        elif self.server_id == "brave_search":
            return await self._call_brave_search_tool(tool_name, arguments)
        elif self.server_id == "{server_id}":
            return await self._call_{server_name}_tool(tool_name, arguments)
        else:
            return {"error": f"Tool execution not yet implemented for {self.config['name']}"}
            
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
```

### **Step 6: Update Environment Variables**

Add required environment variables to `.env`:

```bash
# {Server Name} Configuration
API_KEY_ENV_VAR=your_api_key_here
MCP_{UPPER}_CONTAINER_NAME=agent-framework-mcp-{server-name}-1  # Optional override
```

### **Step 7: Add to Main Docker Compose**

Add the new service to `/workspaces/Agent-Framework/compose.yaml`:

```yaml
  mcp-{server-name}:
    container_name: agent-framework-mcp-{server-name}-1
    image: mcp/{server-name}:latest
    environment:
      - API_KEY=${API_KEY_ENV_VAR}
    ports:
      - "8112:8080"
    restart: unless-stopped
    stdin_open: true
    tty: true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### **Step 8: Test Integration**

1. **Container Test**:
   ```bash
   docker compose up -d mcp-{server-name}
   docker ps | grep {server-name}
   curl http://localhost:8112/health
   ```

2. **Python Client Test**:
   ```python
   from mcp_integration.multi_mcp_client import MultiMCPClient
   
   client = MultiMCPClient()
   await client.initialize()
   
   result = await client.call_tool("{server_id}", "tool_name", {"param": "value"})
   print(result)
   ```

3. **UI Test**:
   - Run Streamlit app: `streamlit run src/streamlit_app.py`
   - Go to MCP tab
   - Select new server from dropdown
   - Test tool execution

4. **Bot Integration Test**:
   ```python
   from mcp_integration.mcp_openai_bot_v2 import MCPOpenAIBot
   
   bot = MCPOpenAIBot()
   await bot.initialize_mcp()
   
   response = await bot.chat("Use {server name} to...")
   print(response)
   ```

## 🎯 Next Implementation Target: GitHub MCP Server

Based on research, here's the specific plan for GitHub server integration:

### **GitHub Server Specifications:**
- **Official Image**: `github/github-mcp-server:latest` (new official) or `mcp/github:latest` (legacy)
- **Protocol**: STDIO (no HTTP interface)
- **Authentication**: `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable
- **Key Tools**: `create_or_update_file`, `search_repositories`, `create_issue`, `create_pull_request`, `get_file_contents`, `search_code`, `list_issues`, etc.

### **GitHub Integration Steps:**

1. **Create `/workspaces/Agent-Framework/mcp_integration/servers/github/`**

2. **Define `server.yaml`**:
   ```yaml
   name: "github"
   version: "1.0.0"
   description: "GitHub API operations - repos, issues, files, PRs"
   icon: "🐙"
   enabled: true
   priority: 3

   container:
     name: "agent-framework-mcp-github-1"
     image: "github/github-mcp-server:latest"
     ports: []  # STDIO protocol, no HTTP
     environment:
       - "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}"

   tools:
     - name: "create_or_update_file"
       description: "Create or update a file in a repository"
       parameters:
         owner: "Repository owner (required)"
         repo: "Repository name (required)"
         path: "File path (required)"
         content: "File content (required)"
         message: "Commit message (required)"
         branch: "Target branch (optional)"
     - name: "search_repositories"
       description: "Search GitHub repositories"
       parameters:
         query: "Search query (required)"
         sort: "Sort by stars, forks, updated (optional)"
     # Add other tools...
   ```

3. **Implement STDIO-based client method**:
   ```python
   async def _call_github_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
       """Execute GitHub tools via STDIO protocol"""
       import json
       
       mcp_request = {
           "method": "tools/call",
           "params": {
               "name": tool_name,
               "arguments": arguments
           }
       }
       
       json_payload = json.dumps(mcp_request)
       
       # Execute via STDIO 
       stdin_cmd = [
           "sh", "-c", 
           f"echo '{json_payload}' | docker exec -i {self.container_name} /app/server"
       ]
       
       result = await self._run_docker_command(stdin_cmd)
       # Handle response...
   ```

4. **Environment setup**:
   ```bash
   # Add to .env
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
   ```

## 🔧 Key Implementation Principles

1. **Isolation**: All MCP code lives in `/workspaces/Agent-Framework/mcp_integration/`
2. **Docker Exec Transport**: Proven reliable approach, avoid stdio asyncio issues
3. **Configuration-Driven**: Servers defined in `config.py`, auto-discovered by UI
4. **Error Handling**: Comprehensive error handling and user-friendly messages
5. **Extensible Design**: Adding new servers requires minimal code changes
6. **Testing Strategy**: Container, client, UI, and bot integration tests for each server

## 🚦 Development Workflow

1. **Research**: Verify official container image and API documentation
2. **Create**: Set up server directory with YAML and compose files
3. **Register**: Add to `config.py` with full tool specifications
4. **Implement**: Add client method for tool execution
5. **Test**: Container → Client → UI → Bot integration testing
6. **Document**: Update README and instructions for future servers

This proven pattern ensures reliable, maintainable MCP server integrations that work seamlessly with the existing Agent Framework without affecting the core `/src` codebase.
