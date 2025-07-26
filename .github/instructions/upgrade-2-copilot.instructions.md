---
applyTo: '*/workspaces/Agent-Framework/mcp_integration*'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.### Overview


The `ui-upgrade-2` branch currently attempts to inject CSS directly in `mcp_integration/ui/mcp_tab.py`, but the CSS block is missing `<style>` tags and there are no matching elements for the rules.  This results in a blank “Conversation History” region and no sticky input bar.  To centralize styling and achieve a clean chat-like layout, we can separate the CSS into its own module, import it, and wrap the UI elements in identifiable containers.

Below is a detailed, step‑by‑step plan that adds a new CSS module and modifies `render_mcp_tab` to use it.  Every file path, new import, and code change is shown with contextual line numbers from the current `ui-upgrade-2` branch.

## overview of steps ### GitHub Copilot MCP Prompt — UI Upgrade (centralized CSS)

*Read first:* `/workspaces/Agent‑Framework/.github/instructions/ui_upgrade-copilot.instructions.md`

**Goal**
Move all chat‑UI CSS into a new helper, wrap history / input in matching `<div>` IDs, and inject the CSS via `mcp_tab.py`. Wrapper `mcp_integration/mcp_tab.py` must stay untouched.

---

## Step‑by‑Step (1 change per commit)

### **Step 1 – create CSS helper**

1. **filesystem MCP** → write `mcp_integration/ui/css_styles.py` with:

   ```python
   # mcp_integration/ui/css_styles.py
   """
   Centralised chat CSS for the MCP tab.
   """
   CHAT_CSS = """
   <style>
   #mcp-history-area{
       overflow-y:auto;
       height:calc(100vh - 14rem);
       padding-right:0.5rem;
   }
   #mcp-input-area{
       position:sticky;
       bottom:0;
       background:var(--background-color);
       padding:1rem 0;
       border-top:1px solid var(--secondary-background-color);
   }
   div[data-testid="stExpander"] summary{font-size:1.1rem;}
   </style>
   """
   ```

2. **memory MCP** → log new file.

3. **Pylance MCP** → run lint; expect no errors.

### **Step 2 – import & inject CSS**

1. **filesystem MCP** → edit `mcp_integration/ui/mcp_tab.py`:

   * Add `from .css_styles import CHAT_CSS` after existing imports.
   * Replace current multi‑line CSS `st.markdown(""" ...`, unsafe\_allow\_html=True)`block with`st.markdown(CHAT\_CSS, unsafe\_allow\_html=True)\`.

2. **memory MCP** → log changed lines.

3. **Pylance MCP** → lint.

### **Step 3 – add `<div id>` wrappers**

1. **filesystem MCP** → in the same file:

   * **History**: replace the two blank markdown placeholders around `await draw_mcp_messages(...)` with:

     ```python
     st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
     await draw_mcp_messages(amessage_iter(messages))
     st.markdown("</div>", unsafe_allow_html=True)
     ```

   * **Input**: before quick‑action sub‑header add
     `st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)`
     and after the chat‑input block add
     `st.markdown("</div>", unsafe_allow_html=True)`.

2. **memory MCP** → log edits.

3. **Pylance MCP** → lint.

### **Step 4 – runtime check**

1. **filesystem MCP** → ensure wrapper file unchanged.

2. Run `python src/streamlit_app.py`, open MCP tab, send a message:

   * Conversation scrolls independently.
   * Quick‑action & input bar stick to bottom.

3. If layout off, minimally tweak `height: calc(100vh - 14rem);` in `css_styles.py`.

4. **memory MCP** → record any tweak.

### Confirmation protocol

After each numbered step:

* **Re‑run Pylance MCP** and **runtime check**; if both pass, ask:
  `Step X complete — proceed to Step Y?`

If an error appears, stop, describe the issue, await guidance.

Use **Brave‑Search MCP** only if Streamlit CSS behaviour is uncertain.

---


---

### Step 1 – Create a dedicated CSS module

**File / Path** – `mcp_integration/ui/css_styles.py` (new file)

**Purpose** – Centralize all chat‑related CSS in one place so that UI files remain focused on layout and logic.

**Contents**

```python
# mcp_integration/ui/css_styles.py

"""
Centralized CSS for the MCP tab.  Wrap your rules in a <style> tag so
Streamlit applies them correctly.
"""

CHAT_CSS = """
<style>
#mcp-history-area {
    /* Make conversation history scrollable.  Adjust the height to suit your layout. */
    overflow-y: auto;
    height: calc(100vh - 14rem);
    padding-right: 0.5rem;
}

#mcp-input-area {
    /* Stick the input area to the bottom of the viewport. */
    position: sticky;
    bottom: 0;
    background: var(--background-color);
    padding-top: 1rem;
    padding-bottom: 1rem;
    border-top: 1px solid var(--secondary-background-color);
}

/* Enlarge expander header text; useful if you keep an expander wrapper. */
div[data-testid="stExpander"] summary {
    font-size: 1.1rem;
}
</style>
"""
```

This file exports a constant `CHAT_CSS` containing the CSS wrapped in `<style>` tags.  It defines styles for `#mcp-history-area` (scrollable history), `#mcp-input-area` (sticky input area), and enlarges the expander header for accessibility.

