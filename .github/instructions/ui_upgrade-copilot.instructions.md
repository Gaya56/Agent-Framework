---
applyTo: '*/workspaces/Agent-Framework/mcp_integration, /workspaces/Agent-Framework/mcp_integration/ui*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.### 1. Show loading spinner for tool calls

Adding a spinner gives users visual feedback during potentially slow tool execution. In `ui/mcp_tab.py`, the “Execute” button triggers `handle_quick_action()`, and user‑input calls `process_mcp_message()`. By wrapping each call in `with st.spinner("Processing…")`, we keep the asynchronous `await` pattern intact while Streamlit displays a spinner during execution. Imports and function signatures remain unchanged.

```diff
@@ async def render_mcp_tab() -> None:
-    with col2:
-        if st.button("Execute", use_container_width=True, type="primary"):
-            await handle_quick_action(
-                quick_action,
-                mcp_client,
-                st.session_state.selected_mcp_server,
-                messages,
-            )
+    with col2:
+        if st.button("Execute", use_container_width=True, type="primary"):
+            with st.spinner("Processing…"):
+                await handle_quick_action(
+                    quick_action,
+                    mcp_client,
+                    st.session_state.selected_mcp_server,
+                    messages,
+                )
@@ if user_input := st.chat_input("Type your request..."):
-                ai_response = await process_mcp_message(
-                    user_input,
-                    mcp_client,
-                    st.session_state.selected_mcp_server,
-                    messages
-                )
+                with st.spinner("Processing…"):
+                    ai_response = await process_mcp_message(
+                        user_input,
+                        mcp_client,
+                        st.session_state.selected_mcp_server,
+                        messages
+                    )
```

Validation: after this change, run `python -m pylint mcp_integration`, then `python src/streamlit_app.py` to see spinners while tools run, and ensure `from mcp_tab import render_mcp_tab` still resolves.

### 2. Organize quick actions with icons

Currently the quick‑action selector uses plain strings. To support icons or labels separately from action keys, convert the list returned by `build_quick_actions()` into tuples `(label, value)`. Use the `format_func` argument of `st.selectbox()` to display the first element while storing the second. Update the call to `handle_quick_action()` to pass the selected value. This keeps the existing helper functions and imports intact.

```diff
@@ async def render_mcp_tab() -> None:
-    quick_actions = build_quick_actions(server_tools)
+    quick_actions = [(action, action) for action in build_quick_actions(server_tools)]
@@
-    with col1:
-        quick_action = st.selectbox(
-            "Choose an action:",
-            quick_actions,
-            key="mcp_quick_action",
-        )
+    with col1:
+        quick_action = st.selectbox(
+            "Choose an action:",
+            quick_actions,
+            format_func=lambda x: x[0],
+            key="mcp_quick_action",
+        )
@@
-    if st.button("Execute", use_container_width=True, type="primary"):
-            await handle_quick_action(
-                quick_action,
-                mcp_client,
-                st.session_state.selected_mcp_server,
-                messages,
-            )
+    if st.button("Execute", use_container_width=True, type="primary"):
+            await handle_quick_action(
+                quick_action[1],
+                mcp_client,
+                st.session_state.selected_mcp_server,
+                messages,
+            )
```

Validation: run lint and start the app; the dropdown should still list actions, but internally the selected tuple’s second element is sent to `handle_quick_action`. The import path `mcp_tab -> quick_actions` remains unchanged.

### 3. Add timestamps to messages

To show when each message was sent, modify `draw_mcp_messages()` in `ui/message_rendering.py`. After importing `datetime`, append the current time to the message content before writing it to the chat. Because `draw_mcp_messages()` already runs inside an async loop and writes to Streamlit, adding a timestamp does not affect control flow or imports.

```diff
@@
-from schema import ChatMessage
+from schema import ChatMessage
+from datetime import datetime
@@ async def draw_mcp_messages(messages_agen: AsyncGenerator[ChatMessage, None]) -> None:
-            case "human":
-                st.chat_message("human").write(msg.content)
-            case "ai":
-                st.chat_message("ai").write(msg.content)
+            case "human":
+                ts = datetime.now().strftime("%H:%M")
+                st.chat_message("human").write(f"{msg.content} ({ts})")
+            case "ai":
+                ts = datetime.now().strftime("%H:%M")
+                st.chat_message("ai").write(f"{msg.content} ({ts})")
```

Validation: run lint and the app; messages should now display `(HH:MM)` timestamps. No other module depends on `datetime`, so imports remain correct.

### 4. Wrap conversation in an expander

Long conversations can dominate the page. Wrap the call to `draw_mcp_messages()` inside a collapsible expander. In `ui/mcp_tab.py`, enclose the existing call at lines 41–43 inside `with st.expander("Conversation history"):`. This does not alter asynchronous behaviour since `await draw_mcp_messages(...)` is still executed inside the context manager.

```diff
@@ async def render_mcp_tab() -> None:
-    # Display existing messages using helper
-    await draw_mcp_messages(amessage_iter(messages))
+    # Display existing messages inside collapsible panel
+    with st.expander("Conversation history"):
+        await draw_mcp_messages(amessage_iter(messages))
```

Validation: after linting, run the app; the conversation history can be collapsed or expanded. The import relationship in `src/streamlit_app.py` remains unaffected.

### 5. Improve sidebar accessibility & contrast

To enhance readability and provide context for screen‑reader users, inject light CSS to increase expander header size and add `help=` tooltips to each expander in `ui/sidebar.py`. These modifications occur within the existing `st.sidebar` context and do not require new imports.

```diff
@@ async def render_sidebar(mcp_client, st_state) -> str:
-    with st.sidebar:
+    with st.sidebar:
+        # Accessibility and contrast tweaks
+        st.markdown(
+            "<style>.sidebar .st-expanderHeader{font-size:1.1em;font-weight:bold;}</style>",
+            unsafe_allow_html=True,
+        )
@@
-        with st.expander(f"📋 {info['name']} Tools", expanded=True):
+        with st.expander(f"📋 {info['name']} Tools", expanded=True, help="Tools available on selected server"):
@@
-        with st.expander("🐳 MCP Server Status"):
+        with st.expander("🐳 MCP Server Status", help="Status of each MCP server"):
@@
-        with st.expander("💬 Conversation Tracking"):
+        with st.expander("💬 Conversation Tracking", help="Number of messages and thread ID"):
```

Validation: run lint and the app; the expander headers should be larger and tooltips appear on hover. No change to import paths or logic.
