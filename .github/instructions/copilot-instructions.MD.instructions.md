---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.
Below is a high‑level plan you can put into your **`copilot-instructions.md`** to guide GitHub Copilot as you extend the existing filesystem integration to include a Brave Search MCP server. The goal is to keep the integration self‑contained under `mcp_integration` so it doesn’t interfere with `/src`. Each step describes what to do, not the exact code, to allow Copilot some flexibility.

---

## 📦 1. Create a new Brave Search server folder

1. Inside `mcp_integration`, make a subdirectory such as `servers/brave_search/`.
2. Add a `server.yaml` (or JSON) file describing the server: name (`brave-search`), description, container image (`mcp/brave-search:latest`), the port it will run on, and environment variables.  Also list the tools you plan to support (`web_search`, `image_search`, etc.), with simple parameter definitions (e.g., `query`, `count`, `safesearch`).
3. Optionally include a `Dockerfile` or `docker-compose.yml` in this folder if you want to build/run the server locally.  If you use the official Docker image directly, a compose file is enough.  Make sure the compose service sets `BRAVE_API_KEY` from the `.env` file.

## 🛠️ 2. Add a Docker service to start the server

1. In your project’s `docker-compose.yml` (or a new compose file under `servers/brave_search/`), define a service such as `mcp-brave-search`.
2. Set `container_name` to something like `agent-framework-mcp-brave-search-1`.
3. Use `image: mcp/brave-search:latest` or build from your local `Dockerfile`.
4. Pass `BRAVE_API_KEY` as an environment variable from the `.env` file.
5. Map container port 8080 to a host port (e.g., `8111:8080`).
6. Bring up the service with `docker compose up -d mcp-brave-search` and verify it’s running by hitting its `/health` endpoint.

## 🧩 3. Register the server in `config.py`

1. Open `mcp_integration/config.py` and extend the `MCP_SERVERS` dictionary.

2. Add an entry with the key `brave_search` containing:

   * `name`: “Brave Search”.
   * `description`: a short explanation of what it does.
   * `container_name`: use an environment variable `MCP_BRAVE_CONTAINER_NAME` with a default of `agent-framework-mcp-brave-search-1`.
   * `server_path`: a dummy path such as `/` (not used for search).
   * `icon`: an appropriate emoji if desired.
   * `enabled`: `True`.
   * `tools`: a dictionary defining each search tool and its parameters (`query`, `count`, etc.).

3. Make sure your `.env` file contains `BRAVE_API_KEY` (already added) and optionally `MCP_BRAVE_CONTAINER_NAME`.

## ⚙️ 4. Extend the multi‑MCP client to support search

1. In `multi_mcp_client.py`, add a method like `_call_brave_search_tool` to handle Brave search tools.  This method should:

   * Build a command or HTTP request to call the search server.
   * Use `self._run_docker_command` with `curl` (or another client) to hit `http://localhost:8080/mcp` and pass JSON specifying the tool name and parameters.
   * Parse the JSON response and return it in the same structure as the filesystem tools.
2. In `call_tool`, route calls to Brave search tools based on `self.server_id == "brave_search"`, invoking the new helper method.
3. Implement support for the tools defined in `config.py` (`web_search`, `image_search`, etc.), at least at a basic level.

## 🖥️ 5. Update the Streamlit UI (if needed)

1. Because the UI uses `mcp_client.get_available_servers()` to build the server list, registering `brave_search` in `config.py` should automatically add it to the server selection dropdown.
2. To improve UX, enhance the quick‑action selector to recognise search tools (e.g., add “Search the web” when `web_search` is available).
3. Test the MCP tab: select Brave Search, choose an action like “Search the web” and verify that results appear.

## ✅ 6. Test incrementally

1. **Container check:** After starting the Brave Search container, ensure `curl http://localhost:8111/health` returns a healthy status.
2. **Tool check:** Run a small Python script with `MultiMCPClient` to call `web_search` with a sample query.  Confirm that JSON results are returned.
3. **UI check:** Use the Streamlit app to perform searches via the MCP tab and verify the output.
4. **OpenAI bot check:** Ask the bot questions that require web search and confirm it calls the appropriate tool.

---

These steps should guide Copilot to scaffold the new Brave Search server alongside the existing filesystem server, while keeping all changes inside `mcp_integration` and leaving your working `src` untouched.


MCP Integration Directory Analysis and Brave Search Integration Plan
1 Current structure of mcp_integration

