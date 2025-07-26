# mcp_integration/mcp_tab.py
"""
Wrapper module to preserve compatibility with existing imports.
This ensures that streamlit_app.py can continue using 'from mcp_tab import render_mcp_tab'
"""

from ui.mcp_tab import render_mcp_tab, draw_mcp_messages, process_mcp_message

__all__ = ["render_mcp_tab", "draw_mcp_messages", "process_mcp_message"]
