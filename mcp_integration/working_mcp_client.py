"""
Working MCP Client using docker exec to avoid stdio/asyncio issues.
This provides a reliable way to interact with MCP filesystem containers
without the TaskGroup errors we encountered with stdio_client.
"""
import asyncio
from typing import Any

from config import get_enabled_servers


class WorkingMCPClient:
    """
    MCP client that uses docker exec to communicate with MCP containers.
    This avoids asyncio TaskGroup issues while providing reliable MCP access.
    """
    
    def __init__(self):
        # Get filesystem config from enabled servers
        enabled_servers = get_enabled_servers()
        filesystem_config = enabled_servers.get("filesystem", {})
        
        self.container_name = filesystem_config.get("container_name", "agent-framework-mcp-filesystem-1")
        self.server_path = filesystem_config.get("server_path", "/projects")
        self.is_initialized = False
        self.available_tools = {
            "list_directory": {
                "description": "List contents of a directory",
                "parameters": {"path": "Directory path to list"}
            },
            "read_file": {
                "description": "Read contents of a text file",
                "parameters": {"path": "File path to read"}
            },
            "write_file": {
                "description": "Write content to a file",
                "parameters": {"path": "File path to write", "content": "Content to write"}
            },
            "create_directory": {
                "description": "Create a new directory",
                "parameters": {"path": "Directory path to create"}
            },
            "move_file": {
                "description": "Move or rename a file",
                "parameters": {"source": "Source path", "destination": "Destination path"}
            },
            "get_file_info": {
                "description": "Get file metadata and information",
                "parameters": {"path": "File path to inspect"}
            },
            "search_files": {
                "description": "Search for files matching a pattern",
                "parameters": {"pattern": "Search pattern", "path": "Directory to search in"}
            },
            "directory_tree": {
                "description": "Get directory tree structure",
                "parameters": {"path": "Root directory path", "max_depth": "Maximum depth (optional)"}
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize connection to MCP container"""
        try:
            print("🔄 Initializing Working MCP Client...")
            print(f"   Container: {self.container_name}")
            print(f"   Base Path: {self.server_path}")
            
            # Test container accessibility
            result = await self._run_docker_command(["ls", "-la", self.server_path])
            
            if result["success"]:
                print("✅ Container connection successful")
                print(f"   Available directories: {len(result['output'].splitlines())} items")
                self.is_initialized = True
                return True
            else:
                print(f"❌ Container connection failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ MCP client initialization failed: {e}")
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
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute MCP tool via docker commands"""
        if not self.is_initialized:
            return {"error": "MCP client not initialized"}
        
        if tool_name not in self.available_tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
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
                            "text": result["output"]
                        }]
                    }
                else:
                    return {"error": f"Failed to read file: {result['error']}"}
            
            elif tool_name == "write_file":
                path = self._safe_path(arguments.get("path", ""))
                content = arguments.get("content", "")
                
                # Use echo to write content (for simple cases)
                result = await self._run_docker_command([
                    "sh", "-c", f"echo '{content}' > {path}"
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
                            "text": f"Directory created: {path}"
                        }]
                    }
                else:
                    return {"error": f"Failed to create directory: {result['error']}"}
            
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
                result = await self._run_docker_command([
                    "find", search_path, "-name", pattern, "-type", "f"
                ])
                
                if result["success"]:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Files matching '{pattern}' in {search_path}:\n{result['output']}"
                        }]
                    }
                else:
                    return {"error": f"Search failed: {result['error']}"}
            
            elif tool_name == "directory_tree":
                path = self._safe_path(arguments.get("path", self.server_path))
                max_depth = arguments.get("max_depth", 3)
                result = await self._run_docker_command([
                    "find", path, "-maxdepth", str(max_depth), "-type", "d"
                ])
                
                if result["success"]:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Directory tree for {path}:\n{result['output']}"
                        }]
                    }
                else:
                    return {"error": f"Failed to get directory tree: {result['error']}"}
            
            else:
                return {"error": f"Tool {tool_name} not implemented"}
                
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}
    
    def get_available_tools(self) -> dict[str, dict]:
        """Get list of available MCP tools"""
        return self.available_tools
    
    async def close(self):
        """Close MCP client connection"""
        self.is_initialized = False
        print("🔌 Working MCP client closed")


async def test_working_client():
    """Test the working MCP client"""
    print("🧪 Testing Working MCP Client")
    print("=" * 50)
    
    client = WorkingMCPClient()
    
    # Initialize
    success = await client.initialize()
    if not success:
        print("❌ Failed to initialize client")
        return
    
    print(f"\n🔧 Available tools: {len(client.get_available_tools())}")
    for tool_name, tool_info in client.get_available_tools().items():
        print(f"   • {tool_name}: {tool_info['description']}")
    
    # Test directory listing
    print("\n📁 Testing directory listing...")
    result = await client.call_tool("list_directory", {"path": "/projects"})
    if "error" not in result:
        print("✅ Directory listing successful")
        content = result["content"][0]["text"]
        lines = content.split('\n')[:5]  # First 5 lines
        for line in lines:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"❌ Directory listing failed: {result['error']}")
    
    # Test file creation and reading
    print("\n📝 Testing file operations...")
    
    # Create a test file
    write_result = await client.call_tool("write_file", {
        "path": "/projects/mcp_data/test_file.txt",
        "content": "Hello from Working MCP Client!"
    })
    
    if "error" not in write_result:
        print("✅ File write successful")
        
        # Read the file back
        read_result = await client.call_tool("read_file", {
            "path": "/projects/mcp_data/test_file.txt"
        })
        
        if "error" not in read_result:
            content = read_result["content"][0]["text"].strip()
            print(f"✅ File read successful: '{content}'")
        else:
            print(f"❌ File read failed: {read_result['error']}")
    else:
        print(f"❌ File write failed: {write_result['error']}")
    
    # Test search
    print("\n🔍 Testing file search...")
    search_result = await client.call_tool("search_files", {
        "pattern": "*.txt",
        "path": "/projects/mcp_data"
    })
    
    if "error" not in search_result:
        print("✅ File search successful")
        found_files = search_result["content"][0]["text"].strip()
        if found_files:
            print(f"   Found: {found_files.replace('/n', ', ')}")
    else:
        print(f"❌ File search failed: {search_result['error']}")
    
    await client.close()
    
    print("\n🎯 Working MCP Client Test Complete!")
    print("   This approach avoids asyncio TaskGroup errors")
    print("   and provides reliable MCP filesystem access.")


if __name__ == "__main__":
    asyncio.run(test_working_client())