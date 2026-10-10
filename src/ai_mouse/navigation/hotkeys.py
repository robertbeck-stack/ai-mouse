"""
Intelligent Shortcut Extraction and Standard Application Profiles.
Extracts shortcuts embedded in control names/tooltips and provides
built-in hotkey knowledge profiles for common Windows applications.
"""

import re

# Regex to detect embedded shortcut hints like (Ctrl+S), (Ctrl+Shift+N), (Alt+F4), (F5)
SHORTCUT_REGEX = re.compile(
    r"\(((?:Ctrl|Alt|Shift)[^\)]*|F\d{1,2})\)",
    re.IGNORECASE,
)

# Standard application hotkey profiles
APP_PROFILES = {
    "brave": {
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
    "chrome": {
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
    "notepad": {
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
    "explorer": {
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
}


def extract_shortcut_from_name(name: str, fallback_shortcut: str = "") -> tuple[str, str]:
    """
    Extract embedded shortcut from a control name.
    Example: 'Collapse tabs (Ctrl+Shift+L)' -> ('Collapse tabs', 'Ctrl+Shift+L')
    Example: 'Bold (Ctrl+B)' -> ('Bold', 'Ctrl+B')
    """
    if not name:
        return "", fallback_shortcut

    match = SHORTCUT_REGEX.search(name)
    if match:
        extracted = match.group(1).strip()
        # Clean the name of the trailing (Ctrl+...)
        clean_name = re.sub(r"\s*\((?:Ctrl|Alt|Shift)[^\)]*\)\s*", "", name, flags=re.IGNORECASE).strip()
        return clean_name or name, extracted

    # If UIA gave us an AccessKey like 'Alt, B' or 'Alt, F', but no accelerator
    if fallback_shortcut and not fallback_shortcut.startswith("Alt,"):
        return name, fallback_shortcut

    return name, fallback_shortcut


def get_app_hotkeys(app_name: str) -> dict[str, str]:
    """Retrieve known hotkey profile for a given application by name."""
    low = app_name.lower()
    for key, shortcuts in APP_PROFILES.items():
        if key in low:
            return shortcuts
    return {}

