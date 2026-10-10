# DeskDriver 🚀

> **The Native Desktop Automation & Spatial Operating Layer for AI Agents**  
> *Like WebDriver for the Web, DeskDriver is the sub-millisecond, token-free driver for desktop applications.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078d4.svg)]()
[![MCP](https://img.shields.io/badge/MCP-2.3+-green.svg)](https://modelcontextprotocol.io)
[![Latency](https://img.shields.io/badge/hotkey%20latency-0.5%20ms-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ⚡ Why DeskDriver?

Traditional LLM computer-use agents rely on continuous vision captures: taking screenshots, uploading mega-pixel images, paying tens of thousands of tokens per turn, and waiting 2–5 seconds per action while guessing coordinate pixels.

**DeskDriver provides a deterministic native fastpath:**

| Metric | Vision-Based Computer Use | DeskDriver |
| :--- | :--- | :--- |
| **Action Latency** | 2,000 ms – 5,000 ms | **0.5 ms** (Hotkeys) / **< 1 ms** (Roadmap) / **0 ms** (OS URI) |
| **Token Cost** | $0.02 – $0.10+ per click (Vision tokens) | **$0.00** (Native execution) |
| **Coordinate Accuracy** | Fuzzy vision guessing (hallucination prone) | **100% Deterministic** (Win32 & UI Automation tree) |
| **Window Resizing** | Breaks visual layout | **Dynamic edge-anchoring** (adapts automatically) |
| **System Settings** | 5–10 slow sequential clicks | **Instant OS Fastpaths** (`ms-settings:`, `calc:`) |
| **Movement Style** | Abrupt instant teleportation | **Human-like Bézier motion** (undetectable easing) |

---

## 🌐 DeskDriver Wikipedia (UI-Pedia)

DeskDriver includes an authentic, Wikipedia-styled encyclopedic desktop knowledge base (`dashboard.py`):

- **Main Encyclopedia:** Live statistics of all indexed applications, interactive controls, and global hotkeys.
- **Application Articles:** Dedicated encyclopedic pages for apps (e.g. *Brave (software)*, *Notepad (software)*, *File Explorer*), detailing mapped controls, anchors, and shortcuts.
- **Global Shortcut Registry:** Over 30 universal keyboard accelerators dispatchable on-demand.
- **OS Fastpaths Table:** Instant URI protocol handlers to directly open system dialogs.
- **Interactive Live Testing:** Test-click buttons and trigger hotkeys in real time directly from the encyclopedia.
- **Dark & Light Mode:** Authentic Wikipedia typography, infoboxes, and responsive navigation.

Launch it with a single command:
```powershell
deskdriver
# Or: python dashboard.py
```

---

## 🛠️ Core Capabilities

### 1. Atomic Win32 `SendInput` Engine
Dispatches inputs directly into the Windows kernel event queue using verified 40-byte 64-bit `INPUT` unions. Completely avoids deprecated `keybd_event` or stuck auto-repeat modifiers.
- Supports combined chords (`Ctrl+Shift+S`, `Win+Shift+S`, `Alt+F4`).
- Handles isolated desktop stations (`SetThreadDesktop`).
- Native Per-Monitor v2 DPI Awareness (`SetProcessDpiAwarenessContext(-4)`).

### 2. Spatial Roadmap & Responsive Anchoring
Learns application UI structures and serializes them to `ui_roadmap.json`.
- **$O(1)$ coordinate resolution:** Resolves target buttons in under 1 ms without re-querying the accessibility tree.
- **Responsive Anchors:** Automatically anchors controls to `top-left`, `top-right`, or `bottom-right`. When a window is resized, button coordinates dynamically adjust without re-scanning.

### 3. OS Protocol Fastpaths (0 ms)
Bypasses manual clicking for operating system utilities:
- `open_fastpath("display")` &rarr; opens `ms-settings:display`
- `open_fastpath("sound")` &rarr; opens `ms-settings:sound`
- `open_fastpath("taskmgr")` &rarr; opens Windows Task Manager
- `open_fastpath("calc")` &rarr; launches Calculator

### 4. Human-like Bézier Cursor Dynamics
Generates cubic Bézier curves parameterized with smoothstep velocity easing and micro-overshoot corrections, making cursor automation appear completely natural (150–250 ms duration) without mechanical jumping.

### 5. Privacy Sanitizer & Community Hub Ready
Built-in privacy sanitizer scrubs document filenames, file paths (`C:\Users\...`), emails, and PII before exporting roadmap profiles for community sharing. See [ROADMAP.md](ROADMAP.md).

---

## 📦 Installation & Setup

### Requirements
- Windows 10 or 11 (64-bit)
- Python 3.10 or newer

```powershell
# Clone the repository
git clone https://github.com/robertbeck-stack/deskdriver.git
cd deskdriver

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .
```

---

## 🚀 Quickstart

### 1. Run the Interactive Demo
Inspect your cursor, list foreground controls, and observe smooth Bézier movement:
```powershell
python demo.py
```

### 2. Launch the Wikipedia Encyclopedia
```powershell
deskdriver
# Open http://localhost:8765 in your browser
```

### 3. Run the Automated Test Suite
```powershell
python tests/test_deskdriver.py
```

---

## 🤖 MCP (Model Context Protocol) Integration

DeskDriver exposes a high-performance **MCP Server** ready for integration with Claude Desktop, Antigravity, Cursor, and any MCP-compliant client.

### Configuration (`claude_desktop_config.json`)

Add the following to your MCP settings file (e.g. `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "deskdriver": {
      "command": "C:\\path\\to\\deskdriver\\.venv\\Scripts\\python.exe",
      "args": ["-m", "deskdriver.server"]
    }
  }
}
```

### Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `fast_click` | `element_name`, `window_search`, `instant=True` | **Smart action:** Dispatches hotkey if available (0.5 ms), or clicks cached roadmap coordinates (< 1 ms). |
| `press_hotkey` | `hotkey` (e.g. `ctrl+s`, `win+shift+s`) | Dispatches an atomic keyboard accelerator directly to the OS event queue. |
| `type_text` | `text`, `enter=False` | Types clean Unicode text into the active control via `SendInput`. |
| `open_fastpath` | `target` (e.g. `system`, `sound`, `calc`) | Instantly opens Windows settings or tools via URI protocols (0 ms). |
| `fill_input` | `element_name`, `text`, `press_enter=True` | Clicks an input field, clears existing content (`Ctrl+A` -> `Backspace`), and types the new text. |
| `system_prelearn` | `max_elements_per_app=150` | Scans all open windows and caches their interactive controls into `ui_roadmap.json`. |
| `get_roadmap_stats` | *none* | Returns cached application summaries and indexed controls. |
| `get_mouse_position` | *none* | Returns current screen coordinates `(x, y)`. |
| `move_mouse` | `x`, `y`, `smooth=True`, `duration=0.25` | Moves the cursor using human Bézier trajectory. |
| `click` | `button="left"`, `clicks=1` | Clicks mouse button at current position (supports left, right, double). |
| `move_and_click` | `x`, `y`, `button="left"`, `clicks=1` | Moves smoothly to target and clicks in a single action. |
| `mouse_scroll` | `clicks=3`, `direction="down"` | Smoothly scrolls the mouse wheel. |
| `drag_and_drop` | `start_x`, `start_y`, `end_x`, `end_y` | Performs click-drag-release operations. |
| `inspect_under_cursor` | *none* | Inspects the UI Automation control directly under the cursor. |
| `inspect_at` | `x`, `y` | Inspects control metadata at specific coordinates without moving cursor. |
| `list_windows` | *none* | Returns all visible desktop windows with handles and coordinates. |
| `list_clickable_elements` | `window_search=""`, `max_elements=40` | Finds buttons and inputs in a window with their exact center coordinates. |
| `snap_window` | `window_search`, `side="left"` | Snaps a window to screen halves or center (`left`, `right`, `top`, `bottom`, `center`, `full`). |
| `maximize_window` / `minimize_window` | `window_search` | Maximizes or minimizes a target window via native Win32. |
| `move_window` | `window_search`, `x`, `y`, `width`, `height` | Repositions and resizes a target window. |
| `clipboard_paste` | `text` | Instantly pastes long multi-line text (0.5 ms) via Windows clipboard and `Ctrl+V`. |
| `clipboard_get` | *none* | Reads the current text from the Windows clipboard. |
| `record_current_element` | `custom_name=""` | Captures the element under cursor with responsive anchors directly into the roadmap cache. |
| `wait_for_window` | `window_search`, `timeout=3.0` | Polls until a window appears, eliminating arbitrary sleep delays in AI agent execution. |
| `wait_for_element` | `element_name`, `window_search=""`, `timeout=3.0` | Polls until a specific control/button is ready and rendered. |
| `wait_and_click` | `element_name`, `window_search=""`, `timeout=3.0` | Waits for a target button/dialog and clicks it immediately in one atomic call. |

---

## 🐍 Python API Usage

DeskDriver can also be used directly as a standalone Python library:

```python
import deskdriver as dd

# 1. Bring application to focus and snap to screen half
dd.focus_window("Notepad")
dd.snap_window("Notepad", "left")

# 2. Fast-click or trigger keyboard shortcuts (0.5 ms)
dd.press_hotkey("ctrl+s")

# 3. Instant clipboard paste (0.5 ms for massive multiline text)
dd.clipboard_paste("Hello World from DeskDriver!\nInstant multiline execution.")

# 4. Fill an input field
dd.fill_input("Address and search bar", "https://github.com", submit=True)

# 5. Human-like Bézier mouse motion
dd.move_mouse(500, 300, smooth=True, duration=0.2)

# 6. Record whatever element is currently under the mouse cursor
record_info = dd.record_element_at_cursor(custom_name="SaveButton")
```

### Backward Compatibility
For legacy integrations, `ai_mouse` is retained as an importable shim:
```python
# Fully supported drop-in alias
import ai_mouse as am
am.move_mouse(100, 100)
```

---

## 🗺️ Project Architecture

```text
deskdriver/
├── src/
│   ├── deskdriver/                # Primary package
│   │   ├── core/                  # Low-level Win32 integration
│   │   │   ├── desktop.py         # Thread desktops, DPI awareness context
│   │   │   ├── keyboard.py        # 40-byte atomic SendInput, hotkeys
│   │   │   └── mouse.py           # Bézier movement, clicks, scrolls, drags
│   │   ├── automation/            # Windows UI Automation (UIA)
│   │   │   ├── windows.py         # Window enumeration & foreground focus
│   │   │   └── uia.py             # COM element inspection & clickables
│   │   ├── navigation/            # Spatial navigation & caching
│   │   │   ├── fastpaths.py       # OS URI handlers (ms-settings, calc)
│   │   │   ├── hotkeys.py         # Accelerator extraction from UI text
│   │   │   ├── prelearn.py        # Batch scanner for open applications
│   │   │   └── roadmap.py         # O(1) cache with responsive anchors
│   │   ├── sync/                  # Cloud sync & community sharing
│   │   │   ├── sanitizer.py       # PII & path scrubbing
│   │   │   └── client.py          # Community roadmap client
│   │   └── server.py              # FastMCP Server implementation
│   └── ai_mouse/                  # Backward compatibility shim
│       └── __init__.py            # Re-exports deskdriver
├── tests/
│   └── test_deskdriver.py         # Self-check verification test suite
├── dashboard.py                   # Wikipedia-style UI-Pedia web interface
├── demo.py                        # Terminal interactive demo
├── pyproject.toml                 # Packaging configuration (v0.2.0)
└── ROADMAP.md                     # Community Hub & Future Architecture
```

---

## 📄 License

DeskDriver is released under the **MIT License**. Free for commercial and personal agent automation.
