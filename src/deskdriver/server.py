"""
Model Context Protocol (MCP) Server for ai-mouse.
Exposes modular tools to AI agents.
"""

from mcp.server.mcpserver import MCPServer
import deskdriver as am

server = MCPServer("deskdriver")


@server.tool()
def get_mouse_position() -> dict:
    """Get the current (x, y) screen coordinates of the mouse cursor."""
    x, y = am.get_mouse_position()
    return {"x": x, "y": y}


@server.tool()
def move_mouse(x: int, y: int, smooth: bool = True, duration: float = 0.25) -> dict:
    """
    Move the mouse cursor to (x, y) coordinates.
    Set smooth=True for human-like natural Bézier curve movement.
    """
    am.move_mouse(x, y, smooth=smooth, duration=duration)
    curr_x, curr_y = am.get_mouse_position()
    return {"status": "moved", "x": curr_x, "y": curr_y}


@server.tool()
def click(button: str = "left", clicks: int = 1) -> dict:
    """
    Click at current mouse position.
    button: 'left', 'right', or 'middle'.
    clicks: 1 for single click, 2 for double click.
    """
    am.mouse_click(button=button, clicks=clicks)
    x, y = am.get_mouse_position()
    return {"status": "clicked", "button": button, "clicks": clicks, "at_x": x, "at_y": y}


@server.tool()
def move_and_click(
    x: int, y: int, button: str = "left", clicks: int = 1, smooth: bool = True, duration: float = 0.25
) -> dict:
    """Move the mouse to (x, y) and click in one fluid operation."""
    am.move_and_click(x, y, button=button, clicks=clicks, smooth=smooth, duration=duration)
    return {"status": "moved_and_clicked", "button": button, "clicks": clicks, "x": x, "y": y}


@server.tool()
def mouse_scroll(delta: int = 120) -> dict:
    """
    Scroll the mouse wheel vertically.
    Positive delta scrolls up; negative delta scrolls down (e.g. 120 or -120).
    """
    am.mouse_scroll(delta=delta)
    return {"status": "scrolled", "delta": delta}


@server.tool()
def drag_and_drop(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    smooth: bool = True,
    duration: float = 0.35,
) -> dict:
    """Click and drag from (start_x, start_y) to (end_x, end_y)."""
    am.drag_and_drop(start_x, start_y, end_x, end_y, smooth=smooth, duration=duration)
    return {"status": "dragged_and_dropped", "from": [start_x, start_y], "to": [end_x, end_y]}



@server.tool()
def press_hotkey(hotkey: str) -> dict:
    """
    Press and release a keyboard combination (e.g. 'ctrl+s', 'win+shift+s', 'ctrl+t', 'enter').
    Executes in 0.5 ms for maximum speed.
    """
    am.press_hotkey(hotkey)
    return {"status": "hotkey_executed", "hotkey": hotkey}


@server.tool()
def type_text(text: str, enter: bool = False) -> dict:
    """
    Type Unicode text directly into the focused input or window.
    Set enter=True to submit by pressing Enter after typing.
    """
    am.type_text(text, enter=enter)
    return {"status": "typed", "length": len(text), "enter_pressed": enter}



@server.tool()
def inspect_under_cursor() -> dict:
    """
    Inspect the exact UI element currently under the mouse cursor.
    Returns name, control type, bounding rectangle, and parent window title.
    """
    return am.get_element_under_cursor()


@server.tool()
def inspect_at(x: int, y: int) -> dict:
    """Inspect the UI element located at coordinates (x, y) without moving the mouse."""
    return am.get_element_at(x, y)


@server.tool()
def list_windows() -> list[dict]:
    """List all open and visible application windows on the desktop."""
    return am.list_windows()


@server.tool()
def focus_window(title_or_hwnd: str) -> dict:
    """Bring a window to foreground and give it focus."""
    target = int(title_or_hwnd) if title_or_hwnd.isdigit() else title_or_hwnd
    success = am.focus_window(target)
    return {"success": success, "target": title_or_hwnd}


@server.tool()
def list_clickable_elements(window_search: str = "", max_elements: int = 40) -> list[dict]:
    """Find clickable/interactive elements in the active or searched window."""
    search = window_search.strip() if window_search else None
    return am.list_clickable_elements(window_search=search, max_elements=max_elements)


@server.tool()
def fast_click(element_name: str, window_search: str = "", instant: bool = True) -> dict:
    """
    High-speed click on an element by name (e.g. 'System', 'Reload', 'Minimise').
    Uses Roadmap Cache to resolve coordinates in < 1ms if previously learned.
    Automatically learns on cache miss.
    """
    return am.fast_click_element(element_name=element_name, window_search=window_search, instant=instant)


@server.tool()
def fill_input(
    element_name: str,
    text: str,
    window_search: str = "",
    submit: bool = False,
    clear_existing: bool = True,
) -> dict:
    """
    Combined high-efficiency tool for AI:
    Focuses the window, clicks into the input field (via Roadmap cache or UIA),
    clears previous text, types new text, and optionally presses Enter to submit.
    """
    return am.fill_input(
        element_name=element_name,
        text=text,
        window_search=window_search,
        submit=submit,
        clear_existing=clear_existing,
    )



@server.tool()
def open_fastpath(target: str) -> dict:
    """
    Direct zero-click OS shortcut to navigate Windows settings or tools.
    Examples: 'system', 'display', 'sound', 'bluetooth', 'wifi', 'apps', 'calculator', 'taskmgr'.
    """
    success = am.execute_fastpath(target)
    return {"success": success, "target": target}