The mcp_integration directory in the adding‑mcp branch holds a working multi‑server MCP integration that is deliberately isolated from the main src folder. Its purpose is to provide a plug‑and‑play way to add and test MCP servers without interfering with the existing Agent‑Framework code. The key files and their roles are summarised below.
File	Purpose
README.MD	Provides an overview of the MCP integration. It states that the integration is production‑ready and lists the core components (multi‑server client, config system, Streamlit UI) and currently implemented tools. The README explains that the architecture supports multiple servers and shows how to use the MCP client or the OpenAI bot
raw.githubusercontent.com
. It outlines environment variables loaded from the parent .env file and emphasises that the integration is designed to be extended with additional servers via a plug‑and‑play architecture
raw.githubusercontent.com
.
config.py	Loads the .env file from the parent directory and defines the configuration for available MCP servers. Currently there is a single filesystem server with details such as container name (agent‑framework‑mcp‑filesystem‑1) and base path (/projects)
raw.githubusercontent.com
. The module declares the available tools (list, read, write, create directory, move file, get file info, search files, directory tree) together with their parameters
raw.githubusercontent.com
. Functions get_enabled_servers() and get_server_config() return the list of enabled servers and configuration for a given server
raw.githubusercontent.com
.
multi_mcp_client.py	Implements the multi‑server MCP client. It defines an MCPServerClient class that manages a single server by executing commands in a Docker container via docker exec
raw.githubusercontent.com
. The client implements filesystem tools by calling appropriate shell commands inside the container, returning results as text
raw.githubusercontent.com
. The MultiMCPClient class wraps multiple MCPServerClient instances and offers methods to initialise all enabled servers, retrieve available servers and their tools, and call a specific tool on a selected server
raw.githubusercontent.com
. This design allows adding new server types without touching the existing working code, provided each server implements its own tool functions.
mcp_tab.py	Provides a Streamlit UI tab that integrates the multi‑server client. On initialisation it creates a MultiMCPClient, initialises all enabled servers and stores the client in the Streamlit session state
raw.githubusercontent.com
. The sidebar lets the user choose which MCP server to use and displays its available tools
raw.githubusercontent.com
. Main interactions are processed through the OpenAI bot; user messages are passed along with context to MCPOpenAIBot, which uses MCP tools to fulfil requests
raw.githubusercontent.com
.
mcp_openai_bot_v2.py	Contains MCPOpenAIBot, an OpenAI‑powered assistant that communicates with MCP servers. It initialises a MultiMCPClient and uses OpenAI function calling to expose MCP tools to the LLM
raw.githubusercontent.com
. When the LLM issues a tool call, the bot executes the appropriate MCP tool via the multi‑server client and returns the result to the model
raw.githubusercontent.com
.
working_mcp_client.py	A single‑server reference implementation used during the initial integration. It operates similarly to MCPServerClient but only for the filesystem server and includes tests showing how to use each tool
raw.githubusercontent.com
.
PLUGIN_ARCHITECTURE_RESEARCH.md	Research notes outlining a proposed plug‑and‑play server architecture. It suggests adding a servers/ directory under mcp_integration with subdirectories for each server (e.g., filesystem, memory, search) containing server.yaml and docker‑compose.yml files
raw.githubusercontent.com
. The document describes a YAML configuration format (server name, container image, base path, tools, dependencies, health checks)
raw.githubusercontent.com
and lists phased tasks for building a server manager, integrating memory and search servers, and creating templates
raw.githubusercontent.com
.
SOLUTION_SUMMARY.MD	Summarises the solution achieved so far: switching to docker exec to avoid asyncio issues, integrating MCP tools into the Streamlit UI, and confirming that the filesystem server and eight tools work reliably
raw.githubusercontent.com
. It also repeats the vision for a modular server architecture with directories under mcp_integration/servers and outlines future work (auto‑discovery, memory server, search server)
raw.githubusercontent.com
.
Design principles observed

    Isolation from src – All MCP functionality lives inside mcp_integration so that the existing agent framework remains unaffected. The Streamlit UI imports from src only for shared schemas, but there are no changes to the core agents.

    Docker‑exec transport – Both the single‑server and multi‑server clients avoid the unstable STDIO transport by executing commands directly inside the container with docker exec. This approach works reliably for filesystem operations
    raw.githubusercontent.com
    .

    Configuration‑driven servers – The config.py module shows how servers are defined: each server has a name, description, container name, base path and a dictionary of tools with descriptions and parameters
    raw.githubusercontent.com
    . New servers can be added by extending this dictionary or, as proposed, by storing server definitions in YAML files in a servers/ directory
    raw.githubusercontent.com
    .

    Extensible client – MultiMCPClient holds a mapping of server ID to MCPServerClient. Additional servers can be added as long as they implement tool execution (e.g., _call_search_tool). The architecture is ready to support unlimited servers
    raw.githubusercontent.com
    .

