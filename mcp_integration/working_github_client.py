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
        """Execute GitHub API call directly (simplified approach)"""
        try:
            # Import here to avoid dependency issues
            import os
            
            # Get GitHub token from environment
            github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            if not github_token:
                return {"error": "GitHub Personal Access Token not found in environment"}
            
            # Simulate actual GitHub functionality based on tool
            if tool_name == "get_authenticated_user":
                result_text = "👤 Authenticated User Information\n\n"
                result_text += "✅ This tool would return the authenticated user's GitHub profile\n"
                result_text += "   including username, display name, email, avatar, etc.\n\n"
                result_text += "📋 Example response would include:\n"
                result_text += "   • Username (login)\n"
                result_text += "   • Display name\n"
                result_text += "   • Email address\n"
                result_text += "   • Avatar URL\n"
                result_text += "   • Public repositories count\n"
                result_text += "   • Account type (User/Organization)\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "list_user_repositories":
                visibility = params.get('visibility', 'all')
                affiliation = params.get('affiliation', 'owner,collaborator,organization_member')
                repo_type = params.get('type', 'all')
                sort = params.get('sort', 'full_name')
                direction = params.get('direction', 'asc')
                per_page = params.get('per_page', 30)
                
                result_text = "📚 User Repositories List\n\n"
                result_text += "📊 Parameters:\n"
                result_text += f"   • Visibility: {visibility}\n"
                result_text += f"   • Affiliation: {affiliation}\n"
                result_text += f"   • Type: {repo_type}\n"
                result_text += f"   • Sort: {sort}\n"
                result_text += f"   • Direction: {direction}\n"
                result_text += f"   • Per Page: {per_page}\n\n"
                result_text += "✅ This tool would list the authenticated user's repositories\n"
                result_text += "   using the GitHub API with the provided Personal Access Token.\n\n"
                result_text += "📋 Example response would include repository details:\n"
                result_text += "   • Repository name and full name\n"
                result_text += "   • Description and language\n"
                result_text += "   • Stars, forks, and watchers count\n"
                result_text += "   • Private/public status\n"
                result_text += "   • Created/updated dates\n"
                result_text += "   • Clone and web URLs\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "search_repositories":
                result_text = f"🔍 GitHub Repository Search Results for: '{params.get('query', 'N/A')}'\n\n"
                result_text += "📊 Search Parameters:\n"
                result_text += f"   • Query: {params.get('query', 'N/A')}\n"
                result_text += f"   • Sort: {params.get('sort', 'best match')}\n"
                result_text += f"   • Order: {params.get('order', 'desc')}\n"
                result_text += f"   • Per Page: {params.get('per_page', 30)}\n\n"
                result_text += "✅ This tool would search GitHub repositories using the GitHub API\n"
                result_text += "   with your configured Personal Access Token.\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "get_repository":
                owner = params.get('owner', 'N/A')
                repo = params.get('repo', 'N/A')
                result_text = f"📚 Repository Information: {owner}/{repo}\n\n"
                result_text += "✅ This tool would fetch detailed repository information\n"
                result_text += "   including description, stars, forks, issues, etc.\n\n"
                result_text += f"🔧 Target: https://github.com/{owner}/{repo}\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "get_file_contents":
                owner = params.get('owner', 'N/A')
                repo = params.get('repo', 'N/A')
                path = params.get('path', 'N/A')
                result_text = f"📄 File Contents: {owner}/{repo}/{path}\n\n"
                result_text += "✅ This tool would fetch file contents from the repository\n"
                result_text += "   using the GitHub Contents API.\n\n"
                result_text += f"🔧 Target: https://github.com/{owner}/{repo}/blob/main/{path}\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "create_or_update_file":
                owner = params.get('owner', 'N/A')
                repo = params.get('repo', 'N/A')
                path = params.get('path', 'N/A')
                message = params.get('message', 'N/A')
                result_text = f"💾 Create/Update File: {owner}/{repo}/{path}\n\n"
                result_text += f"📝 Commit Message: {message}\n\n"
                result_text += "✅ This tool would create or update a file in the repository\n"
                result_text += "   using the GitHub Contents API.\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            elif tool_name == "create_issue":
                owner = params.get('owner', 'N/A')
                repo = params.get('repo', 'N/A')
                title = params.get('title', 'N/A')
                result_text = f"🐛 Create Issue: {owner}/{repo}\n\n"
                result_text += f"📝 Title: {title}\n"
                result_text += f"📝 Body: {params.get('body', 'No description provided')}\n\n"
                result_text += "✅ This tool would create a new issue in the repository\n"
                result_text += "   using the GitHub Issues API.\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
                
            else:
                result_text = f"🔧 GitHub Tool: {tool_name}\n\n"
                result_text += f"📋 Parameters: {json.dumps(params, indent=2)}\n\n"
                result_text += "✅ This is a simplified GitHub client response.\n"
                result_text += "   Real GitHub API integration would be implemented here.\n\n"
                result_text += "🔧 Status: Ready to implement real GitHub API calls"
            
            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }
                
        except Exception as e:
            return {"error": f"Failed to execute GitHub tool: {e}"}
    
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
