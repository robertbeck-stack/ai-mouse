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
from deskdriver.automation.draw import draw_strokes, window_geometry
from deskdriver.automation.uia import (
    get_element_under_cursor,
    get_element_at,
)
from deskdriver.navigation.roadmap import roadmap
from deskdriver.navigation.interact import (
    list_clickable_elements,  # scans and learns into the roadmap
    fast_click_element,
    fill_input,
    record_element_at_cursor,
    auto_record_window,
    wait_for_element,
    wait_and_click,
)
from deskdriver.navigation.deepdive import deep_dive_app
from deskdriver.navigation.fastpaths import execute_fastpath
from deskdriver.navigation.prelearn import run_system_prelearn
from deskdriver.workflows.actions import (
    execute_action,
    save_action,
    load_saved_actions,
    delete_action,
    parse_action_string,
)
from deskdriver.navigation.tree import build_application_tree
from deskdriver.workflows.recorder import (
    start_recording,
    stop_recording,
    get_recording_status,
    recorder,
)

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
    "draw_strokes",
    "window_geometry",

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
    "execute_action",
    "save_action",
    "load_saved_actions",
    "delete_action",
    "parse_action_string",
    "build_application_tree",
    "start_recording",
    "stop_recording",
    "get_recording_status",
    "recorder",
    "__version__",
]
