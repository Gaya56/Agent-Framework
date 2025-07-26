---
applyTo: '*/workspaces/Agent-Framework/mcp_integration*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.## Overview

The current MCP tab implementation displays the conversation in a single `st.expander` and places quick actions and the chat input sequentially afterward. This causes the page to jump when new messages are added and leaves the input bar at the bottom of the conversation rather than the viewport. We need to restructure the UI to separate the conversation into a scrollable container and fix the input bar at the bottom. The wrapper module (`mcp_integration/mcp_tab.py`) re‑exports `render_mcp_tab` and should remain untouched.

## Detailed Changes

### Modify `render_mcp_tab` to introduce containers and styling

In `mcp_integration/ui/mcp_tab.py`, we replace the single expander and sequential elements with a scrollable history container (`history_area`) and a sticky input container (`input_area`). We also inject CSS to control these areas. The unified diff below shows the exact code modifications:

```diff
@@ async def render_mcp_tab() -> None:
-     # Draw existing MCP messages (following streamlit_app.py pattern)
-     messages: list[ChatMessage] = st.session_state.mcp_messages
-
-     # Display existing messages inside collapsible panel
-     with st.expander("Conversation history", expanded=True):
-         await draw_mcp_messages(amessage_iter(messages))
-
-     # Quick action selector
-     st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
-     
-     # Create dynamic quick actions based on available tools using helper
-     server_tools = current_server_info.get("tools", [])
-     quick_actions = [(action, action) for action in build_quick_actions(server_tools)]
-     
-     # Create columns for better layout
-     col1, col2 = st.columns([3, 1])
-     
-     with col1:
-         quick_action = st.selectbox(
-             "Choose an action:",
-             quick_actions,
-             format_func=lambda x: x[0],
-             key="mcp_quick_action",
-         )
-     
-     with col2:
-         if st.button("Execute", use_container_width=True, type="primary"):
-             with st.spinner("Processing…"):
-                 await handle_quick_action(
-                     quick_action[1],
-                     mcp_client,
-                     st.session_state.selected_mcp_server,
-                     messages,
-                 )
-
-     # Handle new user input (following streamlit_app.py pattern)
-     if user_input := st.chat_input("Type your request..."):
-         if st.session_state.selected_mcp_server:
-             ...
-         else:
-             st.error("Please select an MCP server first!")
+     # Retrieve existing messages for display
+     messages: list[ChatMessage] = st.session_state.mcp_messages
+
+     # CSS injected to make history scrollable and input sticky
+     st.markdown(
+         """
+         <style>
+         #mcp-history-area {
+             overflow-y: auto;
+             height: calc(100vh - 18rem);
+             padding-right: 0.5rem;
+         }
+         #mcp-input-area {
+             position: sticky;
+             bottom: 0;
+             background: var(--background-color);
+             padding-top: 1rem;
+             padding-bottom: 1rem;
+             border-top: 1px solid var(--secondary-background-color);
+         }
+         div[data-testid="stExpander"] summary {
+             font-size: 1.1rem;
+         }
+         </style>
+         """,
+         unsafe_allow_html=True,
+     )
+
+     # Containers to isolate scrollable history and sticky input areas
+     history_area = st.container()
+     input_area = st.container()
+
+     # History container wrapped in an expander
+     with history_area:
+         with st.expander("Conversation history", expanded=True):
+             st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
+             await draw_mcp_messages(amessage_iter(messages))
+             st.markdown("</div>", unsafe_allow_html=True)
+
+     # Input container with quick actions and chat box
+     with input_area:
+         st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)
+         st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
+         server_tools = current_server_info.get("tools", [])
+         quick_actions = [(action, action) for action in build_quick_actions(server_tools)]
+         col1, col2 = st.columns([3, 1])
+         with col1:
+             quick_action = st.selectbox(
+                 "Choose an action:",
+                 quick_actions,
+                 format_func=lambda x: x[0],
+                 key="mcp_quick_action",
+             )
+         with col2:
+             if st.button("Execute", use_container_width=True, type="primary"):
+                 with st.spinner("Processing…"):
+                     await handle_quick_action(
+                         quick_action[1],
+                         mcp_client,
+                         st.session_state.selected_mcp_server,
+                         messages,
+                     )
+         # Chat input remains the same but lives inside the sticky container
+         if user_input := st.chat_input("Type your request..."):
+             if st.session_state.selected_mcp_server:
+                 user_message = ChatMessage(type="human", content=user_input)
+                 messages.append(user_message)
+                 st.chat_message("human").write(user_input)
+                 try:
+                     with st.spinner("Processing…"):
+                         ai_response = await process_mcp_message(
+                             user_input,
+                             mcp_client,
+                             st.session_state.selected_mcp_server,
+                             messages,
+                         )
+                     ai_message = ChatMessage(type="ai", content=ai_response)
+                     messages.append(ai_message)
+                     st.chat_message("ai").write(ai_response)
+                     st.rerun()
+                 except Exception as e:
+                     st.error(f"Error processing MCP request: {e}")
+                     st.stop()
+             else:
+                 st.error("Please select an MCP server first!")
+         st.markdown("</div>", unsafe_allow_html=True)
```

**Context & Rationale:**

* Lines 38–44 of the original file show messages drawn directly inside a single expander. We move this into a container (`history_area`) and wrap the content with a `<div id='mcp-history-area'>` so that CSS can control its height and overflow.
* Lines 45–71 originally handle quick actions and lines 73–96 handle chat input sequentially. We encapsulate these in another container (`input_area`) and a `<div id='mcp-input-area'>` so CSS can pin it to the bottom.
* The injected `<style>` block defines `#mcp-history-area` as scrollable and `#mcp-input-area` as sticky. It also increases expander header font size to maintain accessibility.
* We reuse existing logic for quick actions, message processing, and `st.rerun()` to avoid altering async flows or business logic.

## Checklist

* [ ] Edit `mcp_integration/ui/mcp_tab.py` as shown above.
* [ ] Add CSS for scrollable history and sticky input to maintain user focus.
* [ ] Retain the wrapper import (`from mcp_tab import render_mcp_tab`) to ensure compatibility.
* [ ] Ensure no other files are modified.
