---
applyTo: '*/workspaces/Agent-Framework/mcp_integration*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.Below is a comprehensive migration guide that covers every file and import affected by the reorganisation we discussed.  It is written so that, when you follow it step by step, the application will still run exactly as it does now—`streamlit_app.py` will continue to find `render_mcp_tab` from the top‑level `mcp_tab.py`, and your MCP clients and tools will work as before.

---

## 1. Create the new directory layout

Inside `mcp_integration`, create the following directories, each with an empty `__init__.py` so they are importable:

```
mcp_integration/
    ui/
    core/
    clients/
    plugins/
    utils/
```

Each subfolder should include `__init__.py` (even if it is empty) so Python can import from it.

## 2. Move and rename files

1. Move `config.py` into `core/` and rename it `config.py` (the filename stays the same, only its location changes).
2. Move `multi_mcp_client.py` into `core/` and rename it `multi_client.py`.
3. Move `mcp_openai_bot_v2.py` into `core/` and rename it `mcp_openai_bot.py`.
4. Move `working_mcp_client.py` into `clients/` and rename it `filesystem_client.py`.
5. Move `working_brave_search_client.py` into `clients/` and rename it `brave_search_client.py`.
6. Move the YAML config(s) under `mcp_integration/servers/` into `plugins/<server>/config.yaml`.  For example, move `servers/brave_search/server.yaml` to `plugins/brave_search/config.yaml`.

   * If there isn’t a YAML file for the filesystem server, create `plugins/filesystem/config.yaml` based on the settings in the `filesystem` entry of your original `MCP_SERVERS` dictionary.  This should contain at least: `name`, `description`, `container_name`, `server_path`, `icon`, `enabled`, and a list of tool definitions.
7. Optionally move documentation like `CLEANUP_GUIDE.md` and `MCP_ARCHITECTURE.md` into a separate `docs/` folder.

At this point, your new folder might look like this (only showing the relevant parts):

```
mcp_integration/
    mcp_tab.py          # thin wrapper (see step 10)
    core/
        __init__.py
        config.py       # original config.py
        multi_client.py # original multi_mcp_client.py
        mcp_openai_bot.py # original mcp_openai_bot_v2.py
        plugin_manager.py  # new file (see section 5)
    clients/
        __init__.py
        filesystem_client.py   # original working_mcp_client.py
        brave_search_client.py # original working_brave_search_client.py
    plugins/
        filesystem/
            __init__.py
            config.yaml       # new YAML built from MCP_SERVERS['filesystem']
        brave_search/
            __init__.py
            config.yaml       # moved from servers/brave_search/server.yaml
    ui/
        __init__.py
        mcp_tab.py       # original mcp_tab.py content goes here
    utils/
        __init__.py
        helpers.py       # optional, for common functions
```

## 3. Adjust `core/config.py`

Open `core/config.py` (original `config.py`) and make the following adjustments:

1. Keep environment loading at the top:

   ```python
   import os
   from pathlib import Path
   from typing import Any
   from dotenv import load_dotenv

   env_path = Path(__file__).parent.parent / ".env"
   load_dotenv(env_path)

   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
   ```

2. Remove the `MCP_SERVERS` dictionary.  Instead, the config module should rely on a plugin manager (see section 5) to load server definitions dynamically.

3. Provide helper functions that delegate to the plugin manager:

   ```python
   from .plugin_manager import load_plugins

   def get_enabled_servers() -> dict[str, dict[str, Any]]:
       """Return only enabled plugins from plugin manager."""
       plugins = load_plugins()
       return {sid: cfg for sid, cfg in plugins.items() if cfg.get("enabled", False)}

   def get_server_config(server_id: str) -> dict[str, Any]:
       """Return configuration for a specific server."""
       return load_plugins().get(server_id, {})
   ```

4. If you plan to keep simple console output (the “Configuration loaded” print statements), update their references accordingly.

These changes will allow your clients and multi‑client to call `get_enabled_servers()` and `get_server_config()` exactly as before, but the data will now come from the plugin system rather than a hard‑coded dictionary.

## 4. Create `core/plugin_manager.py`

Create a new file `core/plugin_manager.py`.  Its job is to scan the `plugins` directory, load the YAML files, and (optionally) import the corresponding client class.  A minimal implementation might look like this:

