"""Sidebar rendering for the MCP tab."""
import uuid
import streamlit as st

async def render_sidebar(mcp_client, st_state) -> str:
    """Build the sidebar, return selected server ID, update session."""
    with st.sidebar:
        # Accessibility and contrast tweaks
        st.markdown(
            "<style>.sidebar .st-expanderHeader{font-size:1.1em;font-weight:bold;}</style>",
            unsafe_allow_html=True,
        )
        st.subheader("🛠️ MCP Servers")
        if st.button(":material/chat: New MCP Chat", use_container_width=True):
            st_state.mcp_messages = []
            st_state.mcp_thread_id = str(uuid.uuid4())
            st.rerun()

        available = mcp_client.get_available_servers()
        if not available:
            st.error("No MCP servers available"); st.stop()

        options = {sid: f"{info['icon']} {info['name']}" for sid, info in available.items()}
        selected = st.selectbox(
            "Select MCP Server:",
            list(options.keys()),
            format_func=options.get,
            index=list(options).index(st_state.selected_mcp_server)
                  if st_state.selected_mcp_server in options else 0,
            key="mcp_server_selector")

        if selected != st_state.selected_mcp_server:
            st_state.selected_mcp_server = selected; st.rerun()

        info = available[selected]
        with st.expander(
            f"📋 {info['name']} Tools",
            expanded=True,
        ):
            st.write(f"**{info['description']}**")
            st.write(f"**{len(info['tools'])} tools available:**")
            shown = info['tools'][:8]
            for t in shown:
                desc = mcp_client.get_server_tools(selected).get(t, {}).get("description", "No description")
                st.write(f"• **{t}** – {desc}")
            if len(info['tools']) > 8:
                st.write(f"... and {len(info['tools']) - 8} more")

        with st.expander("🐳 MCP Server Status"):
            for sid, i in available.items():
                icon = "✅" if sid == selected else "⚪"
                st.write(f"{icon} {i['icon']} **{i['name']}**")

        with st.expander("💬 Conversation Tracking"):
            n = len(st_state.mcp_messages)
            st.info(f"📝 {n} messages in current conversation")
            if n:
                st.write(f"**Thread ID**: {st_state.mcp_thread_id[:8]}…")

    return selected