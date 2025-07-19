"""
Updated MCP OpenAI Bot using the multi-server MCP client.
This version works with server selection and uses docker exec to avoid asyncio issues.
"""
import asyncio
import json
from datetime import datetime

import openai
from config import OPENAI_API_KEY
from multi_mcp_client import MultiMCPClient


class MCPOpenAIBot:
    """OpenAI bot with MCP multi-server tools"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize Multi-MCP client
        self.mcp_client = MultiMCPClient()
        self.mcp_ready = False
        self.default_server = "filesystem"  # Default to filesystem server
        
    async def initialize(self):
        """Initialize MCP connection"""
        print("🤖 Initializing MCP OpenAI Bot...")
        
        # Initialize MCP client
        self.mcp_ready = await self.mcp_client.initialize()
        
        if self.mcp_ready:
            available_servers = self.mcp_client.get_available_servers()
            total_tools = sum(len(info['tools']) for info in available_servers.values())
            print(f"✅ Bot ready with {len(available_servers)} servers and {total_tools} total MCP tools")
            return True
        else:
            print("❌ Bot initialization failed - MCP not available")
            return False
    
    def get_available_tools(self):
        """Get available tools from default server (for compatibility)"""
        if not self.mcp_ready:
            return {}
        return self.mcp_client.get_server_tools(self.default_server)
    
    def _create_openai_tools(self):
        """Convert MCP tools to OpenAI function format"""
        mcp_tools = self.get_available_tools()
        openai_tools = []
        
        for tool_name, tool_info in mcp_tools.items():
            # Create OpenAI function schema
            properties = {}
            required = []
            
            for param_name, param_desc in tool_info["parameters"].items():
                properties[param_name] = {
                    "type": "string",
                    "description": param_desc
                }
                required.append(param_name)
            
            function_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info["description"], 
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            openai_tools.append(function_def)
            
        return openai_tools
    
    async def _execute_mcp_tool(self, tool_name: str, arguments: dict):
        """Execute MCP tool and return result"""
        if not self.mcp_ready:
            return "MCP tools are not available"
        
        result = await self.mcp_client.call_tool(self.default_server, tool_name, arguments)
        
        if "error" in result:
            return f"Error: {result['error']}"
        elif "content" in result:
            return result["content"][0]["text"]
        else:
            return str(result)
    
    async def chat(self, user_message: str) -> str:
        """Chat with the bot, which can use MCP tools"""
        try:
            # Prepare messages
            messages = [
                {
                    "role": "system", 
                    "content": f"""You are an AI assistant with access to filesystem tools via MCP (Model Context Protocol).
                    
Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

You can help users with:
- Reading and writing files
- Listing directories 
- Creating directories
- Searching for files
- Getting file information
- Managing file operations

The filesystem is mounted at /projects with these directories:
- /projects/data - Read-only data files
- /projects/mcp_data - Read-write working directory

Be helpful and explain what you're doing when using tools.
MCP Status: {'Available' if self.mcp_ready else 'Unavailable'}
"""
                },
                {"role": "user", "content": user_message}
            ]
            
            # Prepare tools if MCP is ready
            tools = self._create_openai_tools() if self.mcp_ready else None
            
            # Call OpenAI
            kwargs = {
                "model": "gpt-4",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Handle tool calls
            message = response.choices[0].message
            
            if message.tool_calls:
                # Execute tool calls
                messages.append(message)
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)  # Parse JSON properly
                    
                    print(f"🔧 Executing: {tool_name}({arguments})")
                    
                    tool_result = await self._execute_mcp_tool(tool_name, arguments)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })
                
                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                return final_response.choices[0].message.content
            else:
                return message.content
                
        except Exception as e:
            return f"Error: {e}"
    
    async def close(self):
        """Close MCP connection"""
        if self.mcp_client:
            await self.mcp_client.close()


async def test_mcp_bot():
    """Test the MCP OpenAI bot"""
    print("🤖 Testing MCP OpenAI Bot")
    print("=" * 50)
    
    bot = MCPOpenAIBot()
    
    # Initialize
    success = await bot.initialize()
    if not success:
        print("❌ Bot initialization failed")
        return
    
    # Test conversations
    test_messages = [
        "Hi! Can you list the files in /projects?",
        "Create a new file called hello.txt in /projects/mcp_data with the content 'Hello World!'",
        "Now read that file back to me",
        "Search for all .txt files in /projects/mcp_data"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n💬 Test {i}: {message}")
        response = await bot.chat(message)
        print(f"🤖 Bot: {response}")
        print("-" * 40)
    
    await bot.close()
    print("\n✅ MCP OpenAI Bot test complete!")


async def interactive_chat():
    """Interactive chat with the MCP bot"""
    print("🤖 MCP OpenAI Bot - Interactive Mode")
    print("=" * 50)
    print("Type 'quit' to exit")
    
    bot = MCPOpenAIBot()
    
    # Initialize
    success = await bot.initialize()
    if not success:
        print("❌ Bot initialization failed")
        return
    
    try:
        while True:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if not user_input:
                continue
            
            print("🤖 Bot: ", end="", flush=True)
            response = await bot.chat(user_input)
            print(response)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        await bot.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_mcp_bot())
    else:
        asyncio.run(interactive_chat())