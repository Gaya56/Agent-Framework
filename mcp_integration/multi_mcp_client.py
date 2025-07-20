"""
Multi-server MCP Client that can manage multiple MCP servers.
This replaces the single working_mcp_client with a flexible multi-server approach.
"""
import asyncio
from typing import Any

from config import get_enabled_servers


class MCPServerClient:
    """Individual MCP server client (similar to WorkingMCPClient but server-specific)"""
    
    def __init__(self, server_id: str, config: dict[str, Any]):
        self.server_id = server_id
        self.config = config
        self.container_name = config["container_name"]
        self.server_path = config["server_path"]
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize connection to MCP container"""
        try:
            print(f"🔄 Initializing {self.config['name']}...")
            print(f"   Container: {self.container_name}")
            print(f"   Base Path: {self.server_path}")
            
            # Test container accessibility
            result = await self._run_docker_command(["ls", "-la", self.server_path])
            
            if result["success"]:
                print(f"✅ {self.config['name']} connection successful")
                self.is_initialized = True
                return True
            else:
                print(f"❌ {self.config['name']} connection failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ {self.config['name']} initialization failed: {e}")
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
    
    def _safe_path(self, path: str) -> str:
        """Ensure path is safe and within server boundaries"""
        if not path.startswith('/'):
            path = f"{self.server_path}/{path}"
        
        # Basic path safety (expand this as needed)
        path = path.replace('..', '')
        return path
    
    def get_available_tools(self) -> dict[str, dict[str, Any]]:
        """Get tools available for this server"""
        return self.config.get("tools", {})
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute MCP tool via docker commands"""
        if not self.is_initialized:
            return {"error": f"{self.config['name']} not initialized"}
        
        available_tools = self.get_available_tools()
        if tool_name not in available_tools:
            return {"error": f"Unknown tool '{tool_name}' for {self.config['name']}"}
        
        try:
            # For now, only implement filesystem tools since that's what we have
            if self.server_id == "filesystem":
                return await self._call_filesystem_tool(tool_name, arguments)
            elif self.server_id == "brave_search":
                return await self._call_brave_search_tool(tool_name, arguments)
            elif self.server_id == "github":
                return await self._call_github_tool(tool_name, arguments)
            else:
                return {"error": f"Tool execution not yet implemented for {self.config['name']}"}
                
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def _call_filesystem_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute filesystem-specific tools"""
        if tool_name == "list_directory":
            path = self._safe_path(arguments.get("path", self.server_path))
            result = await self._run_docker_command(["ls", "-la", path])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Directory listing for {path}:\n{result['output']}"
                    }]
                }
            else:
                return {"error": f"Failed to list directory: {result['error']}"}
        
        elif tool_name == "read_file":
            path = self._safe_path(arguments.get("path", ""))
            result = await self._run_docker_command(["cat", path])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"Contents of {path}:\n{result['output']}"
                    }]
                }
            else:
                return {"error": f"Failed to read file: {result['error']}"}
        
        elif tool_name == "write_file":
            path = self._safe_path(arguments.get("path", ""))
            content = arguments.get("content", "")
            
            # Use echo to write content (better than cat << EOF for simple content)
            result = await self._run_docker_command([
                "sh", "-c", f"echo '{content}' > '{path}'"
            ])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully wrote to {path}"
                    }]
                }
            else:
                return {"error": f"Failed to write file: {result['error']}"}
        
        elif tool_name == "create_directory":
            path = self._safe_path(arguments.get("path", ""))
            result = await self._run_docker_command(["mkdir", "-p", path])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully created directory {path}"
                    }]
                }
            else:
                return {"error": f"Failed to create directory: {result['error']}"}
        
        elif tool_name == "move_file":
            source = self._safe_path(arguments.get("source", ""))
            destination = self._safe_path(arguments.get("destination", ""))
            result = await self._run_docker_command(["mv", source, destination])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Successfully moved {source} to {destination}"
                    }]
                }
            else:
                return {"error": f"Failed to move file: {result['error']}"}
        
        elif tool_name == "get_file_info":
            path = self._safe_path(arguments.get("path", ""))
            result = await self._run_docker_command(["stat", path])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"File info for {path}:\n{result['output']}"
                    }]
                }
            else:
                return {"error": f"Failed to get file info: {result['error']}"}
        
        elif tool_name == "search_files":
            pattern = arguments.get("pattern", "*")
            search_path = self._safe_path(arguments.get("path", self.server_path))
            result = await self._run_docker_command(["find", search_path, "-name", pattern])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Search results for '{pattern}' in {search_path}:\n{result['output']}"
                    }]
                }
            else:
                return {"error": f"Failed to search files: {result['error']}"}
        
        elif tool_name == "directory_tree":
            path = self._safe_path(arguments.get("path", self.server_path))
            max_depth = arguments.get("max_depth", 3)
            result = await self._run_docker_command(["find", path, "-maxdepth", str(max_depth), "-type", "d"])
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Directory tree for {path} (max depth {max_depth}):\n{result['output']}"
                    }]
                }
            else:
                return {"error": f"Failed to get directory tree: {result['error']}"}
        
        else:
            return {"error": f"Unknown filesystem tool: {tool_name}"}

    async def _call_brave_search_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute Brave search-specific tools"""
        import json
        
        # Prepare the MCP request payload
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Convert to JSON string for the curl command
        json_payload = json.dumps(mcp_request)
        
        # Build the curl command to call the MCP server via HTTP
        curl_cmd = [
            "sh", "-c",
            f"curl -s -X POST http://localhost:8080 -H 'Content-Type: application/json' -d '{json_payload}'"
        ]
        
        # Execute the curl command in the Brave search container
        result = await self._run_docker_command(curl_cmd)
        
        if result["success"]:
            try:
                # Parse the JSON response
                response_data = json.loads(result["output"])
                
                # Check if the MCP response contains an error
                if "error" in response_data:
                    return {"error": f"Brave Search API error: {response_data['error']}"}
                
                # Return the result in the expected format
                if "result" in response_data:
                    # Format the search results for display
                    search_results = response_data["result"]
                    formatted_results = self._format_brave_search_results(tool_name, search_results)
                    
                    return {
                        "content": [{
                            "type": "text",
                            "text": formatted_results
                        }]
                    }
                else:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Search completed but no results returned: {result['output']}"
                        }]
                    }
                    
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse Brave Search response: {e}\nRaw output: {result['output']}"}
        else:
            return {"error": f"Failed to call Brave Search API: {result['error']}"}

    def _format_brave_search_results(self, tool_name: str, results: dict) -> str:
        """Format Brave search results for display"""
        if tool_name == "brave_web_search":
            if "web" in results and "results" in results["web"]:
                formatted = "🔍 Web Search Results:\n\n"
                for i, result in enumerate(results["web"]["results"][:10], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    description = result.get("description", "No description")
                    formatted += f"{i}. **{title}**\n   {url}\n   {description}\n\n"
                return formatted
            else:
                return "No web search results found."
                
        elif tool_name == "brave_image_search":
            if "images" in results and "results" in results["images"]:
                formatted = "🖼️ Image Search Results:\n\n"
                for i, result in enumerate(results["images"]["results"][:5], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    thumbnail = result.get("thumbnail", {}).get("src", "No thumbnail")
                    formatted += f"{i}. **{title}**\n   Image: {url}\n   Thumbnail: {thumbnail}\n\n"
                return formatted
            else:
                return "No image search results found."
                
        elif tool_name == "brave_video_search":
            if "videos" in results and "results" in results["videos"]:
                formatted = "🎥 Video Search Results:\n\n"
                for i, result in enumerate(results["videos"]["results"][:10], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    duration = result.get("duration", "Unknown duration")
                    formatted += f"{i}. **{title}**\n   {url}\n   Duration: {duration}\n\n"
                return formatted
            else:
                return "No video search results found."
                
        elif tool_name == "brave_news_search":
            if "news" in results and "results" in results["news"]:
                formatted = "📰 News Search Results:\n\n"
                for i, result in enumerate(results["news"]["results"][:10], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    description = result.get("description", "No description")
                    age = result.get("age", "Unknown date")
                    formatted += f"{i}. **{title}**\n   {url}\n   {description}\n   Published: {age}\n\n"
                return formatted
            else:
                return "No news search results found."
                
        elif tool_name == "brave_local_search":
            if "locations" in results and "results" in results["locations"]:
                formatted = "📍 Local Search Results:\n\n"
                for i, result in enumerate(results["locations"]["results"][:10], 1):
                    title = result.get("title", "No title")
                    address = result.get("address", "No address")
                    phone = result.get("phone", "No phone")
                    rating = result.get("rating", {}).get("value", "No rating")
                    formatted += f"{i}. **{title}**\n   {address}\n   Phone: {phone}\n   Rating: {rating}\n\n"
                return formatted
            else:
                return "No local search results found."
        
        # Fallback for unknown result format
        return f"Search completed. Raw results: {str(results)}"

    async def _call_github_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute GitHub-specific tools via STDIO protocol"""
        import json
        
        # Build MCP request payload
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        json_payload = json.dumps(mcp_request)
        
        # Execute via STDIO - GitHub server uses stdin/stdout
        stdin_cmd = [
            "sh", "-c", 
            f"echo '{json_payload}' | docker exec -i {self.container_name} node dist/index.js"
        ]
        
        result = await self._run_docker_command(stdin_cmd)
        
        if result["success"]:
            try:
                response_data = json.loads(result["output"])
                
                if "error" in response_data:
                    return {"error": f"GitHub API error: {response_data['error']}"}
                
                if "result" in response_data:
                    formatted_results = self._format_github_results(tool_name, response_data["result"])
                    return {
                        "content": [{
                            "type": "text",
                            "text": formatted_results
                        }]
                    }
                else:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"GitHub tool completed: {result['output']}"
                        }]
                    }
                    
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse GitHub response: {e}\nRaw output: {result['output']}"}
        else:
            return {"error": f"Failed to call GitHub API: {result['error']}"}

    def _format_github_results(self, tool_name: str, results: dict) -> str:
        """Format GitHub API results for display"""
        
        if tool_name == "create_or_update_file":
            if "commit" in results:
                commit = results["commit"]
                file_url = results.get("content", {}).get("html_url", "N/A")
                return f"✅ File created/updated successfully!\n📄 File URL: {file_url}\n🔗 Commit: {commit.get('html_url', 'N/A')}\n📝 SHA: {commit.get('sha', 'N/A')}"
            else:
                return f"File operation completed: {str(results)}"
                
        elif tool_name == "push_files":
            if "commit" in results:
                commit = results["commit"]
                return f"✅ Files pushed successfully!\n🔗 Commit: {commit.get('html_url', 'N/A')}\n📝 SHA: {commit.get('sha', 'N/A')}\n📁 Files: {len(results.get('files', []))}"
            else:
                return f"Push operation completed: {str(results)}"
                
        elif tool_name == "search_repositories":
            if "items" in results:
                formatted = f"🔍 Found {results.get('total_count', 0)} repositories:\n\n"
                for i, repo in enumerate(results["items"][:10], 1):
                    name = repo.get("full_name", "N/A")
                    description = repo.get("description", "No description")
                    stars = repo.get("stargazers_count", 0)
                    url = repo.get("html_url", "N/A")
                    formatted += f"{i}. **{name}** ⭐ {stars}\n   {url}\n   {description}\n\n"
                return formatted
            else:
                return "No repositories found."
                
        elif tool_name == "create_repository":
            name = results.get("full_name", "N/A")
            url = results.get("html_url", "N/A")
            return f"✅ Repository created successfully!\n📚 {name}\n🔗 {url}"
            
        elif tool_name == "get_file_contents":
            content = results.get("content", "")
            path = results.get("path", "N/A")
            url = results.get("html_url", "N/A")
            return f"📄 File: {path}\n🔗 URL: {url}\n\n```\n{content}\n```"
            
        elif tool_name == "create_issue":
            number = results.get("number", "N/A")
            title = results.get("title", "N/A")
            url = results.get("html_url", "N/A")
            return f"✅ Issue created successfully!\n🐛 #{number}: {title}\n🔗 {url}"
            
        elif tool_name == "create_pull_request":
            number = results.get("number", "N/A")
            title = results.get("title", "N/A")
            url = results.get("html_url", "N/A")
            return f"✅ Pull request created successfully!\n🔄 #{number}: {title}\n🔗 {url}"
            
        elif tool_name == "fork_repository":
            name = results.get("full_name", "N/A")
            url = results.get("html_url", "N/A")
            return f"✅ Repository forked successfully!\n🍴 {name}\n🔗 {url}"
            
        elif tool_name == "create_branch":
            ref = results.get("ref", "N/A")
            sha = results.get("object", {}).get("sha", "N/A")
            return f"✅ Branch created successfully!\n🌿 {ref}\n📝 SHA: {sha}"
            
        elif tool_name == "list_issues":
            if isinstance(results, list):
                formatted = f"🐛 Found {len(results)} issues:\n\n"
                for i, issue in enumerate(results[:10], 1):
                    number = issue.get("number", "N/A")
                    title = issue.get("title", "N/A")
                    state = issue.get("state", "N/A")
                    url = issue.get("html_url", "N/A")
                    formatted += f"{i}. #{number} [{state.upper()}] {title}\n   🔗 {url}\n\n"
                return formatted
            else:
                return "No issues found."
                
        elif tool_name == "update_issue":
            number = results.get("number", "N/A")
            title = results.get("title", "N/A")
            state = results.get("state", "N/A")
            url = results.get("html_url", "N/A")
            return f"✅ Issue updated successfully!\n🐛 #{number} [{state.upper()}]: {title}\n🔗 {url}"
            
        elif tool_name == "add_issue_comment":
            url = results.get("html_url", "N/A")
            return f"✅ Comment added successfully!\n💬 {url}"
            
        elif tool_name == "search_code":
            if "items" in results:
                formatted = f"🔍 Found {results.get('total_count', 0)} code results:\n\n"
                for i, item in enumerate(results["items"][:10], 1):
                    name = item.get("name", "N/A")
                    path = item.get("path", "N/A")
                    repo = item.get("repository", {}).get("full_name", "N/A")
                    url = item.get("html_url", "N/A")
                    formatted += f"{i}. **{name}** in {repo}\n   📁 {path}\n   🔗 {url}\n\n"
                return formatted
            else:
                return "No code results found."
                
        elif tool_name == "search_issues":
            if "items" in results:
                formatted = f"🔍 Found {results.get('total_count', 0)} issues/PRs:\n\n"
                for i, item in enumerate(results["items"][:10], 1):
                    number = item.get("number", "N/A")
                    title = item.get("title", "N/A")
                    state = item.get("state", "N/A")
                    repo = item.get("repository_url", "").split("/")[-2:] if item.get("repository_url") else ["N/A"]
                    repo_name = "/".join(repo) if len(repo) == 2 else "N/A"
                    url = item.get("html_url", "N/A")
                    formatted += f"{i}. #{number} [{state.upper()}] {title}\n   📚 {repo_name}\n   🔗 {url}\n\n"
                return formatted
            else:
                return "No issues/PRs found."
        
        # Fallback for unknown result format
        return f"GitHub operation completed. Results: {str(results)}"


class MultiMCPClient:
    """
    Multi-server MCP client that manages multiple MCP servers.
    Provides a unified interface for server selection and tool execution.
    """
    
    def __init__(self):
        self.servers: dict[str, MCPServerClient] = {}
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all enabled MCP servers"""
        try:
            print("🔄 Initializing Multi-MCP Client...")
            
            enabled_servers = get_enabled_servers()
            if not enabled_servers:
                print("⚠️ No enabled MCP servers found")
                return False
            
            # Initialize each server
            for server_id, config in enabled_servers.items():
                server_client = MCPServerClient(server_id, config)
                success = await server_client.initialize()
                
                if success:
                    self.servers[server_id] = server_client
                    print(f"✅ {config['name']} ready")
                else:
                    print(f"❌ {config['name']} failed to initialize")
            
            if self.servers:
                print(f"✅ Multi-MCP Client initialized with {len(self.servers)} servers")
                self.is_initialized = True
                return True
            else:
                print("❌ No MCP servers successfully initialized")
                return False
                
        except Exception as e:
            print(f"❌ Multi-MCP Client initialization failed: {e}")
            return False
    
    def get_available_servers(self) -> dict[str, dict[str, Any]]:
        """Get all available/initialized servers"""
        return {
            server_id: {
                "name": server.config["name"],
                "description": server.config["description"], 
                "icon": server.config["icon"],
                "tools": list(server.get_available_tools().keys())
            }
            for server_id, server in self.servers.items()
        }
    
    def get_server_tools(self, server_id: str) -> dict[str, dict[str, Any]]:
        """Get tools available for a specific server"""
        if server_id in self.servers:
            return self.servers[server_id].get_available_tools()
        return {}
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute tool on specific server"""
        if not self.is_initialized:
            return {"error": "Multi-MCP Client not initialized"}
        
        if server_id not in self.servers:
            available = list(self.servers.keys())
            return {"error": f"Server '{server_id}' not available. Available servers: {available}"}
        
        return await self.servers[server_id].call_tool(tool_name, arguments)
    
    async def close(self):
        """Clean up resources"""
        # For now, no cleanup needed as we use docker exec
        # Future servers might need connection cleanup
        pass
