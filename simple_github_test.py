#!/usr/bin/env python3
"""
Simple GitHub MCP integration test that can run from the host system.
"""
import asyncio
import subprocess
import json
import sys
import os

# Add the mcp_integration directory to Python path
sys.path.append('/workspaces/Agent-Framework/mcp_integration')

from multi_mcp_client import MultiMCPClient

async def test_github_search():
    """Test GitHub repository search functionality"""
    print("🧪 Testing GitHub MCP Server Integration...")
    
    # Test if GitHub container is accessible
    try:
        result = subprocess.run([
            'docker', 'exec', 'agent-framework-mcp-github-1', 
            'echo', 'GitHub container is accessible'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ GitHub container is accessible")
        else:
            print(f"❌ GitHub container access failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Container accessibility test failed: {e}")
        return False
    
    # Initialize MCP client
    try:
        client = MultiMCPClient()
        success = await client.initialize()
        
        if not success:
            print("❌ MCP Client initialization failed")
            return False
            
        print(f"✅ MCP Client initialized with {len(client.servers)} servers")
        
        # Check if GitHub server is available
        if "github" not in client.servers:
            print("❌ GitHub server not found in initialized servers")
            return False
            
        print("✅ GitHub server found and initialized")
        
        # Test a simple GitHub search
        print("\n🔍 Testing GitHub repository search...")
        
        search_result = await client.call_tool("github", "search_repositories", {
            "query": "python mcp",
            "per_page": 3
        })
        
        if "error" in search_result:
            print(f"❌ GitHub search failed: {search_result['error']}")
            return False
        else:
            print("✅ GitHub search completed successfully!")
            if "content" in search_result and search_result["content"]:
                content = search_result["content"][0]["text"]
                print(f"📊 Search results preview:\n{content[:300]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ GitHub integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting GitHub MCP Integration Test...")
    
    # Check if GitHub token is set
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if github_token:
        print("✅ GitHub Personal Access Token found")
    else:
        print("❌ GitHub Personal Access Token not found in environment")
        return
    
    success = await test_github_search()
    
    if success:
        print("\n🎉 GitHub MCP Server integration test PASSED!")
        print("✅ GitHub server is properly integrated and functional")
    else:
        print("\n💥 GitHub MCP Server integration test FAILED!")

if __name__ == "__main__":
    asyncio.run(main())
