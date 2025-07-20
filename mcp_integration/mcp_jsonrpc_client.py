"""
MCP JSON-RPC Client Helper
Handles proper communication with MCP servers using JSON-RPC over stdio protocol.
"""
import asyncio
import json
import uuid
from typing import Any


class MCPJSONRPCClient:
    """Helper class for communicating with MCP servers via JSON-RPC over stdio"""
    
    def __init__(self, container_name: str, server_path: str = "/app"):
        self.container_name = container_name
        self.server_path = server_path
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool using proper JSON-RPC protocol"""
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Build JSON-RPC request for tool call
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Convert to JSON string
            request_json = json.dumps(request)
            
            # Execute the MCP server with our request
            command = [
                "docker", "exec", "-i", self.container_name,
                "node", f"{self.server_path}/dist/index.js"
            ]
            
            # Run the command with stdin input
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send the JSON-RPC request
            stdout, stderr = await process.communicate(input=request_json.encode())
            
            if process.returncode == 0:
                # Parse JSON-RPC response
                try:
                    response_lines = stdout.decode().strip().split('\n')
                    # Look for the actual response (may have multiple JSON lines)
                    for line in response_lines:
                        if line.strip():
                            try:
                                response = json.loads(line)
                                if "result" in response:
                                    return response["result"]
                                elif "error" in response:
                                    return {"error": f"MCP Error: {response['error']}"}
                            except json.JSONDecodeError:
                                continue
                    
                    # If no valid JSON response found, return raw output
                    return {
                        "content": [{
                            "type": "text",
                            "text": stdout.decode()
                        }]
                    }
                    
                except Exception as e:
                    return {"error": f"Failed to parse MCP response: {e}"}
            else:
                error_msg = stderr.decode()
                return {"error": f"MCP server error: {error_msg}"}
                
        except Exception as e:
            return {"error": f"Failed to communicate with MCP server: {e}"}


async def test_mcp_jsonrpc():
    """Test the MCP JSON-RPC client"""
    print("🧪 Testing MCP JSON-RPC Client")
    print("=" * 50)
    
    # Test Brave Search
    brave_client = MCPJSONRPCClient("agent-framework-mcp-brave-search-1")
    print("\n🔍 Testing Brave Search JSON-RPC...")
    result = await brave_client.call_tool("brave_web_search", {
        "query": "Python programming",
        "count": 2
    })
    print(f"Brave Result: {result}")
    
    # Test GitHub  
    github_client = MCPJSONRPCClient("agent-framework-mcp-github-1")
    print("\n🐙 Testing GitHub JSON-RPC...")
    result = await github_client.call_tool("search_repositories", {
        "query": "python machine learning",
        "sort": "stars",
        "order": "desc",
        "per_page": 2
    })
    print(f"GitHub Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_mcp_jsonrpc())