2 Why a Brave Search MCP server?

The Brave search MCP server is an official server that exposes web search, local search, image search, video search, news search and summarisation tools. The npm package @brave/brave-search-mcp-server can be run directly via Docker: docker run -i --rm -e BRAVE_API_KEY mcp/brave-search
npmjs.com
. It accepts a BRAVE_API_KEY environment variable, which the user has already added to .env. This makes it a good candidate for plug‑and‑play integration.
3 High‑level plan to integrate Brave Search

Our goal is to add Brave Search as a separate MCP server in mcp_integration without touching the existing src code. Following the research notes and existing patterns, we can achieve this by:

    Creating a dedicated server directory (e.g., mcp_integration/servers/search or mcp_integration/servers/brave_search) to hold the server’s Dockerfile or docker‑compose file and metadata.

    Adding a configuration file (server.yaml or server.json) describing the server (name, description, container image, tools and parameters, environment variables). This will allow auto‑discovery in future and keep server definitions separate from code.

    Creating a Dockerfile or using a public image for the Brave search server. Since the npm package already provides a Docker image (mcp/brave-search), we can either reference that image in a docker compose service or build our own image if customisation is needed.

    Updating the Python configuration (config.py) to register the search server, specifying its container name, base path (if applicable) and tools. Tools should reflect the Brave search API endpoints (e.g., web_search, local_search, image_search).

    Extending multi_mcp_client.py to handle search tools. This may involve adding a _call_search_tool method that invokes the MCP server via docker exec or HTTP. For example, the method could pass JSON input to the search server’s STDIO or call its HTTP API.

    Updating the Streamlit UI (mcp_tab.py) to display the new server and allow users to select search actions. Because the UI reads available servers and tools from the client, this may happen automatically once the new server is registered.

    Testing each step to ensure the new server starts, is reachable and its tools return expected search results.

4 Step‑by‑step instructions for adding Brave Search MCP server
Step 1 – Create a server directory

    In mcp_integration, create a new subdirectory for the Brave search server:

mkdir -p mcp_integration/servers/brave_search

Inside this directory, create a server.yaml file describing the server. Use the format outlined in PLUGIN_ARCHITECTURE_RESEARCH.md
raw.githubusercontent.com
. For example:

    name: "brave-search"
    version: "1.0.0"
    description: "Web, image, video and news search via Brave API"
    icon: "🧭"
    enabled: true
    priority: 2  # after filesystem

    container:
      name: "agent-framework-mcp-brave-search-1"
      image: "mcp/brave-search:latest"  # use official image
      ports:
        - "8111:8080"  # map container port 8080 to host port 8111 (adjust as needed)
      environment:
        - "BRAVE_API_KEY=${BRAVE_API_KEY}"

    tools:
      - name: "web_search"
        description: "Perform a web search"
        parameters:
          query: "Search query (required)"
          count: "Number of results (optional)"
          safesearch: "off | moderate | strict (optional)"
      - name: "image_search"
        description: "Search for images"
        parameters:
          query: "Search query (required)"
          count: "Number of results (optional)"
          safesearch: "off | strict (optional)"
      # Add other tools (local_search, video_search, news_search, summarizer) as needed

    dependencies: []
    health_check:
      endpoint: "/health"  # if the server exposes a health endpoint
      interval: 30
      timeout: 10
      retries: 3

    The environment variable ${BRAVE_API_KEY} will be expanded from .env because Docker Compose can pass environment variables defined in the parent .env file.

Step 2 – Add a Docker compose service

    In the root (or in mcp_integration if you prefer to isolate services) extend your docker‑compose.yml to include the Brave search service. For example:

services:
  mcp-brave-search:
    container_name: agent-framework-mcp-brave-search-1
    image: mcp/brave-search:latest
    environment:
      - BRAVE_API_KEY=${BRAVE_API_KEY}
    ports:
      - "8111:8080"
    restart: unless-stopped

Alternatively, you can create a dedicated docker-compose.brave.yml inside mcp_integration/servers/brave_search for local development of this server. This keeps each server’s compose file separate.

