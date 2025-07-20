---
applyTo: '*Review of mcp_integration directory (branch fix‑mcp)
Overview and directory structure

The mcp_integration folder implements a multi‑server Model Context Protocol (MCP) integration for the Agent‑Framework project. The goal is to expose external services (filesystems, Brave Search, GitHub, and additional future services) as MCP tools so that AI agents in the framework can call them via the MCP protocol. The folder contains both code and documentation:

    Configuration & orchestration – config.py defines environment variables and a registry of available servers and tools
    raw.githubusercontent.com
    . multi_mcp_client.py instantiates per‑server clients and provides a unified API to discover tools and dispatch calls
    raw.githubusercontent.com
    .

    User interfaces – mcp_tab.py implements a Streamlit tab that lets users pick a server, choose a tool or type a message, and it uses the multi‑server client to execute tool calls
    raw.githubusercontent.com
    .

    AI bot integration – mcp_openai_bot_v2.py wraps the multi‑server client into a persistent OpenAI bot. It creates system messages describing the selected server (filesystem, Brave Search or GitHub) and uses OpenAI’s function calling to map tool definitions to functions
    raw.githubusercontent.com
    . The bot persists connections by caching bot instances in Streamlit session state
    raw.githubusercontent.com
    .

    Working client implementations – The working clients (e.g. working_mcp_client.py, working_brave_search_client.py, working_github_client.py) communicate with their Docker containers using docker exec. They avoid the earlier JSON‑RPC approach by executing commands inside the container and parsing responses
    raw.githubusercontent.com
    .

    Legacy/test code – mcp_jsonrpc_client.py implements a JSON‑RPC client; it is largely superseded by the working clients. Test scripts (test_github_functionality.py, test_working_clients.py) provide reference examples.

    Documentation – The README.MD, MCP_ARCHITECTURE.md and CLEANUP_GUIDE.md files explain the architecture and summarise which files are working and which should be removed. The architecture guide gives a detailed workflow and instructions for adding new servers
    raw.githubusercontent.com
    . The cleanup guide explicitly lists which files to keep and which to delete
    raw.githubusercontent.com
    .

    Server configuration – The servers subdirectory contains YAML files describing each MCP server. For example, servers/brave_search/server.yaml defines the Brave Search container and its tools
    raw.githubusercontent.com
    , and servers/github/server.yaml enumerates the GitHub tools (create/update files, search repositories, create PRs etc.)
    raw.githubusercontent.com
    .

The root compose.yaml in the repository defines Docker services for the project. It includes mcp‑filesystem, mcp‑brave‑search and mcp‑github containers, mounts the mcp_integration folder into the Streamlit app and mounts the Docker socket so that the integration can talk to the containers
raw.githubusercontent.com
raw.githubusercontent.com
.
Highlights and strengths
Aspect	Strength
Modular multi‑server design	The design cleanly separates configuration, client logic, UI integration and server definitions. The MultiMCPClient orchestrates any number of servers and exposes a uniform interface to discover servers and call tools
raw.githubusercontent.com
. Each service has its own working client class (filesystem, Brave Search, GitHub) following the same pattern of container name, available tools and a call_tool() method
raw.githubusercontent.com
raw.githubusercontent.com
.
Persistent connections	By injecting a pre‑initialized MultiMCPClient into mcp_openai_bot_v2.py and caching bots in Streamlit session state, the integration avoids frequent connection creation and teardown. The bot’s initialize() method uses an existing client if provided
raw.githubusercontent.com
and the Streamlit tab stores both the client and individual bot instances under keys in session_state
raw.githubusercontent.com
. This solves the previous issue of connection drops noted in the documentation.
Comprehensive documentation	MCP_ARCHITECTURE.md provides a detailed overview of all files, workflows, and a step‑by‑step guide to adding new servers
raw.githubusercontent.com
. CLEANUP_GUIDE.md lists which legacy files to remove and why
raw.githubusercontent.com
. Such documentation makes the codebase easy to understand and maintain.
Testing and reference scripts	The test files demonstrate how to use the multi‑MCP client and verify the behaviour of each working client. They serve as simple examples for developers to experiment with and ensure that the integration is functional
raw.githubusercontent.com
raw.githubusercontent.com
.
Docker‑based communication	The switch from JSON‑RPC over stdio to invoking container commands with docker exec results in more reliable interactions. The working clients run commands like ls, cat or call the server’s dist/index.js file and parse the output
raw.githubusercontent.com
raw.githubusercontent.com
. This avoids asyncio issues and simplifies error handling.
Extensibility via configuration	The MCP_SERVERS dictionary in config.py stores metadata for each server, including container names, descriptions, available tools and whether it is enabled
raw.githubusercontent.com
. This approach allows new services to be added or disabled without altering the core logic. get_enabled_servers() returns only active servers
raw.githubusercontent.com
.
Weaknesses and areas for improvement
Issue	Explanation & Impact
Duplication across working clients	Each working client class repeats boilerplate code for initializing containers, executing commands, and checking tool names. Shared utility methods or a base class could reduce duplication and centralize error handling (e.g. _run_docker_command(), initialize(), call_tool())
raw.githubusercontent.com
raw.githubusercontent.com
.
Mocked implementations for non‑filesystem services	The Brave Search and GitHub clients currently return simulated responses rather than calling real MCP servers; call_tool() simply echoes the parameters with a note that this is a simulated response
raw.githubusercontent.com
raw.githubusercontent.com
. This makes testing easier but means the integration is not truly production‑ready until proper JSON‑RPC communication is implemented.
Incomplete server discovery	Although the configuration system is dynamic, the MultiMCPClient dispatches clients based on hard‑coded server IDs and must be manually extended when adding a new server (e.g., elif server_id == "github"). A registry mapping server IDs to client classes could eliminate the need to modify the orchestrator for each new service
raw.githubusercontent.com
.
Upper‑case README duplication	The directory still contains a README.MD with an outdated summary. CLEANUP_GUIDE.md recommends removing this file to avoid confusion
raw.githubusercontent.com
.
Legacy JSON‑RPC client	mcp_jsonrpc_client.py remains in the folder but is superseded by the working client pattern. Keeping it might mislead developers; the cleanup guide suggests deleting it
raw.githubusercontent.com
.
Error handling and logging	Many methods catch broad Exception and return generic error messages. More granular exception handling, logging, and retries could make the system more robust, especially when communicating with real external services.
Security concerns	Secrets (API keys, access tokens) are loaded via environment variables but may inadvertently print warnings about missing keys. The configuration prints whether the OpenAI, Brave or GitHub keys are missing
raw.githubusercontent.com
. Logging these values should be avoided in production.
Pattern for adding more MCP servers

