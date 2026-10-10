"""
DeskDriver: The native desktop automation and spatial operating layer for AI agents.
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
from deskdriver.core.clipboard import (
    get_clipboard_text,
    set_clipboard_text,
    clipboard_paste,
    clipboard_copy,
)
from deskdriver.automation.windows import (
    list_windows,
    focus_window,
    maximize_window,
    minimize_window,
    restore_window,
    move_window,
    snap_window,
    wait_for_window,
)
from deskdriver.automation.uia import (
    get_element_under_cursor,
    get_element_at,
    list_clickable_elements,
)
from deskdriver.navigation.roadmap import (
    fast_click_element,
    fill_input,
    record_element_at_cursor,
    auto_record_window,
    wait_for_element,
    wait_and_click,
    roadmap,
)
from deskdriver.navigation.deepdive import deep_dive_app
from deskdriver.navigation.fastpaths import execute_fastpath
from deskdriver.navigation.prelearn import run_system_prelearn

__version__ = "0.2.0"

__all__ = [
    # Mouse
    "get_mouse_position",
    "move_mouse",
    "mouse_click",
    "move_and_click",
    "mouse_scroll",
    "drag_and_drop",

    # Keyboard & Clipboard
    "press_hotkey",
    "type_text",
    "COMMON_HOTKEYS",
    "get_clipboard_text",
    "set_clipboard_text",
    "clipboard_paste",
    "clipboard_copy",

    # Windows Management & Snapping
    "list_windows",
    "focus_window",
    "maximize_window",
    "minimize_window",
    "restore_window",
    "move_window",
    "snap_window",
    "wait_for_window",

    # UIA Inspection & Roadmap
    "get_element_under_cursor",
    "get_element_at",
    "list_clickable_elements",
    "fast_click_element",
    "fill_input",
    "record_element_at_cursor",
    "auto_record_window",
    "wait_for_element",
    "wait_and_click",
    "roadmap",
    "deep_dive_app",
    "execute_fastpath",
    "run_system_prelearn",
]
