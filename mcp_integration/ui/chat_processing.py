"""Process user messages via MCP/OpenAI."""
import streamlit as st
from core.multi_client import MultiMCPClient
from typing import Optional
from schema import ChatMessage

async def process_mcp_message(
    user_input: str,
    mcp_client: MultiMCPClient,
    selected_server: str,
    conversation_history: Optional[list[ChatMessage]] = None,
) -> str:
    """Process input with persistent MCPOpenAIBot and conversation context."""
    from core.mcp_openai_bot import MCPOpenAIBot  # avoid circular import
    try:
        bot_key = f"mcp_bot_{selected_server}"
        if bot_key not in st.session_state or st.session_state[bot_key] is None:
            st.session_state[bot_key] = MCPOpenAIBot(selected_server, mcp_client)
            await st.session_state[bot_key].initialize()
        bot = st.session_state[bot_key]
        # Build conversation context
        history = (
            "\n".join(
                f"{'User' if msg.type=='human' else 'Assistant'}: {msg.content}"
                for msg in (conversation_history or [])[-20:]
            )
        )
        server_info = mcp_client.get_available_servers().get(selected_server, {})
        server_ctx = f"You are working with {server_info.get('name','MCP Server')} ({selected_server}). "
        full_input = f"{server_ctx}{history}\nCurrent request: {user_input}"
        return await bot.chat(full_input)
    except Exception as e:
        return f"Sorry, I encountered an error processing your request: {e}"