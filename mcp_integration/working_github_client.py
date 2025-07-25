"""
Working GitHub MCP Client using docker exec to communicate with GitHub container.
This follows the same reliable pattern as working_mcp_client.py for filesystem operations.
"""
import asyncio
import json
from typing import Any

from config import get_enabled_servers


class WorkingGitHubClient:
    """
    GitHub MCP client that uses docker exec to communicate with GitHub container.
    This follows the same reliable pattern as the filesystem client.
    """
    
    def __init__(self):
        # Get github config from enabled servers
        enabled_servers = get_enabled_servers()
        github_config = enabled_servers.get("github", {})
        
        self.container_name = github_config.get("container_name", "agent-framework-mcp-github-1")
        self.server_path = github_config.get("server_path", "/app")
        self.is_initialized = False
        self.available_tools = {
            "get_authenticated_user": {
                "description": "Get the authenticated user's information",
                "parameters": {}
            },
            "list_user_repositories": {
                "description": "List repositories for the authenticated user",
                "parameters": {
                    "visibility": "Repository visibility (all, public, private)",
                    "affiliation": "Relationship to repos (owner, collaborator, organization_member)",
                    "type": "Repository type (all, owner, public, private, member)",
                    "sort": "Sort criteria (created, updated, pushed, full_name)",
                    "direction": "Sort direction (asc, desc)",
                    "per_page": "Number of results per page (max 100)"
                }
            },
            "search_repositories": {
                "description": "Search GitHub repositories",
                "parameters": {
                    "query": "Search query string",
                    "sort": "Sort criteria (stars, forks, help-wanted-issues, updated)",
                    "order": "Sort order (asc, desc)",
                    "per_page": "Number of results per page (max 100)"
                }
            },
            "get_repository": {
                "description": "Get detailed information about a repository",
                "parameters": {
                    "owner": "Repository owner username",
                    "repo": "Repository name"
                }
            },
            "create_repository": {
                "description": "Create a new repository",
                "parameters": {
                    "name": "Repository name",
                    "description": "Repository description",
                    "private": "Whether repository should be private (true/false)"
                }
            },
            "get_file_contents": {
                "description": "Get the contents of a file in a repository",
                "parameters": {
                    "owner": "Repository owner username",
                    "repo": "Repository name", 
                    "path": "File path within the repository"
                }
            },
            "create_or_update_file": {
                "description": "Create or update a file in a repository",
                "parameters": {
                    "owner": "Repository owner username",
                    "repo": "Repository name",
                    "path": "File path within the repository",
                    "content": "File content",
                    "message": "Commit message"
                }
            },
            "create_issue": {
                "description": "Create an issue in a repository",
                "parameters": {
                    "owner": "Repository owner username",
                    "repo": "Repository name",
                    "title": "Issue title",
                    "body": "Issue body content"
                }
            },
            "search_code": {
                "description": "Search code across GitHub repositories",
                "parameters": {
                    "query": "Code search query",
                    "sort": "Sort criteria (indexed)",
                    "order": "Sort order (asc, desc)"
                }
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize connection to GitHub MCP container"""
        try:
            print("🔄 Initializing GitHub MCP Client...")
            print(f"   Container: {self.container_name}")
            print(f"   Base Path: {self.server_path}")
            
            # Test container accessibility
            result = await self._run_docker_command(["ls", "-la", self.server_path])
            
            if result["success"]:
                print("✅ GitHub container connection successful")
                self.is_initialized = True
                return True
            else:
                print(f"❌ GitHub container connection failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ GitHub MCP client initialization failed: {e}")
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
        """Execute GitHub MCP tool via docker exec and JSON-RPC communication"""
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
            return {"error": f"Failed to execute GitHub MCP tool: {e}"}
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute GitHub MCP tool"""
        if not self.is_initialized:
            return {"error": "GitHub MCP client not initialized"}
        
        if tool_name not in self.available_tools:
            return {"error": f"Unknown tool: {tool_name}. Available: {list(self.available_tools.keys())}"}
        
        try:
            # Call the MCP tool inside the container
            result = await self._run_mcp_tool(tool_name, arguments)
            return result
                
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}
    
    def get_available_tools(self) -> dict[str, dict]:
        """Get list of available GitHub MCP tools"""
        return self.available_tools
    
    async def close(self):
        """Close GitHub MCP client connection"""
        self.is_initialized = False
        print("🔌 GitHub MCP client closed")


async def test_github_client():
    """Test the GitHub MCP client"""
    print("🧪 Testing GitHub MCP Client")
    print("=" * 50)
    
    client = WorkingGitHubClient()
    
    # Initialize
    success = await client.initialize()
    if not success:
        print("❌ Failed to initialize GitHub client")
        return
    
    print(f"\n🔧 Available tools: {len(client.get_available_tools())}")
    for tool_name, tool_info in client.get_available_tools().items():
        print(f"   • {tool_name}: {tool_info['description']}")
    
    # Test get authenticated user
    print("\n👤 Testing get authenticated user...")
    result = await client.call_tool("get_authenticated_user", {})
    
    if "error" not in result:
        print("✅ Get authenticated user successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ Get authenticated user failed: {result['error']}")
    
    # Test list user repositories
    print("\n📚 Testing list user repositories...")
    result = await client.call_tool("list_user_repositories", {
        "visibility": "public",
        "type": "owner",
        "sort": "updated",
        "direction": "desc",
        "per_page": 5
    })
    
    if "error" not in result:
        print("✅ List user repositories successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ List user repositories failed: {result['error']}")
    
    # Test repository search
    print("\n🔍 Testing repository search...")
    result = await client.call_tool("search_repositories", {
        "query": "python machine learning", 
        "sort": "stars",
        "order": "desc",
        "per_page": 3
    })
    
    if "error" not in result:
        print("✅ Repository search successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ Repository search failed: {result['error']}")
    
    # Test get repository info
    print("\n📚 Testing get repository...")
    result = await client.call_tool("get_repository", {
        "owner": "python",
        "repo": "cpython"
    })
    
    if "error" not in result:
        print("✅ Get repository successful")
        if "content" in result:
            content = result["content"][0]["text"]
            print(f"   Results: {content[:200]}...")
    else:
        print(f"❌ Get repository failed: {result['error']}")
    
    await client.close()
    
    print("\n🎯 GitHub MCP Client Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_github_client())
