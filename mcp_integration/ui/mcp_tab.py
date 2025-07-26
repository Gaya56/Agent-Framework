"""
MCP Tab for Streamlit UI - uses the multi-server MCP client
Handles MCP server interactions with server selection interface
"""
import sys
from pathlib import Path

import streamlit as st

# Import from the new multi-server MCP client
from core.multi_client import MultiMCPClient

# Import schema from the main src directory
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
from schema import ChatMessage

# Import message rendering helpers
from .message_rendering import amessage_iter, draw_mcp_messages
from .quick_actions import build_quick_actions, handle_quick_action
from .chat_processing import process_mcp_message


async def render_mcp_tab() -> None:
    """Render MCP tab with multi-server selection interface"""
    
    # Initialise session and get MCP client from helper
    from .session_utils import init_mcp_session
    mcp_client = await init_mcp_session(st.session_state)

    # Render sidebar via helper and get selected server
    from .sidebar import render_sidebar
    selected_server = await render_sidebar(mcp_client, st.session_state)
    
    # Main content area
    available_servers = mcp_client.get_available_servers()
    current_server_info = available_servers.get(selected_server or "", {})
    
    # Draw existing MCP messages (following streamlit_app.py pattern)
    messages: list[ChatMessage] = st.session_state.mcp_messages

    # Display existing messages using helper
    await draw_mcp_messages(amessage_iter(messages))

    # Quick action selector
    st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
    
    # Create dynamic quick actions based on available tools using helper
    server_tools = current_server_info.get("tools", [])
    quick_actions = build_quick_actions(server_tools)
    
    # Create columns for better layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        quick_action = st.selectbox(
            "Choose an action:",
            quick_actions,
            key="mcp_quick_action",
        )
    
    with col2:
        if st.button("Execute", use_container_width=True, type="primary"):
            await handle_quick_action(
                quick_action,
                mcp_client,
                st.session_state.selected_mcp_server,
                messages,
            )

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