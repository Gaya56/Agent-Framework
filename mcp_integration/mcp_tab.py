"""
MCP Tab for Streamlit UI - uses the multi-server MCP client
Handles MCP server interactions with server selection interface
"""
import asyncio
import sys
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import streamlit as st

# Import from the new multi-server MCP client
from multi_mcp_client import MultiMCPClient

# Import schema from the main src directory
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
from schema import ChatMessage


async def render_mcp_tab() -> None:
    """Render MCP tab with multi-server selection interface"""
    
    # Get or create user ID (following streamlit_app.py pattern)
    user_id = st.session_state.get("user_id", str(uuid.uuid4()))
    
    # Initialize Multi-MCP client (like AgentClient initialization)
    if "mcp_client" not in st.session_state:
        try:
            with st.spinner("Connecting to MCP servers..."):
                st.session_state.mcp_client = MultiMCPClient()
                await st.session_state.mcp_client.initialize()
        except Exception as e:
            st.error(f"Error connecting to MCP servers: {e}")
            st.markdown("Make sure the MCP containers are running.")
            st.stop()
    
    mcp_client: MultiMCPClient = st.session_state.mcp_client
    
    # Initialize MCP messages and selected server (following streamlit_app.py pattern)
    if "mcp_messages" not in st.session_state:
        st.session_state.mcp_messages = []
        
    if "mcp_thread_id" not in st.session_state:
        st.session_state.mcp_thread_id = str(uuid.uuid4())
    
    if "selected_mcp_server" not in st.session_state:
        # Set default to first available server
        available_servers = mcp_client.get_available_servers()
        if available_servers:
            st.session_state.selected_mcp_server = list(available_servers.keys())[0]
        else:
            st.session_state.selected_mcp_server = None

    # MCP Tab sidebar configuration (following streamlit_app.py pattern)
    with st.sidebar:
        st.subheader("🛠️ MCP Servers")
        
        if st.button(":material/chat: New MCP Chat", use_container_width=True):
            st.session_state.mcp_messages = []
            st.session_state.mcp_thread_id = str(uuid.uuid4())
            st.rerun()

        # Server Selection
        available_servers = mcp_client.get_available_servers()
        if available_servers:
            server_options = {
                server_id: f"{info['icon']} {info['name']}"
                for server_id, info in available_servers.items()
            }
            
            selected_server = st.selectbox(
                "Select MCP Server:",
                options=list(server_options.keys()),
                format_func=lambda x: server_options[x],
                index=list(server_options.keys()).index(st.session_state.selected_mcp_server) 
                      if st.session_state.selected_mcp_server in server_options else 0,
                key="mcp_server_selector"
            )
            
            # Update selected server
            if selected_server != st.session_state.selected_mcp_server:
                st.session_state.selected_mcp_server = selected_server
                st.rerun()
            
            # Show server info
            server_info = available_servers[selected_server]
            with st.expander(f"📋 {server_info['name']} Tools", expanded=True):
                st.write(f"**{server_info['description']}**")
                st.write(f"**{len(server_info['tools'])} tools available:**")
                for tool_name in server_info['tools'][:8]:  # Show first 8 tools
                    # Get tool description from server
                    tool_details = mcp_client.get_server_tools(selected_server)
                    tool_desc = tool_details.get(tool_name, {}).get('description', 'No description')
                    st.write(f"• **{tool_name}**: {tool_desc}")
                if len(server_info['tools']) > 8:
                    st.write(f"... and {len(server_info['tools']) - 8} more tools")
        else:
            st.error("No MCP servers available")
            st.stop()

        with st.expander("🐳 MCP Server Status"):
            for server_id, info in available_servers.items():
                status_icon = "✅" if server_id == selected_server else "⚪"
                st.write(f"{status_icon} {info['icon']} **{info['name']}**")
                if server_id == selected_server:
                    st.write(f"   *{info['description']}*")
            
        with st.expander("💬 Conversation Tracking"):
            message_count = len(st.session_state.mcp_messages)
            st.info(f"📝 {message_count} messages in current conversation")
            st.write("**Context**: Last 6 messages sent to AI")
            if message_count > 0:
                st.write(f"**Thread ID**: {st.session_state.mcp_thread_id[:8]}...")

    # Main content area
    current_server_info = available_servers.get(st.session_state.selected_mcp_server or "", {})
    
    # Draw existing MCP messages (following streamlit_app.py pattern)
    messages: list[ChatMessage] = st.session_state.mcp_messages

    # Display existing messages (following streamlit_app.py pattern)
    async def amessage_iter() -> AsyncGenerator[ChatMessage, None]:
        for m in messages:
            yield m

    await draw_mcp_messages(amessage_iter())

    # Quick action selector
    st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
    
    # Create dynamic quick actions based on available tools
    server_tools = current_server_info.get('tools', [])
    quick_actions = ["Select an action..."]
    
    # Add filesystem actions
    if "list_directory" in server_tools:
        quick_actions.append("List the contents of the directory")
    if "create_directory" in server_tools:
        quick_actions.append("Create a new directory")
    if "read_file" in server_tools:
        quick_actions.append("Read a file")
    if "write_file" in server_tools:
        quick_actions.append("Write to a file")
    if "move_file" in server_tools:
        quick_actions.append("Move or rename a file")
    if "get_file_info" in server_tools:
        quick_actions.append("Get file information")
    if "search_files" in server_tools:
        quick_actions.append("Search for a specific file")
    
    # Add Brave Search actions
    if "brave_web_search" in server_tools:
        quick_actions.append("Search the web")
    if "brave_image_search" in server_tools:
        quick_actions.append("Search for images")
    if "brave_video_search" in server_tools:
        quick_actions.append("Search for videos")
    if "brave_news_search" in server_tools:
        quick_actions.append("Search for news")
    if "brave_local_search" in server_tools:
        quick_actions.append("Search for local businesses")
    
    # Add GitHub actions
    if "create_or_update_file" in server_tools:
        quick_actions.append("Create or update a file in a repository")
    if "push_files" in server_tools:
        quick_actions.append("Push multiple files to a repository")
    if "search_repositories" in server_tools:
        quick_actions.append("Search GitHub repositories")
    if "create_issue" in server_tools:
        quick_actions.append("Create a new issue")
    if "create_pull_request" in server_tools:
        quick_actions.append("Open a pull request")
    if "list_issues" in server_tools:
        quick_actions.append("List repository issues")
    if "get_file_contents" in server_tools:
        quick_actions.append("Get contents of a file from repository")
    if "create_repository" in server_tools:
        quick_actions.append("Create a new repository")
    if "fork_repository" in server_tools:
        quick_actions.append("Fork a repository")
    if "create_branch" in server_tools:
        quick_actions.append("Create a new branch")
    
    # Create columns for better layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        quick_action = st.selectbox(
            "Choose an action:",
            quick_actions,
            key="mcp_quick_action"
        )
    
    with col2:
        if st.button("Execute", use_container_width=True, type="primary"):
            if quick_action != "Select an action..." and st.session_state.selected_mcp_server:
                # Add the selected action as user message
                user_message = ChatMessage(type="human", content=quick_action)
                messages.append(user_message)
                st.chat_message("human").write(quick_action)
                
                try:
                    # Process with MCP (simplified - no streaming for now)
                    ai_response = await process_mcp_message(
                        quick_action, 
                        mcp_client, 
                        st.session_state.selected_mcp_server,
                        messages
                    )
                    
                    # Add AI response
                    ai_message = ChatMessage(type="ai", content=ai_response)
                    messages.append(ai_message)
                    st.chat_message("ai").write(ai_response)
                    
                    st.rerun()  # Clear stale containers like streamlit_app.py
                    
                except Exception as e:
                    st.error(f"Error processing MCP request: {e}")
                    st.stop()

    # Handle new user input (following streamlit_app.py pattern)
    if user_input := st.chat_input("Type your request..."):
        if st.session_state.selected_mcp_server:
            # Add user message
            user_message = ChatMessage(type="human", content=user_input)
            messages.append(user_message)
            st.chat_message("human").write(user_input)
            
            try:
                # Process with MCP (simplified - no streaming for now)
                ai_response = await process_mcp_message(
                    user_input, 
                    mcp_client, 
                    st.session_state.selected_mcp_server,
                    messages
                )
                
                # Add AI response
                ai_message = ChatMessage(type="ai", content=ai_response)
                messages.append(ai_message)
                st.chat_message("ai").write(ai_response)
                
                st.rerun()  # Clear stale containers like streamlit_app.py
                
            except Exception as e:
                st.error(f"Error processing MCP request: {e}")
                st.stop()
        else:
            st.error("Please select an MCP server first!")


