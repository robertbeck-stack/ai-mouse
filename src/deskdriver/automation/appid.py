"""
Application identity: which program a window belongs to.

Roadmap data is keyed by the program's executable ("notepad.exe"), not by window
titles, which change with the open document, browser tab or Windows language and
leak personal data. Special cases:

- UWP apps (Settings, Calculator, Store) all live in ApplicationFrameHost.exe
  frames; the real app is the process behind the frame's CoreWindow.
- Shared host executables (explorer.exe is File Explorer, the taskbar and the
  desktop) are qualified with the window class: "explorer.exe#shell_traywnd".
- Owned windows (dialogs such as Notepad's "Page setup") get their own surface
  under the owning app: "notepad.exe/page setup", since their controls are laid
  out relative to the dialog, not the main window.
- If the process can't be opened (elevated / protected), the window class is used.
"""

import ctypes
import os
import re
import time
from ctypes import wintypes
from dataclasses import dataclass
from functools import lru_cache

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GA_ROOT = 2
GW_OWNER = 4

UWP_FRAME_CLASS = "ApplicationFrameWindow"
UWP_CORE_CLASS = "Windows.UI.Core.CoreWindow"

# Executables that host unrelated UIs; their windows are told apart by class.
SHARED_HOST_EXES = {
    "explorer.exe", "rundll32.exe", "dllhost.exe", "java.exe", "javaw.exe",
    "python.exe", "pythonw.exe", "mmc.exe", "applicationframehost.exe",
}
# The class that stands for the "main" app of a shared host (gets the bare exe key).
PRIMARY_HOST_CLASS = {"explorer.exe": "cabinetwclass"}

# Packaged apps often have no FileDescription, and some descriptions are odd.
DISPLAY_NAME_OVERRIDES = {
    "mspaint.exe": "Paint",
    "winstore.app.exe": "Microsoft Store",
    "systemsettings.exe": "Settings",
    "calculatorapp.exe": "Calculator",
    "snippingtool.exe": "Snipping Tool",
    "windowsterminal.exe": "Windows Terminal",
    "cmd.exe": "Command Prompt",
    "explorer.exe": "File Explorer",
    "explorer.exe#shell_traywnd": "Taskbar",
    "brave.exe": "Brave",
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "sechealthui.exe": "Windows Security",
}


def key_for(exe: str, window_class: str) -> str:
    """Storage key for a main window of `exe` with `window_class` (both case-insensitive)."""
    exe = (exe or "").lower()
    cls = (window_class or "").lower()
    if not exe:
        return f"#{cls}" if cls else "unknown"
    if exe in SHARED_HOST_EXES and PRIMARY_HOST_CLASS.get(exe) != cls:
        return f"{exe}#{cls}"
    return exe


def display_name_for(key: str, exe_path: str = "") -> str:
    """Human name for an app key."""
    if key in DISPLAY_NAME_OVERRIDES:
        return DISPLAY_NAME_OVERRIDES[key]
    exe = key.split("#", 1)[0].split("/", 1)[0]
    if exe in DISPLAY_NAME_OVERRIDES:
        return DISPLAY_NAME_OVERRIDES[exe]
    return exe_display_name(exe_path) or os.path.splitext(exe)[0].capitalize() or key


@dataclass(frozen=True)
class AppIdentity:
    key: str            # storage key, e.g. "notepad.exe", "explorer.exe#shell_traywnd", "notepad.exe/page setup"
    exe: str            # lower-case executable name, "" if unknown
    display_name: str   # human name, e.g. "Notepad"
    window_class: str
    surface: str = ""   # owned-window name for dialogs, "" for the main window

    @property
    def app_key(self) -> str:
        """Key of the owning application (without the dialog surface)."""
        return self.key.split("/", 1)[0]


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(wintypes.HWND(hwnd), buf, 256)
    return buf.value


def _title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(wintypes.HWND(hwnd))
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(wintypes.HWND(hwnd), buf, length + 1)
    return buf.value.strip()


