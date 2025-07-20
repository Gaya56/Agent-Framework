---
applyTo: '*Here are some likely reasons why the **Brave Search** and **GitHub** tools are not working correctly in your UI, along with the steps to diagnose and fix them:

---

### 1. API keys missing or not passed into the server containers

* **Required environment variables** – In `config.py` the Brave and GitHub servers are only enabled when `BRAVE_API_KEY` and `GITHUB_PERSONAL_ACCESS_TOKEN` are set.  If these keys are missing, the module logs a warning and the servers are effectively disabled.  Make sure your `.env` file in the project root contains:

  ```env
  BRAVE_API_KEY=<your-brave-key>
  GITHUB_PERSONAL_ACCESS_TOKEN=<your-github-pat>
  ```

  Both keys must be valid and have the correct scopes (e.g., the GitHub PAT needs at least `repo` and `read:user` scopes for listing and updating files, and the Brave API key must match the plan that supports the endpoints you’re calling).

* **Propagation into containers** – The API keys also need to be available inside the Docker containers running the servers.  The official Brave and GitHub MCP servers expect their keys to be provided via environment variables (e.g., `BRAVE_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`) when the container starts.  Check the `server.yaml` or `docker-compose.yml` files under `servers/brave_search` and `servers/github` (or your equivalent deployment scripts) to ensure they pass these variables into the container.  Without them, `docker exec` commands in `multi_mcp_client.py` will fail even if your host environment has the keys set.

---

### 2. Container naming or runtime mismatches

* The client code uses hardcoded container names such as `agent-framework-mcp-brave-search-1` and `agent-framework-mcp-github-1`.  If your running containers use different names (for example, due to changes in your `docker-compose.yaml`), `docker exec` will fail and the server will never initialize.  Use `docker ps` to check the actual container names and update the `container_name` fields in `config.py` accordingly.

* Ensure the containers are running.  `MCPServerClient.initialize()` tests connectivity by running `ls -la` inside the container and marks the server as unavailable if it fails.  If you’ve never started the Brave or GitHub servers (or if they exited due to misconfiguration), they will be unavailable in the UI.

---

### 3. Incorrect endpoint or port in the client code

* For Brave Search, `multi_mcp_client.py` sends a POST request to `/call` on port 80 of the container.  If your Brave Search MCP server exposes a different endpoint (e.g., `/tools/call`) or runs on another port, the client will get a 404.  Check your Brave server’s documentation or `server.yaml` to verify the correct route and port.  If different, update the `_call_brave_search_tool()` method accordingly.

* The GitHub client uses STDIO to call `node dist/index.js` inside the container and reads a JSON response.  If the server expects HTTP rather than STDIO, or if the Node script path is different, this will fail.  Consult the GitHub MCP server’s README to confirm the invocation method; you might need to replace the STDIO call with an HTTP request similar to Brave Search.

---

### 4. Incomplete or incorrect tool parameters

* Some GitHub tools require non‑optional parameters, like `owner`, `repo`, and `path` for file operations or `branch_name` and `message` when creating/updating files.  If the UI sends empty values, the server may return an error.  Likewise, Brave Search tools accept optional parameters like `count` or `additional_params`; invalid parameter values can cause failures.  Double‑check the parameters being sent from the UI and ensure they align with the tool definitions in `config.py`.

---

### 5. Debugging steps

* Run the Brave and GitHub servers manually via `docker run` or `npx` and issue simple test calls to ensure they accept your API keys.  For Brave Search, you can test with:

  ```bash
  curl -X POST -H 'Content-Type: application/json' \
       -d '{"method":"tools/call","params":{"tool_name":"brave_web_search","tool_arguments":{"query":"test","count":1}}}' \
       http://localhost:PORT/call
  ```

  Replace `PORT` with the port your Brave server is listening on and confirm that it returns search results.  Do the same for GitHub, substituting the appropriate tool and arguments.

* From within your `agent-framework` project, run `docker exec -it <container-name> ls` to verify you can enter each container.  If you cannot, the container either isn’t running or the name is wrong.

* If everything looks correct but the UI still shows “not working,” look at the console output from `multi_mcp_client.py` or your server containers for error messages.  These logs often reveal missing keys or incorrect endpoints.

---

By checking the environment variables, container names, server endpoints, and tool parameters, you should be able to pinpoint why the Brave Search and GitHub tools are failing.  Most issues stem from a missing or misconfigured API key or mismatched container configuration.
*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.