#!/usr/bin/env python3
"""
Test script for all working MCP clients to verify they work correctly.
"""
import asyncio

from multi_mcp_client import MultiMCPClient


async def test_multi_mcp_client():
    """Test the updated Multi-MCP Client with working clients"""
    print("🧪 Testing Updated Multi-MCP Client")
    print("=" * 60)
    
    client = MultiMCPClient()
    
    # Initialize
    print("📡 Initializing Multi-MCP Client...")
    success = await client.initialize()
    print(f"📊 Init result: {success}")
    
    if not success:
        print("❌ Failed to initialize Multi-MCP Client")
        return
    
    # Show available servers
    available_servers = client.get_available_servers()
    print(f"\n🌐 Available servers: {len(available_servers)}")
    for server_id, server_info in available_servers.items():
        print(f"   • {server_info['name']} ({server_info['icon']}): {len(server_info['tools'])} tools")
    
    # Test filesystem (should work)
    if "filesystem" in available_servers:
        print("\n✅ Testing filesystem tool...")
        result = await client.call_tool("filesystem", "list_directory", {"path": "/projects"})
        print(f"📁 Filesystem result: {result}")
    
    # Test Brave Search (should now work with working client)
    if "brave_search" in available_servers:
        print("\n🔍 Testing brave search...")
        result = await client.call_tool("brave_search", "brave_web_search", {
            "query": "Python programming", 
            "count": 2
        })
        print(f"🔍 Brave search result: {result}")
    
    # Test GitHub (should now work with working client)
    if "github" in available_servers:
        print("\n🐙 Testing github tool...")
        result = await client.call_tool("github", "search_repositories", {
            "query": "python machine learning",
            "sort": "stars", 
            "order": "desc",
            "per_page": 2
        })
        print(f"🐙 GitHub result: {result}")
    
    await client.close()
    
    print("\n🎯 Updated Multi-MCP Client Test Complete!")
    print("   Now using dedicated working clients for each service!")


if __name__ == "__main__":
    asyncio.run(test_multi_mcp_client())
