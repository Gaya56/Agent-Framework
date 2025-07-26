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
from .css_styles import CHAT_CSS


async def render_mcp_tab() -> None:
    """Render MCP tab with multi-server selection interface"""
    
    # Initialise session and get MCP client from helper
    from .session_utils import init_mcp_session
    mcp_client = await init_mcp_session(st.session_state)
    
    # Retrieve existing messages for display
    messages: list[ChatMessage] = st.session_state.mcp_messages

    # Inject centralized CSS for layout, scroll and sticky behaviour.
    st.markdown(CHAT_CSS, unsafe_allow_html=True)

    # Build the two-column layout using HTML divs for styling hooks
    st.markdown("<div id='mcp-main'>", unsafe_allow_html=True)

    # --- Sidebar column for server and tool selection ---
    st.markdown("<div id='mcp-sidebar'>", unsafe_allow_html=True)
    # Server selection (radio or selectbox)
    available_servers = mcp_client.get_available_servers()
    server_names = list(available_servers.keys())
    # Use st.radio so only one server can be selected at a time
    selected_server = st.radio(
        "Select MCP Server",
        server_names,
        index=0 if server_names else 0,
        key="mcp_server_radio",
    )
    current_server_info = available_servers.get(selected_server or "", {})
    # Tool selection checkboxes
    server_tools = current_server_info.get("tools", [])
    selected_tools = []
    st.markdown("**Available Tools:**")
    for tool in server_tools:
        if st.checkbox(tool, key=f"tool_{tool}"):
            selected_tools.append(tool)
    st.markdown("</div>", unsafe_allow_html=True)  # close sidebar

    # --- Chat area column ---
    st.markdown("<div id='mcp-chat-area'>", unsafe_allow_html=True)
    # Scrollable history
    st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
    await draw_mcp_messages(amessage_iter(messages))
    st.markdown("</div>", unsafe_allow_html=True)
    # Sticky input area
    st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)
    # Optional: quick actions based on selected tools; can be buttons or a selectbox
    if selected_tools:
        st.subheader("Quick Actions")
        quick_actions = [(action, action) for action in build_quick_actions(selected_tools)]
        action_choice = st.selectbox(
            "Choose an action",
            options=quick_actions,
            format_func=lambda x: x[0],
            key="mcp_action_choice",
        )
        if st.button("Execute", key="mcp_execute_action"):
            with st.spinner("Processing…"):
                await handle_quick_action(
                    action_choice[1],
                    mcp_client,
                    selected_server,
                    messages,
                )
    # Chat input tied to the selected server
    if user_input := st.chat_input("Type your request..."):
        if selected_server:
            user_message = ChatMessage(type="human", content=user_input)
            messages.append(user_message)
            st.chat_message("human").write(user_input)
            try:
                with st.spinner("Processing…"):
                    ai_response = await process_mcp_message(
                        user_input,
                        mcp_client,
                        selected_server,
                        messages,
                    )
                ai_message = ChatMessage(type="ai", content=ai_response)
                messages.append(ai_message)
                st.chat_message("ai").write(ai_response)
                st.rerun()
            except Exception as e:
                st.error(f"Error processing MCP request: {e}")
                st.stop()
        else:
            st.error("Please select an MCP server first!")
    st.markdown("</div>", unsafe_allow_html=True)  # close input area
    st.markdown("</div>", unsafe_allow_html=True)  # close chat column
    st.markdown("</div>", unsafe_allow_html=True)  # close main flex wrapper