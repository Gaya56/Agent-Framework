"""Message rendering helpers for MCP tab."""
from collections.abc import AsyncGenerator
import streamlit as st
from schema import ChatMessage
from datetime import datetime

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
                ts = datetime.now().strftime("%H:%M")
                st.chat_message("human").write(f"{msg.content} ({ts})")
            case "ai":
                ts = datetime.now().strftime("%H:%M")
                st.chat_message("ai").write(f"{msg.content} ({ts})")
            case _:
                st.error(f"Unexpected ChatMessage type: {msg.type}")