---

### Step 2 – Import and inject CSS in `mcp_tab.py`

**File / Path** – `mcp_integration/ui/mcp_tab.py`

**Context** – At the top of `mcp_tab.py`, just after the existing imports (`message_rendering`, `quick_actions`, etc.), add a new import line to bring in the CSS:

```diff
@@
 from .message_rendering import amessage_iter, draw_mcp_messages
 from .quick_actions import build_quick_actions, handle_quick_action
 from .chat_processing import process_mcp_message
+from .css_styles import CHAT_CSS  # new import for centralized CSS
```

This import allows `render_mcp_tab` to reference `CHAT_CSS` and keeps styling separate from logic.

Next, replace the existing inline CSS injection (lines 41–63) with a simple call to `st.markdown(CHAT_CSS, unsafe_allow_html=True)`:

```diff
@@ async def render_mcp_tab() -> None:
-     # CSS injected to make history scrollable and input sticky
-     st.markdown(
-         """
-  
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
-  
-         """,
-         unsafe_allow_html=True,
-     )
+     # Inject the centralized CSS.  CHAT_CSS includes <style> tags and IDs.
+     st.markdown(CHAT_CSS, unsafe_allow_html=True)
```

This change removes the hard‑coded CSS block and ensures that the styles are injected correctly with `<style>` tags.

---

### Step 3 – Wrap history and input sections in identifiable containers

Currently, the file places blank markdown strings (`" "`) around the history and input sections.  These placeholders provide no structure for CSS to target.  Replace them with real `<div>` wrappers that match the IDs defined in the CSS.

**Changes in the history area** (lines 70–75):

```diff
@@ async def render_mcp_tab() -> None:
-     # History container wrapped in an expander
-     with history_area:
-         with st.expander("Conversation history", expanded=True):
-             st.markdown(" ", unsafe_allow_html=True)
-             await draw_mcp_messages(amessage_iter(messages))
-             st.markdown(" ", unsafe_allow_html=True)
+     # History container; use a <div> with an ID so CSS can control its size and scroll
+     with history_area:
+         # Optional: remove the expander entirely for a more chat‑like feel.
+         # If you keep it, the CSS will still enlarge its header.
+         st.markdown("<div id='mcp-history-area'>", unsafe_allow_html=True)
+         await draw_mcp_messages(amessage_iter(messages))
+         st.markdown("</div>", unsafe_allow_html=True)
```

**Changes in the input area** (lines 78–123):

```diff
@@ async def render_mcp_tab() -> None:
-     # Input container with quick actions and chat box
-     with input_area:
-         st.markdown(" ", unsafe_allow_html=True)
-         st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
+     # Input container with quick actions and chat box
+     with input_area:
+         # Open the sticky input wrapper
+         st.markdown("<div id='mcp-input-area'>", unsafe_allow_html=True)
+         st.subheader(f"� {current_server_info.get('name', 'MCP Server')}")
@@
-         # Chat input remains the same but lives inside the sticky container
+         # Chat input remains the same but lives inside the sticky container
@@
-         st.markdown(" ", unsafe_allow_html=True)
+         # Close the sticky input wrapper
+         st.markdown("</div>", unsafe_allow_html=True)
```

These changes remove the blank placeholders and instead wrap the message history and input sections with `<div>` elements that correspond to the CSS selectors defined in `CHAT_CSS`.

---

### Explanation and validation

* **Centralizing CSS** – Creating `css_styles.py` keeps styling definitions separate from business logic, making it easier to adjust heights, colours, or dark‑mode tweaks without editing the main UI file.  The CSS block is wrapped in `<style>` tags so Streamlit actually loads it.
* **Importing CSS** – By importing `CHAT_CSS` at the top of `mcp_tab.py` and injecting it with `st.markdown(CHAT_CSS, unsafe_allow_html=True)`, we ensure the styles are applied once per render.
* **Wrapping content with IDs** – The `#mcp-history-area` and `#mcp-input-area` selectors in the CSS only work if those IDs exist in the HTML.  Replacing the blank markdown strings with `<div id='...'>` wrappers provides the necessary hooks for the styles.  Without these wrappers, the styles do nothing, which is what you observed in the current branch.
* **Optional expander removal** – For a more traditional chat layout, you can remove the `st.expander` entirely.  If you keep it, the CSS rule `div[data-testid="stExpander"] summary` enlarges the header text.

After applying these changes, run the app (`python src/streamlit_app.py`), navigate to the MCP tab, and verify that:

1. The conversation history scrolls independently of the rest of the page.
2. The chat input bar and quick actions remain fixed at the bottom.
3. The wrapper import (`from mcp_tab import render_mcp_tab`) still resolves correctly, as we haven’t altered the wrapper module.

This approach consolidates CSS management and corrects the layout issues present in the `ui-upgrade-2` branch.
