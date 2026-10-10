"""
ai-mouse: Fast, human-like AI mouse controller and UI automation MCP server for Windows.
"""

from deskdriver.core.mouse import (
    get_mouse_position,
    move_mouse,
    mouse_click,
    move_and_click,
    mouse_scroll,
    drag_and_drop,
)
from deskdriver.core.keyboard import press_hotkey, type_text, COMMON_HOTKEYS
from deskdriver.automation.windows import list_windows, focus_window

from deskdriver.automation.uia import (
    get_element_under_cursor,
    get_element_at,
    list_clickable_elements,
)
from deskdriver.navigation.roadmap import fast_click_element, fill_input, roadmap
from deskdriver.navigation.fastpaths import execute_fastpath
from deskdriver.navigation.prelearn import run_system_prelearn

__version__ = "0.1.0"

__all__ = [
    "get_mouse_position",
    "move_mouse",
    "mouse_click",
    "move_and_click",
    "mouse_scroll",
    "drag_and_drop",
    "press_hotkey",
    "type_text",
    "COMMON_HOTKEYS",
    "list_windows",
    "focus_window",

    "get_element_under_cursor",
    "get_element_at",
    "list_clickable_elements",
    "fast_click_element",
    "fill_input",
    "roadmap",
    "execute_fastpath",
    "run_system_prelearn",
]

