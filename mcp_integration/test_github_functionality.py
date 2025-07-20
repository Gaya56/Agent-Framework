#!/usr/bin/env python3
"""
Simple test to verify GitHub MCP functionality works correctly.
"""
import asyncio

from multi_mcp_client import MultiMCPClient


async def test_github_functionality():
    """Test GitHub MCP functionality specifically"""
    print("🐙 Testing GitHub MCP Functionality")
    print("=" * 50)
    
    client = MultiMCPClient()
    
    # Initialize
    print("🔄 Initializing Multi-MCP Client...")
    success = await client.initialize()
    if not success:
        print("❌ Failed to initialize Multi-MCP Client")
        return
    
    # Check if GitHub server is available
    available_servers = client.get_available_servers()
    if "github" not in available_servers:
        print("❌ GitHub server not available")
        return
    
    print("✅ GitHub server is available")
    github_tools = client.get_server_tools("github")
    print(f"🔧 Available GitHub tools: {list(github_tools.keys())}")
    
    # Test 1: Search repositories (what the user wanted)
    print("\n🔍 Test 1: Search for popular repositories...")
    search_result = await client.call_tool("github", "search_repositories", {
        "query": "python machine learning stars:>1000",
        "sort": "stars",
        "order": "desc", 
        "per_page": 3
    })
    
    if "error" not in search_result:
        print("✅ Repository search successful")
        if "content" in search_result:
            content = search_result["content"][0]["text"]
            print(f"📋 Results: {content[:300]}...")
    else:
        print(f"❌ Repository search failed: {search_result['error']}")
    
    # Test 2: Search user's repositories (if we have access)
    print("\n👤 Test 2: Search for user repositories...")
    user_repos_result = await client.call_tool("github", "search_repositories", {
        "query": "user:Gaya56",
        "sort": "updated",
        "order": "desc",
        "per_page": 5
    })
    
    if "error" not in user_repos_result:
        print("✅ User repository search successful") 
        if "content" in user_repos_result:
            content = user_repos_result["content"][0]["text"]
            print(f"📋 User repos: {content[:300]}...")
    else:
        print(f"❌ User repository search failed: {user_repos_result['error']}")
    
    # Test 3: Search for recently updated repos
    print("\n⏰ Test 3: Search for recently updated repositories...")
    recent_result = await client.call_tool("github", "search_repositories", {
        "query": "language:python pushed:>2024-07-01",
        "sort": "updated",
        "order": "desc",
        "per_page": 3
    })
    
    if "error" not in recent_result:
        print("✅ Recent repository search successful")
        if "content" in recent_result:
            content = recent_result["content"][0]["text"] 
            print(f"📋 Recent repos: {content[:300]}...")
    else:
        print(f"❌ Recent repository search failed: {recent_result['error']}")
    
    await client.close()
    
    print("\n🎯 GitHub MCP Test Complete!")
    print("   If these work, then the GitHub integration is functioning properly.")


if __name__ == "__main__":
    asyncio.run(test_github_functionality())
