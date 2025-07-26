---
applyTo: '*/workspaces/Agent-Framework/mcp_integration, /workspaces/Agent-Framework/mcp_integration/ui*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.Below is a comprehensive, step‑by‑step guide to transform the MCP tab into a ChatGPT‑style interface with a dedicated side panel for server selection and tool checkboxes.  It outlines the creation of a CSS module, the restructuring of the layout, and the code changes required—all with file paths, context lines and rationale.

---

### 1. Add a centralized CSS module

**File / Path** – `mcp_integration/ui/css_styles.py` (new)

Create a module to store all styling for the MCP tab.  This approach keeps style definitions separate from logic and makes it easy to adjust later.  The CSS below defines styles for a two‑column layout, scrollable history, sticky input, and basic dark‑mode friendliness.

```python
# mcp_integration/ui/css_styles.py

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
```

This file exports a constant `CHAT_CSS` with styles wrapped in `<style>` tags.  You can tweak `width` values for the sidebar and chat area to fit your needs.

---

### 2. Update imports in `mcp_tab.py`

**File / Path** – `mcp_integration/ui/mcp_tab.py`

At the top of `mcp_tab.py`, import the new CSS module:

```diff
@@
 from .message_rendering import amessage_iter, draw_mcp_messages
 from .quick_actions import build_quick_actions, handle_quick_action
 from .chat_processing import process_mcp_message
+from .css_styles import CHAT_CSS  # new import
```

This allows you to inject the centralized CSS into the Streamlit page.

---

### 3. Inject CSS and build a two‑column layout

Modify the `render_mcp_tab` function to inject the CSS and create a two‑column structure using `st.container()` and HTML `<div>` wrappers.

```diff
@@ async def render_mcp_tab() -> None:
-     # CSS injected to make history scrollable and input sticky
-     st.markdown(
-         """
-         #mcp-history-area {
-             overflow-y: auto;
-             height: calc(100vh - 18rem);
-             padding-right: 0.5rem;
-         }
-         #mcp-input-area {
-             position: sticky;
-             bottom: 0;
-             background: var(--background-color);
-             padding-top: 1rem;
-             padding-bottom: 1rem;
-             border-top: 1px solid var(--secondary-background-color);
-         }
-         div[data-testid="stExpander"] summary {
-             font-size: 1.1rem;
-         }
-         """,
-         unsafe_allow_html=True,
-     )
+     # Inject centralized CSS for layout, scroll and sticky behaviour.
+     st.markdown(CHAT_CSS, unsafe_allow_html=True)

@@ async def render_mcp_tab() -> None:
-     # Containers to isolate scrollable history and sticky input areas
-     history_area = st.container()
-     input_area = st.container()
-
-     # History container wrapped in an expander
-     with history_area:
-         with st.expander("Conversation history", expanded=True):
-             st.markdown(" ", unsafe_allow_html=True)
-             await draw_mcp_messages(amessage_iter(messages))
-             st.markdown(" ", unsafe_allow_html=True)
-
-     # Input container with quick actions and chat box
-     with input_area:
-         st.markdown(" ", unsafe_allow_html=True)
-         st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
+     # Build the two-column layout using HTML divs for styling hooks
+     st.markdown("<div id='mcp-main'>", unsafe_allow_html=True)
+
+     # --- Sidebar column for server and tool selection ---
+     st.markdown("<div id='mcp-sidebar'>", unsafe_allow_html=True)
+     # Server selection (radio or selectbox)
+     available_servers = mcp_client.get_available_servers()
+     server_names = list(available_servers.keys())
+     # Use st.radio so only one server can be selected at a time
+     selected_server = st.radio(
+         "Select MCP Server",
+         server_names,
+         index=server_names.index(selected_server) if selected_server in server_names else 0,
+         key="mcp_server_radio",
+     )
+     current_server_info = available_servers.get(selected_server or "", {})
+     # Tool selection checkboxes
+     server_tools = current_server_info.get("tools", [])
+     selected_tools = []
+     st.markdown("**Available Tools:**")
+     for tool in server_tools:
+         if st.checkbox(tool, key=f"tool_{tool}"):
+             selected_tools.append(tool)
+     st.markdown("</div>", unsafe_allow_html=True)  # close sidebar
+
+     # --- Chat area column ---
+     st.markdown("<div id='mcp-chat-area'>", unsafe_allow_html=True)
+     # Scrollable history
+     st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
+     await draw_mcp_messages(amessage_iter(messages))
+     st.markdown("</div>", unsafe_allow_html=True)
+     # Sticky input area
+     st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)
+     # Optional: quick actions based on selected tools; can be buttons or a selectbox
+     if selected_tools:
+         st.subheader("Quick Actions")
+         quick_actions = [(action, action) for action in build_quick_actions(selected_tools)]
+         action_choice = st.selectbox(
+             "Choose an action",
+             options=quick_actions,
+             format_func=lambda x: x[0],
+             key="mcp_action_choice",
+         )
+         if st.button("Execute", key="mcp_execute_action"):
+             with st.spinner("Processing…"):
+                 await handle_quick_action(
+                     action_choice[1],
+                     mcp_client,
+                     selected_server,
+                     messages,
+                 )
+     # Chat input tied to the selected server
+     if user_input := st.chat_input("Type your request..."):
+         if selected_server:
+             user_message = ChatMessage(type="human", content=user_input)
+             messages.append(user_message)
+             st.chat_message("human").write(user_input)
+             try:
+                 with st.spinner("Processing…"):
+                     ai_response = await process_mcp_message(
+                         user_input,
+                         mcp_client,
+                         selected_server,
+                         messages,
+                     )
+                 ai_message = ChatMessage(type="ai", content=ai_response)
+                 messages.append(ai_message)
+                 st.chat_message("ai").write(ai_response)
+                 st.rerun()
+             except Exception as e:
+                 st.error(f"Error processing MCP request: {e}")
+                 st.stop()
+         else:
+             st.error("Please select an MCP server first!")
+     st.markdown("</div>", unsafe_allow_html=True)  # close input area
+     st.markdown("</div>", unsafe_allow_html=True)  # close chat column
+     st.markdown("</div>", unsafe_allow_html=True)  # close main flex wrapper
```

