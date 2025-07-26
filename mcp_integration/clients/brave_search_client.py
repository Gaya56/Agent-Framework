"""
Working Brave Search MCP Client using docker exec to communicate with Brave Search container.
This follows the same reliable pattern as working_mcp_client.py for filesystem operations.
"""
import asyncio
import json
from typing import Any


class BraveSearchClient:
    """
    Brave Search MCP client that uses docker exec to communicate with Brave Search container.
    This follows the same reliable pattern as the filesystem client.
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        # Accept configuration as parameter to avoid circular imports
        if config is None:
            # Fallback to default values if no config provided
            config = {
                "container_name": "agent-framework-mcp-brave-search-1",
                "server_path": "/app"
            }
        
        self.container_name = config.get("container_name", "agent-framework-mcp-brave-search-1")
        self.server_path = config.get("server_path", "/app")
        self.is_initialized = False
        self.available_tools = {
            "brave_web_search": {
                "description": "Search the web using Brave Search API",
                "parameters": {
                    "query": "Search query string",
                    "count": "Number of results (default: 5, max: 20)"
                }
            },
            "brave_image_search": {
                "description": "Search for images using Brave Search API", 
                "parameters": {
                    "searchTerm": "Image search term",
                    "count": "Number of images (default: 1, max: 3)"
                }
            },
            "brave_local_search": {
                "description": "Search for local businesses and places",
                "parameters": {
                    "query": "Local search query (e.g. 'pizza near Central Park')",
                    "count": "Number of results (default: 10, max: 20)"
                }
            },
            "brave_news_search": {
                "description": "Search for news articles",
                "parameters": {
                    "query": "News search query",
                    "count": "Number of results (default: 10, max: 20)",
                    "freshness": "Time filter (pd, pw, pm, py or date range)"
                }
            },
            "brave_video_search": {
                "description": "Search for videos",
                "parameters": {
                    "query": "Video search query", 
                    "count": "Number of results (default: 10, max: 20)",
                    "freshness": "Time filter (pd, pw, pm, py or date range)"
                }
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize connection to Brave Search MCP container"""
        try:
            print("🔄 Initializing Brave Search MCP Client...")
            print(f"   Container: {self.container_name}")
            print(f"   Base Path: {self.server_path}")
            
            # Test container accessibility
            result = await self._run_docker_command(["ls", "-la", self.server_path])
            
            if result["success"]:
                print("✅ Brave Search container connection successful")
                self.is_initialized = True
                return True
            else:
                print(f"❌ Brave Search container connection failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Brave Search MCP client initialization failed: {e}")
            return False
    
    async def _run_docker_command(self, command: list[str]) -> dict[str, Any]:
        """Execute command in docker container"""
        try:
            full_command = ["docker", "exec", self.container_name] + command
            
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace'),
                "error": stderr.decode('utf-8', errors='replace'),
                "returncode": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Command execution failed: {e}",
                "returncode": -1
            }
    
    async def _run_mcp_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute Brave Search MCP tool via docker exec and JSON-RPC communication"""
        try:
            # Create JSON-RPC request
            request_id = f"{tool_name}_{hash(str(params))}"
            json_rpc_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }
            
            # Convert to JSON string
            request_json = json.dumps(json_rpc_request)
            
            # Execute MCP server via docker exec
            # MCP servers expect JSON-RPC via stdin/stdout
            result = await self._run_docker_command([
                "sh", "-c", 
                f"echo '{request_json}' | node /app/dist/index.js"
            ])
            
            if not result["success"]:
                return {"error": f"Docker exec failed: {result['error']}"}
            
            # Parse JSON-RPC response
            try:
                response_json = result["output"].strip()
                if not response_json:
                    return {"error": "Empty response from MCP server"}
                
                # Handle potential multiple JSON responses (split by newlines)
                lines = response_json.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            response = json.loads(line)
                            if response.get("id") == request_id and "result" in response:
                                return response["result"]
                            elif "error" in response:
                                return {"error": f"MCP Server Error: {response['error']}"}
                        except json.JSONDecodeError:
                            continue
                
                # If no valid JSON-RPC response found, return raw output
                return {
                    "content": [{
                        "type": "text",
                        "text": response_json
                    }]
                }
                
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse MCP response: {e}. Raw output: {result['output'][:500]}"}
                
        except Exception as e:
            return {"error": f"Failed to execute Brave Search MCP tool: {e}"}
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute Brave Search MCP tool"""
        if not self.is_initialized:
            return {"error": "Brave Search MCP client not initialized"}
        
        if tool_name not in self.available_tools:
            return {"error": f"Unknown tool: {tool_name}. Available: {list(self.available_tools.keys())}"}
        
        try:
            # Call the MCP tool inside the container
            result = await self._run_mcp_tool(tool_name, arguments)
            return result
                
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}
    
    def get_available_tools(self) -> dict[str, dict]:
        """Get list of available Brave Search MCP tools"""
        return self.available_tools
    
    async def close(self):
        """Close Brave Search MCP client connection"""
        self.is_initialized = False
        print("🔌 Brave Search MCP client closed")


async def test_brave_search_client():
    """Test the Brave Search MCP client"""
    print("🧪 Testing Brave Search MCP Client")
    print("=" * 50)
    
    client = BraveSearchClient()
    
    # Initialize
    success = await client.initialize()
    if not success:
        print("❌ Failed to initialize Brave Search client")
        return
    
    print(f"\n🔧 Available tools: {len(client.get_available_tools())}")
    for tool_name, tool_info in client.get_available_tools().items():
        print(f"   • {tool_name}: {tool_info['description']}")
    
    # Test web search
    print("\n🔍 Testing web search...")
    result = await client.call_tool("brave_web_search", {
        "query": "Python programming", 
        "count": 3
    })
    
    if "error" not in result:
        print("✅ Web search successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ Web search failed: {result['error']}")
    
    # Test image search
    print("\n🖼️ Testing image search...")
    result = await client.call_tool("brave_image_search", {
        "searchTerm": "python logo",
        "count": 2
    })
    
    if "error" not in result:
        print("✅ Image search successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ Image search failed: {result['error']}")
    
    await client.close()
    
    print("\n🎯 Brave Search MCP Client Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_brave_search_client())
