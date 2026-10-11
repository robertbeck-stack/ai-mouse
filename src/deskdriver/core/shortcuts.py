"""
Keyboard shortcut hints embedded in control names, e.g. 'Bold (Ctrl+B)' or 'Media Alt+M'.
Pure text parsing with no dependencies, so every layer can use it.
"""

import re

# Regex to detect embedded shortcut hints like (Ctrl+S), (Ctrl+Shift+N), (Alt+F4), (F5)
SHORTCUT_REGEX = re.compile(
    r"\(((?:Ctrl|Alt|Shift)[^\)]*|F\d{1,2})\)",
    re.IGNORECASE,
)

# A trailing accelerator without parentheses, as Qt menus report them: 'Media Alt+M'
TRAILING_SHORTCUT_REGEX = re.compile(r"^(.*?\S)\s+((?:ctrl|alt|shift|win)(?:\+[^\s+]+)+)$", re.IGNORECASE)


def _tidy_keys(shortcut: str) -> str:
    """'alt+l' -> 'Alt+L', 'ctrl+shift+n' -> 'Ctrl+Shift+N'."""
    return "+".join(k.capitalize() if len(k) > 1 else k.upper() for k in shortcut.split("+"))


def extract_shortcut_from_name(name: str, fallback_shortcut: str = "") -> tuple[str, str]:
    """
    Extract embedded shortcut from a control name.
    Example: 'Collapse tabs (Ctrl+Shift+L)' -> ('Collapse tabs', 'Ctrl+Shift+L')
    Example: 'Bold (Ctrl+B)' -> ('Bold', 'Ctrl+B')
    Example: 'Playback Alt+l' -> ('Playback', 'Alt+L')
    """
    if not name:
        return "", fallback_shortcut

    match = SHORTCUT_REGEX.search(name)
    if match:
        extracted = match.group(1).strip()
        # Clean the name of the hint: "(Ctrl+...)" and "(F5)" alike
        clean_name = re.sub(r"\s+", " ", SHORTCUT_REGEX.sub("", name)).strip()
        return clean_name or name, extracted

    match = TRAILING_SHORTCUT_REGEX.match(name.strip())
    if match:
        return match.group(1), _tidy_keys(match.group(2))

    return name, fallback_shortcut