@server.tool()
def get_roadmap_stats() -> dict:
    """Inspect what applications and elements have been learned into the UI roadmap cache."""
    apps = {}
    for k, v in am.roadmap.map.items():
        apps[k] = len(v.get("elements", {}))
    return {"mapped_applications": apps, "total_apps": len(apps)}


@server.tool()
def system_prelearn(max_elements_per_app: int = 50) -> dict:
    """
    Scan all open windows and the Windows Taskbar to discover and index interactive controls
    into ui_roadmap.json upfront so the AI has pre-learned desktop knowledge.
    """
    return am.run_system_prelearn(max_elements_per_app=max_elements_per_app)



@server.tool()
def snap_window(window_search: str, side: str = "left") -> dict:
    """
    Snap a window to screen halves or quadrants ('left', 'right', 'top', 'bottom', 'center', 'full').
    """
    success = am.snap_window(window_search, side=side)
    return {"status": "snapped" if success else "failed", "window": window_search, "side": side}


@server.tool()
def maximize_window(window_search: str) -> dict:
    """Maximize a target application window."""
    success = am.maximize_window(window_search)
    return {"status": "maximized" if success else "failed", "window": window_search}


@server.tool()
def minimize_window(window_search: str) -> dict:
    """Minimize a target application window."""
    success = am.minimize_window(window_search)
    return {"status": "minimized" if success else "failed", "window": window_search}


@server.tool()
def move_window(window_search: str, x: int, y: int, width: int, height: int) -> dict:
    """Reposition and resize a target application window."""
    success = am.move_window(window_search, x, y, width, height)
    return {"status": "moved" if success else "failed", "window": window_search, "x": x, "y": y, "width": width, "height": height}


@server.tool()
def clipboard_paste(text: str) -> dict:
    """
    Instantly paste multi-line or long text (0.5 ms) into the focused field via clipboard and Ctrl+V.
    """
    success = am.clipboard_paste(text)
    return {"status": "pasted" if success else "failed", "length": len(text)}


@server.tool()
def clipboard_get() -> dict:
    """Read the current plain text stored on the Windows clipboard."""
    text = am.get_clipboard_text()
    return {"text": text, "length": len(text)}


@server.tool()
def record_current_element(custom_name: str = "") -> dict:
    """
    Record on Hover: inspects the element currently under the mouse cursor
    and persists it into the spatial roadmap cache (ui_roadmap.json) with responsive anchors.
    """
    return am.record_element_at_cursor(custom_name=custom_name)


@server.tool()
def auto_record_window(window_search: str = "", move_cursor: bool = True, max_elements: int = 150) -> dict:
    """
    Automatically discovers controls in a window, glides the mouse cursor over each
    one with human-like Bézier motion to visually verify, and persists coordinates into ui_roadmap.json.
    """
    return am.auto_record_window(window_search=window_search, move_cursor=move_cursor, max_elements=max_elements)


@server.tool()
def deep_dive_app(window_search: str = "", max_depth: int = 15, max_elements: int = 500) -> dict:
    """
    Exhaustive Deep Dive: Inspects every menu command (legacy Win32 and modern),
    toolbar, input field, and accelerator in an application, indexing all into ui_roadmap.json.
    """
    return am.deep_dive_app(window_search=window_search, max_depth=max_depth, max_elements=max_elements)




@server.tool()
def wait_for_window(window_search: str, timeout: float = 3.0) -> dict:
    """
    Poll until a target window appears and becomes visible.
    Avoids arbitrary sleep delays in AI agent execution.
    """
    w = am.wait_for_window(window_search, timeout=timeout)
    if w:
        return {"status": "found", "window": w}
    return {"status": "timeout", "error": f"Window {window_search!r} did not appear within {timeout}s"}


@server.tool()
def wait_for_element(element_name: str, window_search: str = "", timeout: float = 3.0) -> dict:
    """
    Poll until a specific UI control/button is ready and rendered.
    """
    el = am.wait_for_element(element_name, window_search=window_search, timeout=timeout)
    if el:
        return {"status": "found", "element": el}
    return {"status": "timeout", "error": f"Element {element_name!r} not found within {timeout}s"}


@server.tool()
def wait_and_click(element_name: str, window_search: str = "", timeout: float = 3.0, instant: bool = True) -> dict:
    """
    Wait for an element to appear and click it in one atomic action.
    """
    return am.wait_and_click(element_name, window_search=window_search, timeout=timeout, instant=instant)


@server.tool()
def execute_action(action: str) -> dict:
    """
    Execute a multi-step desktop workflow serialized as a single string.
    Format: "open:notepad | type:Hello | hotkey:ctrl+s | fill:File name:, mynote.txt | key:enter"
    Supports: open, focus, click, doubleclick, rightclick, type, fill, key/hotkey, drag, wait, snap.
    Zero-token execution for full automated sequences!
    """
    return am.execute_action(action)


@server.tool()
def save_action(name: str, action: str) -> dict:
    """
    Save or update a named reusable action pipeline string into saved_actions.json.
    """
    return am.save_action(name, action)


@server.tool()
def list_saved_actions() -> dict:
    """
    List all saved reusable desktop action pipelines.
    """
    return {"actions": am.load_saved_actions()}


def main():
    server.run()


if __name__ == "__main__":
    main()
