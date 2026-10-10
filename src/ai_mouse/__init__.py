"""
ai-mouse: Fast, human-like AI mouse controller and UI automation MCP server for Windows.
"""

from ai_mouse.core.mouse import (
    get_mouse_position,
    move_mouse,
    mouse_click,
    move_and_click,
)
from ai_mouse.automation.windows import list_windows, focus_window
from ai_mouse.automation.uia import (
    get_element_under_cursor,
    get_element_at,
    list_clickable_elements,
)
from ai_mouse.navigation.roadmap import fast_click_element, roadmap
from ai_mouse.navigation.fastpaths import execute_fastpath

__version__ = "0.1.0"

__all__ = [
    "get_mouse_position",
    "move_mouse",
    "mouse_click",
    "move_and_click",
    "list_windows",
    "focus_window",
    "get_element_under_cursor",
    "get_element_at",
    "list_clickable_elements",
    "fast_click_element",
    "roadmap",
    "execute_fastpath",
]