```python
from pathlib import Path
import yaml
import importlib

_PLUGINS = None

def load_plugins() -> dict[str, dict]:
    """
    Discover and load all plugins.  Returns a dictionary keyed by server_id.
    The returned dictionary should include the configuration and a reference
    to the client class.
    """
    global _PLUGINS
    if _PLUGINS is not None:
        return _PLUGINS

    plugins_dir = Path(__file__).parent.parent / "plugins"
    plugins = {}

    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir():
            config_file = plugin_path / "config.yaml"
            if config_file.exists():
                config = yaml.safe_load(config_file.read_text())
                # Expect the YAML to have a "server_id" (folder name by default)
                server_id = plugin_path.name
                # Optionally allow the YAML to specify the client class
                client_path = config.get("client_class", None)
                if client_path:
                    module_name, class_name = client_path.rsplit(".", 1)
                    module = importlib.import_module(module_name)
                    client_class = getattr(module, class_name)
                else:
                    # Fallback: use naming convention
                    module_name = f"mcp_integration.clients.{server_id}_client"
                    class_name = f"{server_id.title().replace('_', '')}Client"
                    module = importlib.import_module(module_name)
                    client_class = getattr(module, class_name)
                config["client_class"] = client_class
                config["server_id"] = server_id
                plugins[server_id] = config
    _PLUGINS = plugins
    return plugins
```

* Ensure you have `import yaml` available (install `PyYAML` if not already present).
* Each plugin YAML can specify a `client_class` field like `mcp_integration.clients.brave_search_client.BraveSearchClient`.  If not provided, the plugin manager uses a naming convention to locate the client.

## 5. Adjust `core/multi_client.py` (original `multi_mcp_client.py`)

1. At the top of the file, update imports:

   ```python
   from typing import Any
   from .config import get_enabled_servers
   # You no longer need to import specific clients here.
   from .plugin_manager import load_plugins
   ```

2. In `MCPServerClient.__init__`, remove the hard‑coded if/else that selects `WorkingMCPClient` or `WorkingBraveSearchClient`.  Instead, accept a `client_class` argument:

   ```python
   class MCPServerClient:
       def __init__(self, server_id: str, config: dict[str, Any], client_class: type):
           self.server_id = server_id
           self.config = config
           self.container_name = config.get("container_name")
           self.server_path = config.get("server_path")
           self.working_client = client_class()
           self.is_initialized = False
   ```

3. In `MultiMCPClient.initialize`, call the plugin manager to get all plugins, then instantiate `MCPServerClient` with the appropriate client class:

   ```python
   async def initialize(self) -> bool:
       print("🔄 Initializing Multi‑MCP Client...")
       plugins = load_plugins()
       for server_id, config in plugins.items():
           if not config.get("enabled"):
               continue
           client_class = config["client_class"]
           server_client = MCPServerClient(server_id, config, client_class)
           success = await server_client.initialize()
           ...
   ```

4. Keep the rest of the methods (e.g., `get_available_servers`, `get_server_tools`, `call_tool`) largely unchanged, but ensure they reference `config` fields rather than the old dictionary structure.

## 6. Update the client classes in `clients/`

For both `filesystem_client.py` (original `working_mcp_client.py`) and `brave_search_client.py` (original `working_brave_search_client.py`):

1. Change the import at the top:

   ```python
   from core.config import get_enabled_servers
   ```

2. Optionally rename the class from `WorkingMCPClient` to `FilesystemClient` and from `WorkingBraveSearchClient` to `BraveSearchClient`.  If you rename the classes, update the plugin YAML to reference them (see step 8).

3. Leave the rest of the functionality as is so they continue to use Docker exec to run commands or JSON‑RPC calls.

## 7. Adjust the bot in `core/mcp_openai_bot.py`

1. Change imports at the top:

   ```python
   import openai
   from .config import OPENAI_API_KEY
   from .multi_client import MultiMCPClient
   ```

2. Rename the file to `mcp_openai_bot.py` and update any references to it (see step 9 for UI).

3. Otherwise, keep the `MCPOpenAIBot` class logic the same.  It should still create an OpenAI client and call `MultiMCPClient` to execute MCP tools.

## 8. Rewrite the plugin YAML files

Each plugin’s `config.yaml` needs to contain at least:

```yaml
name: "Filesystem Server"
description: "File and directory operations"
container_name: "agent-framework-mcp-filesystem-1"
server_path: "/projects"
icon: "📁"
enabled: true
client_class: "mcp_integration.clients.filesystem_client.FilesystemClient"
tools:
  list_directory:
    description: "List contents of a directory"
    parameters:
      path: "Directory path to list"
  read_file:
    ...
```

The Brave Search plugin YAML should similarly mirror the original `servers/brave_search/server.yaml`, with an added `client_class` pointing to `mcp_integration.clients.brave_search_client.BraveSearchClient`.

## 9. Move and update the UI code

1. Move the original `mcp_tab.py` into `ui/mcp_tab.py`.

2. At the top of this file, update imports:

   ```python
   from core.multi_client import MultiMCPClient
   ...
   from core.mcp_openai_bot import MCPOpenAIBot  # inside process_mcp_message
   ```

   – replace `from multi_mcp_client import MultiMCPClient` with the new import path.
   – replace `from mcp_openai_bot_v2 import MCPOpenAIBot` with `from core.mcp_openai_bot import MCPOpenAIBot`.

3. If the UI uses any constants from the old config, import them from `core.config`.

4. Leave the rest of the Streamlit logic unchanged, so it still persists the MCP client, displays server selectors, and calls `process_mcp_message`.