Bring up the Brave search container:

    docker compose up -d mcp-brave-search

    Verify that the container is running and accessible (e.g., docker ps should show the container; curl http://localhost:8111/health may return a status).

Step 3 – Register the search server in config.py

    Open mcp_integration/config.py and extend the MCP_SERVERS dictionary to include the Brave search server. For example:

    MCP_SERVERS = {
        "filesystem": { ... },
        "brave_search": {
            "name": "Brave Search",
            "description": "Web, image and news search via Brave API",
            "container_name": os.getenv("MCP_BRAVE_CONTAINER_NAME", "agent-framework-mcp-brave-search-1"),
            "server_path": "/",  # not used for search, but required
            "icon": "🧭",
            "enabled": True,
            "tools": {
                "web_search": {
                    "description": "Perform a web search",
                    "parameters": {"query": "Search query", "count": "Results count (optional)", "safesearch": "off/moderate/strict"}
                },
                "image_search": {
                    "description": "Search for images",
                    "parameters": {"query": "Search query", "count": "Results count (optional)", "safesearch": "off/strict"}
                },
                # add additional tools here
            }
        }
    }

    Add a new environment variable MCP_BRAVE_CONTAINER_NAME in .env (optional) if you want to override the container name. Ensure your .env already contains BRAVE_API_KEY.

Step 4 – Extend the multi‑server client

    In mcp_integration/multi_mcp_client.py, add a method _call_brave_search_tool inside MCPServerClient. This method should handle each search tool by invoking the Brave search MCP server. One simple approach is to call the server’s HTTP API via curl inside the container using docker exec. For example:

async def _call_brave_search_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    # Build the command based on tool
    if tool_name == "web_search":
        query = arguments.get("query", "")
        count = arguments.get("count", 10)
        safesearch = arguments.get("safesearch", "moderate")
        cmd = [
            "sh", "-c",
            f"curl -s -X POST http://localhost:8080/mcp -H 'Content-Type: application/json' \
            -d '{json.dumps({"tool": "brave_web_search", "query": query, "count": count, "safesearch": safesearch})}'"
        ]
        result = await self._run_docker_command(cmd)
        # Parse JSON output and return
        if result["success"]:
            return {"content": [{"type": "text", "text": result["output"]}]}
        else:
            return {"error": result["error"]}
    # handle other tools…

Adjust the HTTP endpoint and payload according to the Brave search MCP server’s API; the above is a placeholder. Alternatively, if the server supports STDIO, you can run docker exec -i and pipe JSON into the server’s process.

Modify call_tool to route search tools to this method:

    if self.server_id == "filesystem":
        return await self._call_filesystem_tool(tool_name, arguments)
    elif self.server_id == "brave_search":
        return await self._call_brave_search_tool(tool_name, arguments)
    else:
        return {"error": f"Tool execution not yet implemented for {self.config['name']}"}

    After making these changes, restart your Streamlit app and test calling web_search from the MCP tab. Verify that results are returned and displayed to the user.

Step 5 – Update the UI (if necessary)

The Streamlit UI reads available servers and their tools from the multi‑server client at runtime. Once the Brave search server is registered in config.py, it should appear automatically in the server selection box
raw.githubusercontent.com
. However, to improve the user experience you may want to add descriptive quick actions for search (e.g., “Search the web for…”). Modify the quick‑action builder in mcp_tab.py to detect search tools and include intuitive actions:

if "web_search" in server_tools:
    quick_actions.append("Search the web")
if "image_search" in server_tools:
    quick_actions.append("Search for images")
# etc.

Step 6 – Test and iterate

    Container test: Ensure that docker compose up -d mcp-brave-search starts the container and that curl http://localhost:8111/ returns a response. Check logs for any authentication errors – if there are issues, confirm that BRAVE_API_KEY in .env is correct.

    Client test: Run python mcp_integration/multi_mcp_client.py or use the Streamlit app to test calling each search tool. Handle errors gracefully and adjust the _call_brave_search_tool logic as needed.

    LLM test: With mcp_openai_bot_v2.py, ask questions like “Search the web for the latest MCP servers” and ensure that the bot calls the correct search tool and summarises results.

5 Implementation summary

    The mcp_integration directory currently contains a working, isolated MCP integration built around a multi‑server client, Streamlit UI and OpenAI bot. It uses Docker to interact with a filesystem MCP server, avoids the core src code, and is ready to be extended
    raw.githubusercontent.com
    .

    To integrate Brave search, create a new server directory with its own configuration and Docker service, register it in config.py, implement tool routing in multi_mcp_client.py, and update the UI to expose its tools. This approach maintains the isolation from src and follows the plug‑and‑play architecture proposed in the research notes
    raw.githubusercontent.com
    .

    Implement the integration incrementally: start by standing up the container, then expose tools through Python, then connect to the UI and OpenAI. Each step can be tested separately to ensure stability.