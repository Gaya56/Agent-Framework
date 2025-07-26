"""Message rendering helpers for MCP tab."""
from collections.abc import AsyncGenerator
import streamlit as st
from schema import ChatMessage

async def amessage_iter(messages: list[ChatMessage]) -> AsyncGenerator[ChatMessage, None]:
    """Yield ChatMessage items asynchronously."""
    for m in messages:
        yield m

async def draw_mcp_messages(messages_agen: AsyncGenerator[ChatMessage, None]) -> None:
    """Render messages from an async generator."""
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