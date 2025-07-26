# MCP Integration

The `mcp_integration` package adds Model Context Protocol (MCP) support to the Agent‑Framework. It allows the Streamlit application and the OpenAI‑powered agents to call external services such as a filesystem or Brave Search through a unified interface. The original flat structure was replaced with a plugin‑based architecture so that new servers can be added without changing core code.

## Directory Overview

- **`core/`** – Core logic for MCP integration. This folder contains the environment configuration (`config.py`), the multi‑server client implementation (`multi_client.py`), the OpenAI bot wrapper (`mcp_openai_bot.py`) and the plugin manager. The plugin manager scans the `plugins/` directory, parses each `config.yaml` and dynamically imports the referenced client class.

- **`clients/`** – Concrete implementations of server clients. Each client knows how to initialise its container, list available tools and execute them. For example, the filesystem client provides file operations such as listing, reading and writing files, while the Brave Search client implements web, image and news search tools.

- **`plugins/`** – One directory per MCP server. Each plugin contains a `config.yaml` that describes the server: its name, description, Docker container name, server path, icon, whether it is enabled and the list of exposed tools. The YAML may specify the fully qualified client class or rely on naming conventions.

- **`ui/`** – Streamlit components and UI logic. The `mcp_tab.py` file here implements the MCP tab used in the `streamlit_app.py`; it lets users pick a server, view available tools and send requests.

- **`utils/`** – Optional helper functions (currently minimal).

- **`mcp_tab.py`** – A thin wrapper that re‑exports `render_mcp_tab`, `draw_mcp_messages` and `process_mcp_message` from `ui/mcp_tab.py`, preserving backwards compatibility with `streamlit_app.py`.

## How It Works

At startup the plugin manager reads every subdirectory in `plugins/`, parses its `config.yaml` and loads the specified client class. The `MultiMCPClient` then uses these configurations to create one `MCPServerClient` per enabled server. Each `MCPServerClient` wraps a client instance and exposes methods to list available tools and call them.

The Streamlit UI obtains the list of servers and tools from the `MultiMCPClient` and builds a server selector and quick‑action buttons. When a user sends a message, the UI forwards it and the conversation history to the OpenAI bot. The bot converts available MCP tools into the OpenAI function‑calling schema, calls OpenAI's chat API and executes any returned tool calls via the MCP client before returning the final answer.

## Why Use Plugins?

This architecture decouples server definitions from core code. To add a new MCP server you only need to create a plugin folder with a `config.yaml` and a client class; no changes to `multi_client.py` or the UI are required. Dynamic loading reduces boilerplate, centralises configuration and makes it easy to enable or disable servers via YAML. The separation of core, clients and UI improves maintainability and supports independent testing.

## Core Benefits

- **Dynamic discovery**: The plugin manager automatically discovers enabled servers and loads their client classes.

- **Extensibility**: Adding a new server requires only a new plugin directory and client class.

- **Separation of concerns**: Core logic deals with loading and routing, clients implement server‑specific logic, and the UI handles user interaction.

- **Backward compatibility**: The wrapper `mcp_tab.py` preserves existing imports so that `streamlit_app.py` does not need modification.
## How It Works

At startup the plugin manager reads every subdirectory in `plugins/`, parses its `config.yaml` and loads the specified client class. The `MultiMCPClient` then uses these configurations to create one `MCPServerClient` per enabled server. Each `MCPServerClient` wraps a client instance and exposes methods to list available tools and call them. The Streamlit UI
obtains the list of servers and tools from the MultiMCPClient and builds a
server selector and quick‑action buttons
GitHub
. When a user
sends a message, the UI forwards it and the conversation history to the
OpenAI bot. The bot converts available MCP tools into the OpenAI
function‑calling schema, calls OpenAI’s chat API and executes any returned
tool calls via the MCP client before returning the final answer
GitHub
.
Why use plugins?

This architecture decouples server definitions from core code. To add a new
MCP server you only need to create a plugin folder with a config.yaml and a
client class; no changes to multi_client.py or the UI are required.
Dynamic loading reduces boilerplate, centralises configuration and makes it
easy to enable or disable servers via YAML. The separation of core, clients
and UI improves maintainability and supports independent testing.
Core benefits

    Dynamic discovery: the plugin manager automatically discovers enabled
    servers and loads their client classes
    GitHub
    .

    Extensibility: adding a new server requires only a new plugin
    directory and client class.

    Separation of concerns: core logic deals with loading and routing,
    clients implement server‑specific logic, and the UI handles user
    interaction.

    Backward compatibility: the wrapper mcp_tab.py preserves existing
    imports so that streamlit_app.py does not need modification