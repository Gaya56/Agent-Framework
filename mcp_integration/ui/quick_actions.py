"""Quick action utilities for MCP tab."""
import streamlit as st
from schema import ChatMessage
from .chat_processing import process_mcp_message

def build_quick_actions(server_tools: list[str]) -> list[str]:
    """Return a list of human‑friendly quick actions based on available tools."""
    quick_actions = ["Select an action..."]
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
    return quick_actions

async def handle_quick_action(action: str, mcp_client, selected_server: str, messages: list):
    """Execute a quick action via MCP and update UI."""
    if action == "Select an action..." or not selected_server:
        return
    user_msg = ChatMessage(type="human", content=action)
    messages.append(user_msg)
    st.chat_message("human").write(action)
    try:
        ai_resp = await process_mcp_message(action, mcp_client, selected_server, messages)
        ai_msg = ChatMessage(type="ai", content=ai_resp)
        messages.append(ai_msg)
        st.chat_message("ai").write(ai_resp)
        st.rerun()
    except Exception as e:
        st.error(f"Error processing MCP request: {e}")
        st.stop()