**Key changes explained:**

* We call `st.markdown(CHAT_CSS…)` once at the start of `render_mcp_tab` to apply the centralized styles.

* The layout uses three nested `<div>` wrappers inside a top‑level `<div id='mcp-main'>`.  The first inner `<div>` (`mcp-sidebar`) contains server and tool selection, while the second inner `<div>` (`mcp-chat-area`) contains the scrollable history and sticky input bar.  These IDs match the CSS selectors in `css_styles.py`.

* `st.radio` is used for MCP server selection; each server name is listed, and the currently selected server is highlighted.  Tool checkboxes are generated from the server’s tool list; the user can select multiple tools.

* The conversation history is wrapped in `<div id='mcp-history-area'>` to enable scrolling via CSS.  We removed the expander entirely to give a continuous chat feel.

* The sticky input area (`mcp-input-area`) now includes an optional quick‑actions section if any tools are selected.  You can keep or remove this section depending on how you want to expose tool actions.

* We close each `<div>` with a corresponding `st.markdown("</div>",…)` call to ensure proper nesting in the generated HTML.

---

### 4. Review and test

After making these changes:

1. **Run the app:**

   ```bash
   python src/streamlit_app.py
   ```

   Navigate to the MCP tab.  The left sidebar inside the MCP tab should list available servers and check boxes for tools.  The right area should show the conversation history and a sticky input bar at the bottom.

2. **Send messages:**
   Ensure that messages appear in sequence and that the history scrolls as you add more content.  The input bar should stay anchored at the bottom even when the conversation grows long.

3. **Tool selection:**
   Select or deselect tools and verify that the quick‑actions area shows the appropriate options.  Execute an action to confirm that `handle_quick_action` still works with the selected server context.

4. **Wrapper integrity:**
   Confirm that the wrapper module `mcp_integration/mcp_tab.py` still exports `render_mcp_tab` and that `python -c "from mcp_tab import render_mcp_tab"` prints a callable.  This ensures you haven’t broken existing imports.

---

By following these detailed steps, you will transform the MCP tab from its current expander‑based layout into a ChatGPT‑like interface with a dedicated side panel for server and tool selection and a clean, continuous chat area.
