---
applyTo: '*/workspaces/Agent-Framework/mcp_integration*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.
## Dependency Confirmation Table

| Module / File                              | Imported By                                                                                    |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| **core/config.py**                         | `core/mcp_openai_bot.py` uses `OPENAI_API_KEY` and `BRAVE_API_KEY`                             |
| **core/plugin\_manager.py**                | `core/config.py` imports `load_plugins`; `core/multi_client.py` imports `load_plugins`         |
| **core/multi\_client.py**                  | `core/mcp_openai_bot.py` imports `MultiMCPClient`; `ui/mcp_tab.py` imports it for UI rendering |
| **core/mcp\_openai\_bot.py**               | Used only in `ui/mcp_tab.py` via `process_mcp_message`                                         |
| **clients/filesystem\_client.py**          | Dynamically loaded by `plugin_manager` via `importlib` based on YAML; not imported statically  |
| **clients/brave\_search\_client.py**       | Dynamically loaded by `plugin_manager` via `importlib`                                         |
| **plugins/filesystem/config.yaml**         | Parsed by `plugin_manager.load_plugins`; no direct imports                                     |
| **plugins/brave\_search/config.yaml**      | Parsed by `plugin_manager.load_plugins`; no direct imports                                     |
| **ui/mcp\_tab.py**                         | Imported by `mcp_integration/mcp_tab.py` wrapper                                               |
| **mcp\_integration/mcp\_tab.py** (wrapper) | Imported by `src/streamlit_app.py`                                                             |
| **utils/\_\_init\_\_.py**                  | Not imported by any module (placeholder)                                                       |

## Safe‑Refactor Plan (one change per step)

1. **Move session initialisation to `session_utils.py`:**
   Create `mcp_integration/ui/session_utils.py` with an async `init_session_state(st_state, MultiMCPClient)` function containing lines 24‑53 of `ui/mcp_tab.py`. In `ui/mcp_tab.py`, import `init_session_state` and call it at the start of `render_mcp_tab`. Re‑export nothing here; update wrapper to keep re‑export of `render_mcp_tab`. Run `python -m pylint mcp_integration` and `python src/streamlit_app.py` to ensure imports and behaviour remain valid and `from mcp_tab import render_mcp_tab` still resolves.

2. **Extract sidebar UI to `sidebar.py`:**
   Create `mcp_integration/ui/sidebar.py` with an async `render_sidebar(mcp_client, st_state)` that encapsulates sidebar code (lines 56‑115). Return `selected_server` and update session state internally. In `ui/mcp_tab.py`, import and call `render_sidebar`. Keep wrapper re‑exports unchanged. After moving, run pylint and launch Streamlit to verify that the MCP tab still appears and server selection works.

3. **Move message rendering helpers to `message_rendering.py`:**
   Create `mcp_integration/ui/message_rendering.py` and move `amessage_iter` and `draw_mcp_messages` definitions there. Export `draw_mcp_messages` and any required generator. In `ui/mcp_tab.py`, import `draw_mcp_messages` from the new module; update the wrapper (`mcp_integration/mcp_tab.py`) to re‑export `draw_mcp_messages` from `message_rendering`. Verify with pylint and `python src/streamlit_app.py` that messages render correctly.

4. **Isolate quick‑action logic into `quick_actions.py`:**
   Create `mcp_integration/ui/quick_actions.py` with functions to build the list of quick actions from `server_tools` and to handle execution (the code inside the Execute button and chat input handlers). These functions should accept parameters such as `selected_server`, `messages`, `mcp_client`, and `st_state`, call `process_mcp_message` as needed, and update session state. Replace the corresponding code in `render_mcp_tab` with calls to these helpers. After modifications, run pylint and launch the app to ensure quick actions still work.

5. **Move message processing to `chat_processing.py`:**
   Create `mcp_integration/ui/chat_processing.py` and move the `process_mcp_message` function there. Ensure it imports `MCPOpenAIBot` lazily (inside the function) to avoid circular imports. In `ui/mcp_tab.py`, import `process_mcp_message` from this new module; update the wrapper to re‑export it. Run lint and test that responses are returned and persistent bot instances still function.

