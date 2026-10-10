from deskdriver.core.desktop import ensure_desktop, attach_thread_desktop, init_com
from deskdriver.core.mouse import (
    get_mouse_position,
    move_mouse,
    mouse_click,
    move_and_click,
)
from deskdriver.core.keyboard import press_hotkey, type_text, COMMON_HOTKEYS

__all__ = [
    "ensure_desktop",
    "attach_thread_desktop",
    "init_com",
    "get_mouse_position",
    "move_mouse",
    "mouse_click",
    "move_and_click",
    "press_hotkey",
    "type_text",
    "COMMON_HOTKEYS",
]

