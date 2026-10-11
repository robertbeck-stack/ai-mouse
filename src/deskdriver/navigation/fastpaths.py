"""
Windows direct URI and deep-link fastpaths for zero-click navigation.
"""

import json
import os
import time

from deskdriver.automation.windows import list_windows, focus_window
from deskdriver.paths import LOCAL_FASTPATHS_FILE

FASTPATHS = {
    "system": "ms-settings:system",
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "notifications": "ms-settings:notifications",
    "power": "ms-settings:powersleep",
    "battery": "ms-settings:batterysaver",
    "storage": "ms-settings:storagesense",
    "bluetooth": "ms-settings:bluetooth",
    "network": "ms-settings:network",
    "wifi": "ms-settings:network-wifi",
    "vpn": "ms-settings:network-vpn",
    "personalization": "ms-settings:personalization",
    "background": "ms-settings:personalization-background",
    "colors": "ms-settings:personalization-colors",
    "themes": "ms-settings:themes",
    "lockscreen": "ms-settings:lockscreen",
    "apps": "ms-settings:appsfeatures",
    "defaultapps": "ms-settings:defaultapps",
    "startup": "ms-settings:startupapps",
    "accounts": "ms-settings:yourinfo",
    "time": "ms-settings:dateandtime",
    "region": "ms-settings:regionformatting",
    "language": "ms-settings:keyboard",
    "gaming": "ms-settings:gaming-gamebar",
    "accessibility": "ms-settings:easeofaccess-display",
    "mouse": "ms-settings:mousetouchpad",
    "update": "ms-settings:windowsupdate",
    "security": "windowsdefender:",
    "about": "ms-settings:about",
    "calculator": "ms-calculator:",  # "calc:" is a no-op on current Windows 11
    "explorer": "explorer.exe",
    "taskmgr": "taskmgr.exe",
    "notepad": "notepad.exe",
    "paint": "mspaint.exe",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
}


def _load_local_fastpaths() -> dict[str, str]:
    """Extra fastpaths for this machine (installed games, portable apps) from local_fastpaths.json."""
    try:
        data = json.loads(LOCAL_FASTPATHS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k).lower(): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


FASTPATHS.update(_load_local_fastpaths())


# Title of the window a URI opens, used when the app reuses an already-open window
# (e.g. a second ms-settings: link navigates the existing Settings window).
WINDOW_HINTS = {
    "ms-settings:": "settings",
    "windowsdefender:": "windows security",
    "ms-windows-store:": "microsoft store",
    "ms-calculator:": "calculator",
}


def _window_hint(uri: str) -> str:
    low = uri.lower()
    for prefix, title in WINDOW_HINTS.items():
        if low.startswith(prefix):
            return title
    return ""


def _bring_launched_window_to_front(before: set[int], hint: str, timeout: float) -> int | None:
    """
    Wait for the window the launch produced and focus it. Windows does not let a
    background process (the dashboard, the MCP server) hand focus to the app it
    started, so without this the window opens behind whatever is in front.
    """
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.1)
        wins = list_windows()
        new = [w for w in wins if w["hwnd"] not in before]
        if hint:
            new = [w for w in new if hint in w["title"].lower()] or new
        if new:
            focus_window(new[0]["hwnd"])
            return new[0]["hwnd"]
        # Reused window: give the app a moment to navigate it, then focus it.
        if hint and time.time() - start > 0.6:
            existing = next((w for w in wins if hint in w["title"].lower()), None)
            if existing:
                focus_window(existing["hwnd"])
                return existing["hwnd"]
    return None


def execute_fastpath(target: str, bring_to_front: bool = True, timeout: float = 4.0) -> bool:
    """
    Execute a direct OS URI / program shortcut if recognized.
    Returns False for unknown targets or when Windows refuses to launch it.
    """
    key = target.strip().lower()
    uri = FASTPATHS.get(key)
    if not uri:
        return False

    before = {w["hwnd"] for w in list_windows()} if bring_to_front else set()
    try:
        os.startfile(uri)  # ShellExecute: no cmd.exe parsing of the URI or path
    except OSError:
        return False

    if bring_to_front:
        _bring_launched_window_to_front(before, _window_hint(uri), timeout)
    return True
