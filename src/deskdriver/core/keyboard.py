"""
Low-level Windows keyboard simulation using SendInput and keybd_event.
Supports hotkey combinations (Ctrl+S, Win+Shift+S, Alt+F4) and Unicode text typing.
"""

import ctypes
from ctypes import wintypes
import time
from deskdriver.core.desktop import ensure_desktop

user32 = ctypes.windll.user32

# Key event flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Standard Virtual Key codes mapping
VK_MAP = {
    "ctrl": 0x11,
    "control": 0x11,
    "shift": 0x10,
    "alt": 0x12,
    "menu": 0x12,
    "win": 0x5B,
    "windows": 0x5B,
    "cmd": 0x5B,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "backspace": 0x08,
    "space": 0x20,
    "delete": 0x2E,
    "del": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "printscreen": 0x2C,
    "prtscn": 0x2C,
    "snapshot": 0x2C,
    # F-keys
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}

# Universal shortcut mappings for common actions
COMMON_HOTKEYS = {
    "save": "ctrl+s",
    "copy": "ctrl+c",
    "paste": "ctrl+v",
    "cut": "ctrl+x",
    "undo": "ctrl+z",
    "redo": "ctrl+y",
    "select all": "ctrl+a",
    "select_all": "ctrl+a",
    "find": "ctrl+f",
    "search": "ctrl+f",
    "new tab": "ctrl+t",
    "new_tab": "ctrl+t",
    "close tab": "ctrl+w",
    "close_tab": "ctrl+w",
    "reopen tab": "ctrl+shift+t",
    "new window": "ctrl+n",
    "new_window": "ctrl+n",
    "reload": "ctrl+r",
    "refresh": "f5",
    "bookmark": "ctrl+d",
    "downloads": "ctrl+j",
    "history": "ctrl+h",
    "screenshot": "win+shift+s",
    "snip": "win+shift+s",
    "printscreen": "prtscn",
    "task manager": "ctrl+shift+esc",
    "lock": "win+l",
    "run": "win+r",
    "file explorer": "win+e",
    "minimize all": "win+d",
    "show desktop": "win+d",
}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]


def _get_vk_code(key_str: str) -> int:
    """Resolve key string to Windows Virtual Key code."""
    k = key_str.lower().strip()
    if k in VK_MAP:
        return VK_MAP[k]
    if len(k) == 1:
        # Single alphanumeric char (A-Z, 0-9)
        c = ord(k.upper())
        if (65 <= c <= 90) or (48 <= c <= 57):
            return c
    return 0


def press_hotkey(hotkey: str, delay: float = 0.05):
    """
    Press and release a key combination (e.g. 'ctrl+s', 'win+shift+s', 'alt+f4', 'enter')
    using atomic Windows SendInput.
    """
    ensure_desktop()
    parts = [p.strip() for p in hotkey.lower().replace("+", " ").split() if p.strip()]
    if not parts:
        return

    vk_codes = [_get_vk_code(p) for p in parts if _get_vk_code(p) > 0]
    if not vk_codes:
        return

    # 1. Key down in sequence
    for vk in vk_codes:
        inp = (INPUT * 1)(INPUT(type=1, ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        time.sleep(0.01)

    time.sleep(delay)

    # 2. Key up in reverse sequence
    for vk in reversed(vk_codes):
        inp = (INPUT * 1)(INPUT(type=1, ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        time.sleep(0.01)


def type_text(text: str, enter: bool = False, delay: float = 0.015):
    """
    Type Unicode text directly into the focused control using atomic Windows SendInput.
    Dispatches paired KeyDown and KeyUp events atomically to avoid dropped keys or stuck auto-repeat.
    """
    ensure_desktop()
    for char in text:
        code = ord(char)
        inputs = (INPUT * 2)(
            INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0)),
            INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)),
        )
        user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        if delay > 0:
            time.sleep(delay)

    if enter:
        time.sleep(0.04)
        press_hotkey("enter")