## 10. Create a top‑level wrapper for `mcp_tab`

Since `streamlit_app.py` still expects to import `render_mcp_tab` from `mcp_tab`, create a thin wrapper at `mcp_integration/mcp_tab.py`:

```python
from ui.mcp_tab import render_mcp_tab, draw_mcp_messages, process_mcp_message

__all__ = ["render_mcp_tab", "draw_mcp_messages", "process_mcp_message"]
```

This file should do nothing else; it simply re‑exports the UI functions so that `streamlit_app.py` continues to work without modification.

## 11. Update any remaining imports

* Anywhere in the codebase that used `from working_mcp_client import WorkingMCPClient` should now import from `clients.filesystem_client`.
* Anywhere that used `from working_brave_search_client import WorkingBraveSearchClient` should now import from `clients.brave_search_client`.
* Anywhere that used `from multi_mcp_client import MultiMCPClient` should now import from `core.multi_client`.
* Anywhere that used `from config import OPENAI_API_KEY, get_enabled_servers` should now import from `core.config`.
* If you renamed `WorkingMCPClient` to `FilesystemClient` and `WorkingBraveSearchClient` to `BraveSearchClient`, update references accordingly in the plugin YAML and in any `import` statements.

A systematic way to catch these is to run a search in your IDE for the old module names and update them to the new paths.

## 12. Remove the old `servers/` directory

Once the YAML files are migrated into `plugins/`, you can remove `mcp_integration/servers/` from the project.  All server configuration will now live under `plugins/<server>/config.yaml`, and the plugin manager handles loading it.

## 13. Test the integration end‑to‑end

1. Start your agent services (Docker containers) so that both filesystem and Brave Search servers are running.
2. Run `python src/streamlit_app.py` and ensure:

   * The MCP tab still appears (Streamlit should import `render_mcp_tab` from `mcp_tab` successfully).
   * The server selector shows both servers loaded from the plugin YAMLs.
   * Filesystem tools (list directory, read file, etc.) work as they did before.
   * Brave Search tools (web search, image search, etc.) work as they did before.
3. Check console output to verify that the `MultiMCPClient` is initialising servers based on the plugin manager and not hard‑coded values.

## 14. Document the new structure

Update your README or internal documentation to describe:

* The purpose of each new folder (`core`, `clients`, `plugins`, `ui`, `utils`).
* How to add a new MCP plugin: create a new folder under `plugins/`, add a `config.yaml` with server details and a `client_class` entry, and place the client code in `clients/`.
* How existing files map to the new structure.

---

Following these steps will give you a modular, plugin‑based MCP integration while preserving the existing link between `mcp_tab.py` and `streamlit_app.py`.  Every import path has been enumerated and relocated so that no functionality is lost, and new servers can be added simply by adding a new folder under `plugins/` without touching the core code.

ere's a comprehensive table of the MCP integration breakdown:

| **Component** | **Description** | **Purpose & Functionality** |
| --- | --- | --- |
| **Configuration Module**`config.py` | Centralizes environment variables and server definitions | Uses`os`and`Path`to load environment variables and build a dictionary of MCP server definitions |
| **Multi-Server Client**`multi_mcp_client.py` | Acts as thin orchestrator for working clients | Imports`get_enabled_servers`from config and conditionally instantiates appropriate working clients. Exposes methods to initialize servers, list available servers and tools, and call tools on a specified server |
| **Working Clients**`working_mcp_client.pyworking_brave_search_client.py` | Encapsulate container communication details | Both rely on`asyncio`and Docker exec commands. Filesystem client wraps directory/file operations; Brave Search client wraps JSON-RPC calls to Node.js server |
| **OpenAI Bot**`mcp_openai_bot_v2.py` | Wraps MCP tools into OpenAI function schemas | Handles conversation context and function invocation, exposes async`chat`method. Uses`MultiMCPClient`to retrieve tool schemas and execute tools |
| **Streamlit Tab**`mcp_tab.py` | Sets up web UI interface | Persists`MultiMCPClient`instance in session state, renders server selector and quick actions, calls OpenAI bot via`process_mcp_message` |
| **Servers Folder**`servers/` | Contains YAML configuration | Holds YAML configuration for each MCP server |

**Structural Analysis:**

- **Strengths:**
    - Logically separated by responsibility
    - Cohesive directory structure with clear purpose for each file
    - Dependencies flow in a single direction (configuration → working clients → multi-client → bot → UI)
    - Follows good practices for asynchronous programming and Docker communication
- **Limitations:**
    - Flat directory structure may become unwieldy as more MCP servers are added
    - Hard-codes relationship between server IDs and working clients
    - Adding new servers requires editing core code rather than just adding plugins
- **Suggested Improvements:**
    - Implement plugin-based structure with subdirectories for UI, core, server clients, and utilities
    - Reorganize into modular plugin architecture for better maintainability and scalability