6. **Update wrapper imports and verify entry‑point stability:**
   Modify `mcp_integration/mcp_tab.py` so that it imports `render_mcp_tab` from `ui/mcp_tab.py`, `draw_mcp_messages` from `ui/message_rendering.py` and `process_mcp_message` from `ui/chat_processing.py` (matching names exactly). Keep the `__all__` list unchanged. Confirm that `from mcp_tab import render_mcp_tab` still resolves and that `streamlit_app.py` launches successfully.

7. **Test and monitor circular/async risks:**
   After each step, ensure that no new circular imports are introduced (e.g., avoid importing `ui/mcp_tab.py` inside helpers). For helper modules requiring `ChatMessage`, import it using `from schema import ChatMessage` and, if necessary, replicate the `sys.path` insertion or move the path adjustment into an `__init__.py` file. Verify async functions remain async and are awaited correctly. Run `python -m pylint mcp_integration` to detect import cycles and run `python src/streamlit_app.py` to validate that the MCP tab still loads and behaves as before.

## 1. Directory / File Checklist

* [ ] `mcp_integration/ui/session_utils.py` (new) – holds session/state initialisation logic
* [ ] `mcp_integration/ui/sidebar.py` (new) – renders server sidebar, resets chat, shows status
* [ ] `mcp_integration/ui/message_rendering.py` (new) – provides `amessage_iter` and `draw_mcp_messages`
* [ ] `mcp_integration/ui/quick_actions.py` (new) – builds/handles quick actions
* [ ] `mcp_integration/ui/chat_processing.py` (new) – contains `process_mcp_message`
* [ ] Update `mcp_integration/ui/mcp_tab.py` – remove extracted code and call helpers
* [ ] Update `mcp_integration/mcp_tab.py` – re‑export functions from new modules

## 2. Step‑by‑Step Diffs

### Step 1 – extract session initialisation

