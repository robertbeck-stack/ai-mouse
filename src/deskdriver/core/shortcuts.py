"""
Keyboard shortcut hints embedded in control names, e.g. 'Bold (Ctrl+B)'.
Pure text parsing with no dependencies, so every layer can use it.
"""

import re

# Regex to detect embedded shortcut hints like (Ctrl+S), (Ctrl+Shift+N), (Alt+F4), (F5)
SHORTCUT_REGEX = re.compile(
    r"\(((?:Ctrl|Alt|Shift)[^\)]*|F\d{1,2})\)",
    re.IGNORECASE,
)


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
