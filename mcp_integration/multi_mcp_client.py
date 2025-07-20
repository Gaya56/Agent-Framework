"""
Multi-server MCP Client that can manage multiple MCP servers.
This replaces the single working_mcp_client with a flexible multi-server approach.
"""
from typing import Any

from config import get_enabled_servers
from working_mcp_client import WorkingMCPClient  
from working_brave_search_client import WorkingBraveSearchClient
from working_github_client import WorkingGitHubClient


class MCPServerClient:
    """Individual MCP server client"""
    
    def __init__(self, server_id: str, config: dict[str, Any]):
        self.server_id = server_id
        self.config = config
        self.container_name = config["container_name"]
        self.server_path = config["server_path"]
        self.is_initialized = False
        
        # Initialize the appropriate working client based on server type
        if server_id == "filesystem":
            self.working_client = WorkingMCPClient()
        elif server_id == "brave_search":
            self.working_client = WorkingBraveSearchClient()
        elif server_id == "github":
            self.working_client = WorkingGitHubClient()
        else:
            self.working_client = None
        
    async def initialize(self) -> bool:
        """Initialize connection to MCP container"""
        try:
            print(f"🔄 Initializing {self.config['name']}...")
            print(f"   Container: {self.container_name}")
            
            # Use the working client's initialization
            if self.working_client:
                success = await self.working_client.initialize()
                if success:
                    print(f"✅ {self.config['name']} connection successful")
                    self.is_initialized = True
                    return True
                else:
                    print(f"❌ {self.config['name']} connection failed")
                    return False
            else:
                print(f"❌ No working client available for {self.config['name']}")
                return False
                
        except Exception as e:
            print(f"❌ {self.config['name']} initialization failed: {e}")
            return False
    
    def get_available_tools(self) -> dict[str, dict[str, Any]]:
        """Get tools available for this server"""
        if self.working_client:
            return self.working_client.get_available_tools()
        return self.config.get("tools", {})
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute MCP tool via working clients"""
        if not self.is_initialized:
            return {"error": f"{self.config['name']} not initialized"}
        
        if not self.working_client:
            return {"error": f"No working client available for {self.config['name']}"}
        
        available_tools = self.get_available_tools()
        if tool_name not in available_tools:
            return {"error": f"Unknown tool '{tool_name}' for {self.config['name']}"}
        
        try:
            return await self.working_client.call_tool(tool_name, arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def close(self):
        """Close the working client connection"""
        if self.working_client:
            await self.working_client.close()


class MultiMCPClient:
    """Multi-server MCP client that manages multiple MCP servers"""
    
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
        for server in self.servers.values():
            await server.close()