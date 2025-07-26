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
    
    # Retrieve existing messages for display
    messages: list[ChatMessage] = st.session_state.mcp_messages

    # CSS injected to make history scrollable and input sticky
    st.markdown(
        """
        <style>
        #mcp-history-area {
            overflow-y: auto;
            height: calc(100vh - 18rem);
            padding-right: 0.5rem;
        }
        #mcp-input-area {
            position: sticky;
            bottom: 0;
            background: var(--background-color);
            padding-top: 1rem;
            padding-bottom: 1rem;
            border-top: 1px solid var(--secondary-background-color);
        }
        div[data-testid="stExpander"] summary {
            font-size: 1.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Containers to isolate scrollable history and sticky input areas
    history_area = st.container()
    input_area = st.container()

    # History container wrapped in an expander
    with history_area:
        with st.expander("Conversation history", expanded=True):
            st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
            await draw_mcp_messages(amessage_iter(messages))
            st.markdown("</div>", unsafe_allow_html=True)

    # Input container with quick actions and chat box
    with input_area:
        st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)
        st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
        server_tools = current_server_info.get("tools", [])
        quick_actions = [(action, action) for action in build_quick_actions(server_tools)]
        col1, col2 = st.columns([3, 1])
        with col1:
            quick_action = st.selectbox(
                "Choose an action:",
                quick_actions,
                format_func=lambda x: x[0],
                key="mcp_quick_action",
            )
        with col2:
            if st.button("Execute", use_container_width=True, type="primary"):
                with st.spinner("Processing…"):
                    await handle_quick_action(
                        quick_action[1],
                        mcp_client,
                        st.session_state.selected_mcp_server,
                        messages,
                    )
        # Chat input remains the same but lives inside the sticky container
        if user_input := st.chat_input("Type your request..."):
            if st.session_state.selected_mcp_server:
                user_message = ChatMessage(type="human", content=user_input)
                messages.append(user_message)
                st.chat_message("human").write(user_input)
                try:
                    with st.spinner("Processing…"):
                        ai_response = await process_mcp_message(
                            user_input,
                            mcp_client,
                            st.session_state.selected_mcp_server,
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
        st.markdown("</div>", unsafe_allow_html=True)