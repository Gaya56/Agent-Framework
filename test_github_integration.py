#!/usr/bin/env python3
"""
Test script to verify GitHub MCP server integration
"""
import asyncio
import sys
import os

# Add mcp_integration to path
sys.path.append('/workspaces/Agent-Framework/mcp_integration')

from multi_mcp_client import MultiMCPClient

async def test_github_integration():
    """Test GitHub MCP server integration"""
    print("🧪 Testing GitHub MCP Server Integration...")
    
    # Check if GitHub token is set
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set in environment")
        return False
    else:
        print("✅ GitHub Personal Access Token found")
    
    try:
        # Initialize multi-MCP client
        client = MultiMCPClient()
        success = await client.initialize()
        
        if not success:
            print("❌ Failed to initialize Multi-MCP Client")
            return False
        
        print(f"✅ Multi-MCP Client initialized with {len(client.servers)} servers")
        
        # Check if GitHub server is available
        if "github" not in client.servers:
            print("❌ GitHub server not found in available servers")
            print(f"Available servers: {list(client.servers.keys())}")
            return False
        
        print("✅ GitHub server found in available servers")
        
        # Test a simple GitHub tool - search repositories
        print("\n🔍 Testing GitHub repository search...")
        result = await client.call_tool("github", "search_repositories", {
            "query": "python",
            "per_page": 3
        })
        
        if "error" in result:
            print(f"❌ GitHub tool test failed: {result['error']}")
            return False
        else:
            print("✅ GitHub repository search successful!")
            if "content" in result:
                print("📊 Sample result:")
                content = result["content"][0]["text"]
                # Print first few lines of result
                lines = content.split("\n")[:5]
                for line in lines:
                    print(f"   {line}")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_github_integration())
    if result:
        print("\n🎉 GitHub MCP Server integration test PASSED!")
    else:
        print("\n💥 GitHub MCP Server integration test FAILED!")
