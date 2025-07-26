"""Session initialization helpers for MCP tab."""
import uuid
import streamlit as st
from core.multi_client import MultiMCPClient


async def init_mcp_session(st_state: st.session_state) -> MultiMCPClient:
    """Initialise session state and return MultiMCPClient."""
    if "user_id" not in st_state:
        st_state.user_id = str(uuid.uuid4())
    if "mcp_client" not in st_state:
        try:
            with st.spinner("Connecting to MCP servers..."):
                st_state.mcp_client = MultiMCPClient()
                await st_state.mcp_client.initialize()
        except Exception as e:
            st.error(f"Error connecting to MCP servers: {e}")
            st.markdown("Make sure the MCP containers are running.")
            st.stop()
    mcp_client = st_state.mcp_client
    st_state.setdefault("mcp_messages", [])
    st_state.setdefault("mcp_thread_id", str(uuid.uuid4()))
    if "selected_mcp_server" not in st_state:
        servers = mcp_client.get_available_servers()
        st_state.selected_mcp_server = list(servers)[0] if servers else None
    return mcp_client