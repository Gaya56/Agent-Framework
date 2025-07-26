"""
Centralized CSS for the MCP tab.
"""

CHAT_CSS = """
<style>
/* Main layout: two columns.  The sidebar has a fixed width. */
#mcp-main {
    display: flex;
    flex-direction: row;
    width: 100%;
    gap: 1rem;
}

/* Sidebar column */
#mcp-sidebar {
    width: 20%;
    min-width: 220px;
    max-width: 260px;
}

/* Chat area column */
#mcp-chat-area {
    width: 80%;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

/* Scrollable history container */
#mcp-history-area {
    overflow-y: auto;
    flex-grow: 1;
    padding-right: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Sticky input container */
#mcp-input-area {
    position: sticky;
    bottom: 0;
    background: var(--background-color);
    padding-top: 1rem;
    padding-bottom: 1rem;
    border-top: 1px solid var(--secondary-background-color);
}

/* Optional: adjust expander header text if you keep any expanders */
div[data-testid="stExpander"] summary {
    font-size: 1.1rem;
}
</style>
"""