async def draw_mcp_messages(
    messages_agen: AsyncGenerator[ChatMessage, None],
) -> None:
    """Draw MCP messages - simplified version of streamlit_app.py draw_messages"""
    
    # Iterate over messages and draw them (following streamlit_app.py pattern)
    while msg := await anext(messages_agen, None):
        if not isinstance(msg, ChatMessage):
            st.error(f"Unexpected message type: {type(msg)}")
            continue
            
        match msg.type:
            case "human":
                st.chat_message("human").write(msg.content)
            case "ai":
                st.chat_message("ai").write(msg.content)
            case _:
                st.error(f"Unexpected ChatMessage type: {msg.type}")


async def process_mcp_message(user_input: str, mcp_client: MultiMCPClient, selected_server: str, conversation_history: list[ChatMessage] | None = None) -> str:
    """Process user message with MCP tools via OpenAI with conversation context"""
    
    # Import the OpenAI bot here to avoid circular imports
    from mcp_openai_bot_v2 import MCPOpenAIBot
    
    try:
        # Get or create persistent bot instance for the selected server
        bot_key = f"mcp_bot_{selected_server}"
        if bot_key not in st.session_state or st.session_state[bot_key] is None:
            # Create a new bot instance for this server, using the persistent MCP client
            st.session_state[bot_key] = MCPOpenAIBot(selected_server, mcp_client)
            await st.session_state[bot_key].initialize()
        
        bot: MCPOpenAIBot = st.session_state[bot_key]
        
        # Build conversation context if provided
        if conversation_history:
            # Convert ChatMessage history to OpenAI format
            conversation_context = ""
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                if msg.type == "human":
                    conversation_context += f"User: {msg.content}\n"
                elif msg.type == "ai":
                    conversation_context += f"Assistant: {msg.content}\n"
            
            # Add context to the current message
            if conversation_context:
                contextual_input = f"Previous conversation:\n{conversation_context}\nCurrent request: {user_input}"
            else:
                contextual_input = user_input
        else:
            contextual_input = user_input
        
        # Add server context to the message
        server_info = mcp_client.get_available_servers().get(selected_server, {})
        server_context = f"You are working with {server_info.get('name', 'MCP Server')} ({selected_server}). "
        full_input = server_context + contextual_input
        
        # Use the persistent OpenAI bot to process the message with context
        response = await bot.chat(full_input)
        
        # DO NOT close the bot - keep it persistent for future requests
        # await bot.close()  # <-- Removed this line
        
        return response
        
    except Exception as e:
        return f"Sorry, I encountered an error processing your request: {str(e)}"