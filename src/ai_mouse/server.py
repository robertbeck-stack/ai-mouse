"""
Model Context Protocol (MCP) Server for ai-mouse.
Exposes modular tools to AI agents.
"""

from mcp.server.mcpserver import MCPServer
import ai_mouse as am

server = MCPServer("ai-mouse")


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



def main():
    server.run()


if __name__ == "__main__":
    main()