**Files:** `ui/mcp_tab.py` (#L24-L53 → removed), new `ui/session_utils.py`

```python
# mcp_integration/ui/session_utils.py
"""Session initialization helpers for MCP tab."""
import uuid
import streamlit as st
from core.multi_client import MultiMCPClient

async def init_mcp_session(st_state: st.session_state) -> MultiMCPClient:
    """Initialise session state and return MultiMCPClient."""
    if "user_id" not in st_state:
        st_state.user_id = str(uuid.uuid4())
    if "mcp_client" not in st_state:
        try:
            with st.spinner("Connecting to MCP servers..."):
                st_state.mcp_client = MultiMCPClient()
                await st_state.mcp_client.initialize()
        except Exception as e:
            st.error(f"Error connecting to MCP servers: {e}")
            st.markdown("Make sure the MCP containers are running.")
            st.stop()
    mcp_client: MultiMCPClient = st_state.mcp_client
    if "mcp_messages" not in st_state:
        st_state.mcp_messages = []
    if "mcp_thread_id" not in st_state:
        st_state.mcp_thread_id = str(uuid.uuid4())
    if "selected_mcp_server" not in st_state:
        available_servers = mcp_client.get_available_servers()
        st_state.selected_mcp_server = list(available_servers.keys())[0] if available_servers else None
    return mcp_client
```

**Diff (ui/mcp\_tab.py)**

```diff
@@ async def render_mcp_tab() -> None:
-    # Get or create user ID (following streamlit_app.py pattern)
-    user_id = st.session_state.get("user_id", str(uuid.uuid4()))
-    
-    # Initialize Multi-MCP client (like AgentClient initialization)
-    if "mcp_client" not in st.session_state:
-        try:
-            with st.spinner("Connecting to MCP servers..."):
-                st.session_state.mcp_client = MultiMCPClient()
-                await st.session_state.mcp_client.initialize()
-        except Exception as e:
-            st.error(f"Error connecting to MCP servers: {e}")
-            st.markdown("Make sure the MCP containers are running.")
-            st.stop()
-    
-    mcp_client: MultiMCPClient = st.session_state.mcp_client
-    
-    # Initialize MCP messages and selected server (following streamlit_app.py pattern)
-    if "mcp_messages" not in st.session_state:
-        st.session_state.mcp_messages = []
-        
-    if "mcp_thread_id" not in st.session_state:
-        st.session_state.mcp_thread_id = str(uuid.uuid4())
-    
-    if "selected_mcp_server" not in st.session_state:
-        # Set default to first available server
-        available_servers = mcp_client.get_available_servers()
-        if available_servers:
-            st.session_state.selected_mcp_server = list(available_servers.keys())[0]
-        else:
-            st.session_state.selected_mcp_server = None
+    # Initialise session and get MCP client from helper
+    from .session_utils import init_mcp_session
+    mcp_client = await init_mcp_session(st.session_state)
```

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

### Step 2 – extract sidebar rendering

**Files:** `ui/mcp_tab.py` (#L56-L115 → removed), new `ui/sidebar.py`

```python
# mcp_integration/ui/sidebar.py
"""Sidebar rendering for MCP tab."""
import uuid
import streamlit as st

def render_sidebar(mcp_client, st_state) -> str:
    """Render the MCP sidebar and return the selected server."""
    with st.sidebar:
        st.subheader("🛠️ MCP Servers")
        if st.button(":material/chat: New MCP Chat", use_container_width=True):
            st_state.mcp_messages = []
            st_state.mcp_thread_id = str(uuid.uuid4())
            st.rerun()
        available_servers = mcp_client.get_available_servers()
        if not available_servers:
            st.error("No MCP servers available")
            st.stop()
        server_options = {sid: f"{info['icon']} {info['name']}" for sid, info in available_servers.items()}
        selected_server = st.selectbox(
            "Select MCP Server:",
            options=list(server_options.keys()),
            format_func=lambda x: server_options[x],
            index=list(server_options.keys()).index(st_state.selected_mcp_server)
            if st_state.selected_mcp_server in server_options else 0,
            key="mcp_server_selector",
        )
        if selected_server != st_state.selected_mcp_server:
            st_state.selected_mcp_server = selected_server
            st.rerun()
        server_info = available_servers[selected_server]
        with st.expander(f"📋 {server_info['name']} Tools", expanded=True):
            st.write(f"**{server_info['description']}**")
            st.write(f"**{len(server_info['tools'])} tools available:**")
            for tool_name in server_info['tools'][:8]:
                tool_details = mcp_client.get_server_tools(selected_server)
                tool_desc = tool_details.get(tool_name, {}).get('description', 'No description')
                st.write(f"• **{tool_name}**: {tool_desc}")
            if len(server_info['tools']) > 8:
                st.write(f"... and {len(server_info['tools']) - 8} more tools")
        with st.expander("🐳 MCP Server Status"):
            for server_id, info in available_servers.items():
                status_icon = "✅" if server_id == selected_server else "⚪"
                st.write(f"{status_icon} {info['icon']} **{info['name']}**")
                if server_id == selected_server:
                    st.write(f"   *{info['description']}*")
        with st.expander("💬 Conversation Tracking"):
            message_count = len(st_state.mcp_messages)
            st.info(f"📝 {message_count} messages in current conversation")
            st.write("**Context**: Last 20 messages sent to AI")
            if message_count > 0:
                st.write(f"**Thread ID**: {st_state.mcp_thread_id[:8]}...")
    return selected_server
```

**Diff (ui/mcp\_tab.py)**

```diff
@@ async def render_mcp_tab() -> None:
-    # MCP Tab sidebar configuration (following streamlit_app.py pattern)
-    with st.sidebar:
-        st.subheader("🛠️ MCP Servers")
-        ...
-        with st.expander("💬 Conversation Tracking"):
-            message_count = len(st.session_state.mcp_messages)
-            st.info(f"📝 {message_count} messages in current conversation")
-            st.write("**Context**: Last 20 messages sent to AI")
-            if message_count > 0:
-                st.write(f"**Thread ID**: {st.session_state.mcp_thread_id[:8]}...")
+    # Render sidebar via helper and update selected server
+    from .sidebar import render_sidebar
+    _ = render_sidebar(mcp_client, st.session_state)
```

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

### Step 3 – move message rendering helpers

**Files:** `ui/mcp_tab.py` (#L123-L127 and #L243-L260 → removed), new `ui/message_rendering.py`

```python
# mcp_integration/ui/message_rendering.py
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
```

**Diff (ui/mcp\_tab.py)**

```diff
@@
-    # Display existing messages (following streamlit_app.py pattern)
-    async def amessage_iter() -> AsyncGenerator[ChatMessage, None]:
-        for m in messages:
-            yield m
-
-    await draw_mcp_messages(amessage_iter())
+    from .message_rendering import amessage_iter, draw_mcp_messages
+    await draw_mcp_messages(amessage_iter(messages))
@@
-async def draw_mcp_messages(
-    messages_agen: AsyncGenerator[ChatMessage, None],
-) -> None:
-    """Draw MCP messages - simplified version of streamlit_app.py draw_messages"""
-    
-    # Iterate over messages and draw them (following streamlit_app.py pattern)
-    while msg := await anext(messages_agen, None):
-        if not isinstance(msg, ChatMessage):
-            st.error(f"Unexpected message type: {type(msg)}")
-            continue
-            
-        match msg.type:
-            case "human":
-                st.chat_message("human").write(msg.content)
-            case "ai":
-                st.chat_message("ai").write(msg.content)
-            case _:
-                st.error(f"Unexpected ChatMessage type: {msg.type}")
-
- 
@@
 async def process_mcp_message(user_input: str, mcp_client: MultiMCPClient, selected_server: str, conversation_history: list[ChatMessage] | None = None) -> str:
```

Also remove the now unused import:

```diff
@@
-from collections.abc import AsyncGenerator
```

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

### Step 4 – extract quick‑action logic

**Files:** `ui/mcp_tab.py` (#L130-L169 & #L174-L207 → replaced), new `ui/quick_actions.py`

```python
# mcp_integration/ui/quick_actions.py
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
    user_message = ChatMessage(type="human", content=action)
    messages.append(user_message)
    st.chat_message("human").write(action)
    try:
        ai_response = await process_mcp_message(action, mcp_client, selected_server, messages)
        ai_message = ChatMessage(type="ai", content=ai_response)
        messages.append(ai_message)
        st.chat_message("ai").write(ai_response)
        st.rerun()
    except Exception as e:
        st.error(f"Error processing MCP request: {e}")
        st.stop()
```

**Diff (ui/mcp\_tab.py)**

```diff
@@ async def render_mcp_tab() -> None:
-    # Create dynamic quick actions based on available tools
-    server_tools = current_server_info.get('tools', [])
-    quick_actions = ["Select an action..."]
-    
-    # Add filesystem actions
-    if "list_directory" in server_tools:
-        quick_actions.append("List the contents of the directory")
-    if "create_directory" in server_tools:
-        quick_actions.append("Create a new directory")
-    if "read_file" in server_tools:
-        quick_actions.append("Read a file")
-    if "write_file" in server_tools:
-        quick_actions.append("Write to a file")
-    if "move_file" in server_tools:
-        quick_actions.append("Move or rename a file")
-    if "get_file_info" in server_tools:
-        quick_actions.append("Get file information")
-    if "search_files" in server_tools:
-        quick_actions.append("Search for a specific file")
-    
-    # Add Brave Search actions
-    if "brave_web_search" in server_tools:
-        quick_actions.append("Search the web")
-    if "brave_image_search" in server_tools:
-        quick_actions.append("Search for images")
-    if "brave_video_search" in server_tools:
-        quick_actions.append("Search for videos")
-    if "brave_news_search" in server_tools:
-        quick_actions.append("Search for news")
-    if "brave_local_search" in server_tools:
-        quick_actions.append("Search for local businesses")
-    if "list_issues" in server_tools:
-        quick_actions.append("List repository issues")
-    if "get_file_contents" in server_tools:
-        quick_actions.append("Get contents of a file from repository")
-    if "create_repository" in server_tools:
-        quick_actions.append("Create a new repository")
-    if "fork_repository" in server_tools:
-        quick_actions.append("Fork a repository")
-    if "create_branch" in server_tools:
-        quick_actions.append("Create a new branch")
+    server_tools = current_server_info.get("tools", [])
+    from .quick_actions import build_quick_actions, handle_quick_action
+    quick_actions = build_quick_actions(server_tools)
@@
-    # Create columns for better layout
-    col1, col2 = st.columns([3, 1])
-    
-    with col1:
-        quick_action = st.selectbox(
-            "Choose an action:",
-            quick_actions,
-            key="mcp_quick_action"
-        )
-    
-    with col2:
-        if st.button("Execute", use_container_width=True, type="primary"):
-            if quick_action != "Select an action..." and st.session_state.selected_mcp_server:
-                # Add the selected action as user message
-                user_message = ChatMessage(type="human", content=quick_action)
-                messages.append(user_message)
-                st.chat_message("human").write(quick_action)
-                
-                try:
-                    # Process with MCP (simplified - no streaming for now)
-                    ai_response = await process_mcp_message(
-                        quick_action, 
-                        mcp_client, 
-                        st.session_state.selected_mcp_server,
-                        messages
-                    )
-                    
-                    # Add AI response
-                    ai_message = ChatMessage(type="ai", content=ai_response)
-                    messages.append(ai_message)
-                    st.chat_message("ai").write(ai_response)
-                    
-                    st.rerun()  # Clear stale containers like streamlit_app.py
-                    
-                except Exception as e:
-                    st.error(f"Error processing MCP request: {e}")
-                    st.stop()
+    # Create columns for better layout
+    col1, col2 = st.columns([3, 1])
+    with col1:
+        quick_action = st.selectbox(
+            "Choose an action:",
+            quick_actions,
+            key="mcp_quick_action",
+        )
+    with col2:
+        if st.button("Execute", use_container_width=True, type="primary"):
+            await handle_quick_action(
+                quick_action,
+                mcp_client,
+                st.session_state.selected_mcp_server,
+                messages,
+            )
```

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

### Step 5 – move process\_mcp\_message to chat\_processing.py

**Files:** `ui/mcp_tab.py` (#L263-L309 → removed), new `ui/chat_processing.py`

```python
# mcp_integration/ui/chat_processing.py
"""Process user messages via MCP/OpenAI."""
import streamlit as st
from core.multi_client import MultiMCPClient
from typing import Optional
from schema import ChatMessage

async def process_mcp_message(user_input: str, mcp_client: MultiMCPClient, selected_server: str,
                              conversation_history: Optional[list] = None) -> str:
    """Process input with persistent MCPOpenAIBot and conversation context."""
    from core.mcp_openai_bot import MCPOpenAIBot  # imported here to avoid circular import
    try:
        bot_key = f"mcp_bot_{selected_server}"
        if bot_key not in st.session_state or st.session_state[bot_key] is None:
            st.session_state[bot_key] = MCPOpenAIBot(selected_server, mcp_client)
            await st.session_state[bot_key].initialize()
        bot = st.session_state[bot_key]
        if conversation_history:
            conversation_context = ""
            for msg in conversation_history[-20:]:
                if msg.type == "human":
                    conversation_context += f"User: {msg.content}\n"
                elif msg.type == "ai":
                    conversation_context += f"Assistant: {msg.content}\n"
            contextual_input = (
                f"Previous conversation:\n{conversation_context}\nCurrent request: {user_input}"
                if conversation_context else user_input
            )
        else:
            contextual_input = user_input
        server_info = mcp_client.get_available_servers().get(selected_server, {})
        server_context = f"You are working with {server_info.get('name', 'MCP Server')} ({selected_server}). "
        full_input = server_context + contextual_input
        response = await bot.chat(full_input)
        return response
    except Exception as e:
        return f"Sorry, I encountered an error processing your request: {str(e)}"
```

**Diff (ui/mcp\_tab.py)**

```diff
@@
-from core.mcp_openai_bot import MCPOpenAIBot
@@
-async def process_mcp_message(user_input: str, mcp_client: MultiMCPClient, selected_server: str, conversation_history: list[ChatMessage] | None = None) -> str:
-    """Process user message with MCP tools via OpenAI with conversation context"""
-    # Import the OpenAI bot here to avoid circular imports
-    from core.mcp_openai_bot import MCPOpenAIBot
-    ...
-    except Exception as e:
-        return f"Sorry, I encountered an error processing your request: {str(e)}"
+# Removed local process_mcp_message; imported from helper
```

At the top of `ui/mcp_tab.py`, add a new import:

```diff
@@
-from schema import ChatMessage
+from schema import ChatMessage
+from .chat_processing import process_mcp_message
```

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

### Step 6 – update wrapper to re‑export functions

**File:** `mcp_integration/mcp_tab.py`

```diff
@@
-from ui.mcp_tab import render_mcp_tab, draw_mcp_messages, process_mcp_message
+from ui.mcp_tab import render_mcp_tab
+from ui.message_rendering import draw_mcp_messages
+from ui.chat_processing import process_mcp_message
```

`__all__` remains `["render_mcp_tab", "draw_mcp_messages", "process_mcp_message"]`.

✅ ready to run: `python -m pylint mcp_integration && python src/streamlit_app.py`

## 3. Import‑Update Table

| File & Old Import                                                                                                                          | Updated Import                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ui/mcp_tab.py`: local definitions of session init, sidebar, amessage\_iter, draw\_mcp\_messages, quick actions, and process\_mcp\_message | Remove these definitions; instead add `from .session_utils import init_mcp_session`, `from .sidebar import render_sidebar`, `from .message_rendering import amessage_iter, draw_mcp_messages`, `from .quick_actions import build_quick_actions, handle_quick_action`, and `from .chat_processing import process_mcp_message` |
| `ui/mcp_tab.py`: `from collections.abc import AsyncGenerator`                                                                              | Remove – unused after extracting message rendering                                                                                                                                                                                                                                                                           |
| `mcp_integration/mcp_tab.py`: `from ui.mcp_tab import render_mcp_tab, draw_mcp_messages, process_mcp_message`                              | Update to import `render_mcp_tab` from `ui.mcp_tab` and the other two functions from `ui.message_rendering` and `ui.chat_processing`                                                                                                                                                                                         |

## 4. Validation Commands per Step

After completing each numbered step above:

* Run `python -m pylint mcp_integration` to check for syntax/import errors and cyclic dependencies (`pylint --disable=all --enable=cyclic-import mcp_integration` as needed).
* Run `python src/streamlit_app.py` and verify that the MCP tab loads, the sidebar populates servers, quick actions appear and execute, and free‑text chat works.
* Ensure `from mcp_tab import render_mcp_tab` still resolves in a REPL: `python -c "from mcp_tab import render_mcp_tab; print(render_mcp_tab)"`.

Proceed only when both linting and runtime tests succeed before applying the next step.

## 5. Wrapper Update Diff

See Step 6 diff: `mcp_integration/mcp_tab.py` now imports `render_mcp_tab` from `ui.mcp_tab`, `draw_mcp_messages` from `ui.message_rendering`, and `process_mcp_message` from `ui.chat_processing`, preserving the original `__all__` list.

## 6. Final Completeness Checklist

* [ ] All helper modules (`session_utils.py`, `sidebar.py`, `message_rendering.py`, `quick_actions.py`, `chat_processing.py`) exist in `mcp_integration/ui` and contain the code above.
* [ ] `ui/mcp_tab.py` calls helpers instead of containing duplicated logic; unused imports removed.
* [ ] `mcp_integration/mcp_tab.py` re‑exports `render_mcp_tab`, `draw_mcp_messages`, `process_mcp_message` from the correct modules.
* [ ] Running `python -m pylint mcp_integration` shows no import or cyclic‑import errors.
* [ ] Running `python src/streamlit_app.py` launches without modifying `src/streamlit_app.py`; the MCP tab still functions (server selection, quick actions, conversation tracking, message display).
* [ ] Import path `from mcp_tab import render_mcp_tab` is still valid and returns the UI function.
* [ ] No other files outside `mcp_integration` were altered without explicit approval; entry‑point file remains untouched.
* [ ] Final refactor preserves asynchronous flow and avoids circular imports.