def _pid(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return pid.value


def process_image_path(pid: int) -> str:
    """Full executable path of a process, or "" if it can't be opened."""
    hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hproc:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        kernel32.CloseHandle(hproc)


@lru_cache(maxsize=256)
def exe_display_name(exe_path: str) -> str:
    """FileDescription from the executable's version info ("Notepad"), or "" if absent."""
    if not exe_path:
        return ""
    try:
        import win32api
        langs = win32api.GetFileVersionInfo(exe_path, "\\VarFileInfo\\Translation")
        for lang, codepage in langs or []:
            desc = win32api.GetFileVersionInfo(exe_path, f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileDescription")
            if desc and desc.strip():
                return desc.strip()
    except Exception:
        pass
    return ""


def _uwp_app_pid(frame_hwnd: int) -> int | None:
    """PID of the UWP app hosted in an ApplicationFrameWindow."""
    frame_pid = _pid(frame_hwnd)
    found: list[int] = []

    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def child_cb(hwnd, _):
        if _class_name(hwnd) == UWP_CORE_CLASS:
            pid = _pid(hwnd)
            if pid and pid != frame_pid:
                found.append(pid)
                return False
        return True

    user32.EnumChildWindows(wintypes.HWND(frame_hwnd), enum_proc(child_cb), 0)
    if found:
        return found[0]

    # Minimized / suspended apps detach their CoreWindow into a top-level window
    # with the same title.
    title = _title(frame_hwnd)
    if title:
        def top_cb(hwnd, _):
            if _class_name(hwnd) == UWP_CORE_CLASS and _title(hwnd) == title:
                pid = _pid(hwnd)
                if pid and pid != frame_pid:
                    found.append(pid)
                    return False
            return True

        user32.EnumWindows(enum_proc(top_cb), 0)
    return found[0] if found else None


def surface_name(title: str) -> str:
    """Stable name for a dialog surface: lower-case title without digits or file names."""
    t = re.sub(r"\d+", "", title.lower())
    t = re.sub(r"\s+", " ", t).strip(" -–—:")
    return t[:40] or "dialog"


@lru_cache(maxsize=512)
def _identify(hwnd: int, pid: int, cls: str, owner: int) -> AppIdentity:
    app_pid = pid
    if cls == UWP_FRAME_CLASS:
        app_pid = _uwp_app_pid(hwnd) or pid

    exe_path = process_image_path(app_pid)
    exe = os.path.basename(exe_path).lower()
    key = key_for(exe, cls)
    display = display_name_for(key, exe_path)

    surface = ""
    if owner and user32.IsWindowVisible(wintypes.HWND(owner)):
        owner_id = identify_window(owner)
        surface = surface_name(_title(hwnd))
        return AppIdentity(
            key=f"{owner_id.app_key}/{surface}",
            exe=owner_id.exe,
            display_name=owner_id.display_name,
            window_class=cls,
            surface=surface,
        )
    return AppIdentity(key=key, exe=exe, display_name=display, window_class=cls)


def identify_window(hwnd: int) -> AppIdentity:
    """Identity of the application owning a window (any child hwnd is resolved to its top level)."""
    root = user32.GetAncestor(wintypes.HWND(hwnd), GA_ROOT) or hwnd
    root = int(root)
    owner = int(user32.GetWindow(wintypes.HWND(root), GW_OWNER) or 0)
    # Cache on (hwnd, pid, class, owner) so a recycled hwnd is not mistaken for its predecessor.
    # The title is deliberately not part of the identity.
    return _identify(root, _pid(root), _class_name(root), owner)


def app_matches(identity: AppIdentity, query: str) -> bool:
    """Does a user-facing name ("notepad", "Notepad", "notepad.exe", "settings") refer to this app?"""
    q = query.strip().lower()
    if not q:
        return False
    names = {identity.key.lower(), identity.app_key.lower(), identity.display_name.lower()}
    # The bare exe name means the app's own windows, not another window class that
    # shares the exe ("explorer" is File Explorer, not explorer.exe#shell_traywnd)
    if identity.app_key == identity.exe:
        names |= {identity.exe, os.path.splitext(identity.exe)[0]}
    return q in names


def find_app_window(query: str, windows: list[dict]) -> dict | None:
    """
    First window that belongs to the app named by `query` ("notepad", "notepad.exe",
    "Settings", a full key), falling back to a window whose title contains it.
    """
    q = (query or "").strip().lower()
    if not q:
        return None
    for w in windows:
        if app_matches(identify_window(w["hwnd"]), q):
            return w
    for w in windows:
        if q in w["title"].lower():
            return w
    return None


def wait_for_app_window(query: str, timeout: float = 3.0, poll_interval: float = 0.05) -> dict | None:
    """Poll until a window of the named app (or with that title) exists; None on timeout."""
    from deskdriver.automation.windows import list_windows

    deadline = time.time() + timeout
    while True:
        win = find_app_window(query, list_windows())
        if win or time.time() >= deadline:
            return win
        time.sleep(poll_interval)