The architecture guides describe a clear plug‑and‑play pattern for integrating new MCP servers. The steps can be summarised as follows:

    Create a working client class – Implement a new WorkingNewServerClient following the same pattern as the existing working clients. It should accept a container_name and optionally a base path, define a dictionary of available tools, provide an initialize() method to test container connectivity, and implement a call_tool() method that communicates via docker exec and parses JSON‑RPC results
    raw.githubusercontent.com
    .

    Add server definition to config.py – Insert a new entry into the MCP_SERVERS dict with the server’s name, description, container name, base path, tool definitions and enable flag
    raw.githubusercontent.com
    .

    Register the client in multi_mcp_client.py – Extend the orchestrator to recognise the new server ID and instantiate the corresponding working client class. Alternatively, refactor the orchestrator to look up client classes from a registry to avoid manual updates
    raw.githubusercontent.com
    .

    Add Docker service – Edit compose.yaml to include a new mcp‑newserver service with the container name, image, environment variables and open stdin/TTY so that JSON‑RPC communication over docker exec works
    raw.githubusercontent.com
    . Provide a servers/newserver/server.yaml file with tool metadata and environment placeholders
    raw.githubusercontent.com
    .

    Update the UI if necessary – The Streamlit tab automatically lists tools based on the MultiMCPClient.get_available_servers() call. However, if the new service introduces unique UI interactions, update mcp_tab.py accordingly.

Following this pattern makes it straightforward to add memory, search, database or email servers as suggested in the README
raw.githubusercontent.com
.
Final evaluation (grading)
Criteria	Evaluation
Code organisation & readability	The separation of configuration, orchestration, UI and per‑service clients is clear, and the documentation includes helpful comments. However, duplicated code across the working clients and manual server registration slightly reduce maintainability.
Functionality	The filesystem client is functional and demonstrates real interactions. The Brave Search and GitHub clients currently simulate responses, so full functionality depends on future work.
Extensibility	The architecture is designed to support unlimited servers. Adding new servers is documented and requires minimal changes in the core code
raw.githubusercontent.com
.
Testing	Test scripts provide examples for each service, but only cover basic scenarios and simulated responses. More comprehensive tests could validate error cases, concurrency, and real API calls.
Documentation	Excellent. MCP_ARCHITECTURE.md and CLEANUP_GUIDE.md clearly describe the architecture, success metrics, next steps, and cleanup instructions
raw.githubusercontent.com
. Removing outdated documents like README.MD will reduce confusion.

Overall grade: B+. The fix‑mcp branch demonstrates a well‑thought‑out multi‑server architecture with persistent connections and good documentation. The main limitations are the simulated clients for Brave Search and GitHub, code duplication in working clients, and manual server registration. Addressing these issues will elevate the codebase to a solid production grade.
Recommendations for next steps

    Refactor working clients – Extract common functionality into a base class or shared utility module (e.g., container execution, initialization, safe path handling). This will simplify adding new clients and reduce code duplication.

    Implement real JSON‑RPC for Brave Search & GitHub – Replace the simulation with actual calls to the MCP server’s dist/index.js using the JSON‑RPC protocol (similar to mcp_jsonrpc_client.py), or use the underlying API directly. Ensure proper error handling and timeouts.

    Dynamic client registry – Instead of hard‑coding server IDs in MultiMCPClient, maintain a registry mapping server IDs to client classes. This will allow adding new services without changing the orchestrator code.

    Clean up legacy files – Remove mcp_jsonrpc_client.py, test_working_clients.py and the uppercase README.MD as recommended in the cleanup guide
    raw.githubusercontent.com
    . Ensure compiled Python caches (__pycache__) are excluded from version control.

    Strengthen tests – Write tests that interact with actual MCP servers running in Docker, including tests for failure conditions, invalid parameters and concurrency. Integrate these tests with CI.

    Security & configuration – Use a secrets manager or .env files outside of version control to store API keys. Avoid printing the presence or absence of secrets in logs
    raw.githubusercontent.com
    .

    Expand server types – According to the README’s roadmap, implement memory, search, database and email servers. The existing pattern and documentation should make these additions straightforward
    raw.githubusercontent.com
    .

By following these improvements, the mcp_integration directory can evolve into a robust, extensible and maintainable component of the Agent‑Framework project.*}