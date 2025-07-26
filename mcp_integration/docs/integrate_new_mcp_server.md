# Integrate a New MCP Server

This guide explains how to add a new server to the plugin‑based MCP integration. A server is any external service—such as a filesystem, database or API—that follows the Model Context Protocol (MCP) and exposes a set of callable tools. New servers are integrated via plugins so that no changes are required in the core or UI.

## 1. Create a Plugin Folder

Choose a unique identifier for your server (e.g. `my_service`) and create a folder `mcp_integration/plugins/my_service`. Inside it, add:

- `__init__.py` – Empty file so Python can import the package.

- `config.yaml` – YAML file that describes the server. The plugin manager scans every subdirectory under `plugins/` and loads the YAML configuration and client class dynamically.
## 2. Write config.yaml

Each plugin configuration must define server metadata and tool schemas. The following fields are required:

- `name` – Human‑readable name of the server.

- `description` – Summary of what the server does.

- `container_name` – Name of the Docker container running the MCP server.

- `server_path` – Base path inside the container (for file operations).

- `icon` – Emoji or icon used in the UI.

- `enabled` – Set to `true` to load the server or `false` to ignore it.

- `client_class` – Fully qualified Python path to the client class that implements the tools.

- `tools` – A mapping of tool names to descriptions and parameter schemas.

A template config looks like this:

```yaml
# plugins/my_service/config.yaml
name: "My Service"
description: "Describe what this server does"
container_name: "agent-framework-mcp-my-service-1"
server_path: "/app"              # path inside the container
icon: "🧩"                        # emoji or icon for the UI
enabled: true                    # disable to hide the server
client_class: "mcp_integration.clients.my_service_client.MyServiceClient"
tools:
  my_tool:
    description: "What this tool does"
    parameters:
      arg1: "Description of the first argument"
      arg2: "Description of the second argument"
```

Under `tools`, list each function the server exposes. Provide a human‑readable description and a dictionary of input parameters. At runtime the OpenAI bot converts these definitions into an OpenAI function schema and executes any tool calls via the MCP client.
## 3. Implement the Client Class

Create `mcp_integration/clients/my_service_client.py`. The class should:

- Accept the plugin configuration in its constructor and read `container_name` and `server_path`.

- Define an `available_tools` dictionary mapping tool names to their descriptions and parameters, similar to the filesystem client.

- Implement `initialize()` to connect to the service (e.g. test docker exec or set up API keys) and return `True` when ready.

- Implement `call_tool(tool_name: str, arguments: dict)` to execute the selected tool and return a dictionary with either an error or content list. Follow the pattern used in the Brave Search client, which parses JSON‑RPC responses and reports errors.

- Provide a `get_available_tools()` method that returns the `available_tools` mapping.

A minimal template is shown below:

```python
# clients/my_service_client.py
from typing import Any

class MyServiceClient:
    def __init__(self, config: dict[str, Any] | None = None):
        # Read config; fallback to sensible defaults
        self.container_name = config.get("container_name", "agent-framework-mcp-my-service-1")
        self.server_path = config.get("server_path", "/app")
        self.is_initialized = False
        self.available_tools = {
            "my_tool": {
                "description": "What this tool does",
                "parameters": {"arg1": "Describe arg1", "arg2": "Describe arg2"}
            }
        }

    async def initialize(self) -> bool:
        """Connect to the underlying service."""
        # Perform setup here (e.g. docker exec, API auth)
        self.is_initialized = True
        return True

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return a result."""
        if not self.is_initialized:
            return {"error": "Client not initialized"}
        if tool_name not in self.available_tools:
            return {"error": f"Unknown tool: {tool_name}"}
        # Add logic here to call the service; return content as a list of
        # message blocks, e.g. {"content": [{"type": "text", "text": "Result"}]}
        return {"content": [{"type": "text", "text": f"Executed {tool_name} with {arguments}"}]}

    def get_available_tools(self) -> dict[str, dict]:
        return self.available_tools
```

You can extend this template to use Docker, HTTP or JSON‑RPC depending on how your service communicates. Refer to the existing clients for examples of initialisation and tool execution logic.

If you omit the `client_class` field from `config.yaml`, the plugin manager will fall back to naming conventions (`mcp_integration.clients.<server>_client` and `<ServerName>Client`).

## 4. Test the New Server

- Ensure that the Docker container or service for your server is running.

- Verify that `config.yaml` has `enabled: true` and references the correct `client_class`.

- Run `streamlit run src/streamlit_app.py` and open the MCP tab. The new server should appear in the server selector, and its tools should be listed.

- Select your server and call its tools. If a tool fails, review your client logic and container logs.

- Observe the console; `MultiMCPClient` should report loading the plugin and initialising your server.

## Final Checklist

- Plugin folder (`plugins/my_service`) created with `__init__.py`.

- `config.yaml` includes `name`, `description`, `container_name`, `server_path`, `icon`, `enabled`, `client_class` and `tools` fields.

- Client class implemented in `clients/` and referenced correctly.

- Server container is running and accessible.

- Server appears in the MCP tab and its tools execute without errors.
