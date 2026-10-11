"""
Intelligent Shortcut Extraction and Standard Application Profiles.
Extracts shortcuts embedded in control names/tooltips and provides
built-in hotkey knowledge profiles for common Windows applications.
"""

from deskdriver.core.shortcuts import SHORTCUT_REGEX, extract_shortcut_from_name

__all__ = ["APP_PROFILES", "SHORTCUT_REGEX", "extract_shortcut_from_name", "get_app_hotkeys"]

# Standard application hotkey profiles
APP_PROFILES = {
    "brave.exe": {
        "new tab": "Ctrl+T",
        "close tab": "Ctrl+W",
        "reopen closed tab": "Ctrl+Shift+T",
        "new window": "Ctrl+N",
        "new private window": "Ctrl+Shift+N",
        "reload": "Ctrl+R",
        "hard reload": "Ctrl+Shift+R",
        "address and search bar": "Ctrl+L",
        "find in page": "Ctrl+F",
        "downloads": "Ctrl+J",
        "history": "Ctrl+H",
        "bookmarks manager": "Ctrl+Shift+O",
        "bookmark tab": "Ctrl+D",
        "next tab": "Ctrl+Tab",
        "previous tab": "Ctrl+Shift+Tab",
        "zoom in": "Ctrl+Plus",
        "zoom out": "Ctrl+Minus",
        "reset zoom": "Ctrl+0",
        "devtools": "F12",
        "view source": "Ctrl+U",
        "print": "Ctrl+P",
        "save page as": "Ctrl+S",
    },
    "chrome.exe": {
        "new tab": "Ctrl+T",
        "close tab": "Ctrl+W",
        "reopen closed tab": "Ctrl+Shift+T",
        "new window": "Ctrl+N",
        "new incognito window": "Ctrl+Shift+N",
        "reload": "Ctrl+R",
        "address and search bar": "Ctrl+L",
        "find": "Ctrl+F",
        "downloads": "Ctrl+J",
        "history": "Ctrl+H",
        "bookmarks": "Ctrl+Shift+O",
        "bookmark tab": "Ctrl+D",
        "next tab": "Ctrl+Tab",
        "previous tab": "Ctrl+Shift+Tab",
        "devtools": "F12",
        "print": "Ctrl+P",
    },
    "notepad.exe": {
        "new file": "Ctrl+N",
        "new window": "Ctrl+Shift+N",
        "open": "Ctrl+O",
        "save": "Ctrl+S",
        "save as": "Ctrl+Shift+S",
        "close tab": "Ctrl+W",
        "find": "Ctrl+F",
        "find next": "F3",
        "find previous": "Shift+F3",
        "replace": "Ctrl+H",
        "go to line": "Ctrl+G",
        "select all": "Ctrl+A",
        "time/date": "F5",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "cut": "Ctrl+X",
        "copy": "Ctrl+C",
        "paste": "Ctrl+V",
        "zoom in": "Ctrl+Plus",
        "zoom out": "Ctrl+Minus",
        "reset zoom": "Ctrl+0",
    },
    "explorer.exe": {
        "new folder": "Ctrl+Shift+N",
        "new window": "Ctrl+N",
        "close window": "Ctrl+W",
        "search box": "Ctrl+F",
        "address bar": "Alt+D",
        "refresh": "F5",
        "rename": "F2",
        "select all": "Ctrl+A",
        "delete": "Delete",
        "permanent delete": "Shift+Delete",
        "properties": "Alt+Enter",
        "back": "Alt+Left",
        "forward": "Alt+Right",
        "up one folder": "Alt+Up",
    },
    "vlc.exe": {
        "play/pause": "Space",
        "stop": "S",
        "next": "N",
        "previous": "P",
        "fullscreen": "F",
        "mute": "M",
        "volume up": "Ctrl+Up",
        "volume down": "Ctrl+Down",
        "open file": "Ctrl+O",
        "jump to specific time": "Ctrl+T",
        "take snapshot": "Shift+S",
        "playlist": "Ctrl+L",
        "media information": "Ctrl+I",
        "effects and filters": "Ctrl+E",
        "preferences": "Ctrl+P",
        "quit": "Ctrl+Q",
    },
    "polytopia.exe": {
        "end turn / confirm": "Space",
        "cycle next unit": "Tab",
        "game menu / cancel": "Esc",
        "zoom in": "+",
        "zoom out": "-",
        "pan camera up": "W",
        "pan camera left": "A",
        "pan camera down": "S",
        "pan camera right": "D",
        "quick confirm": "Enter",
    },
}


def get_app_hotkeys(app_name: str) -> dict[str, str]:
    """Known hotkey profile for an app, by key or name ("notepad.exe", "Notepad", "notepad")."""
    low = app_name.strip().lower()
    for key, shortcuts in APP_PROFILES.items():
        stem = key.removesuffix(".exe")
        if low in (key, stem) or stem in low:
            return shortcuts
    return {}
