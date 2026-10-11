"""
Windows enumeration, bounding boxes, and reliable foreground activation.
"""

import ctypes
from ctypes import wintypes
import time
from deskdriver.core.desktop import ensure_desktop

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi

DWMWA_CLOAKED = 14


def is_window_cloaked(hwnd: int) -> bool:
    """True for windows DWM keeps visible-but-hidden (suspended UWP frames, other virtual desktops)."""
    cloaked = wintypes.DWORD(0)
    try:
        hr = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
        )
        return hr == 0 and cloaked.value != 0
    except Exception:
        return False


def list_windows() -> list[dict]:
    """List all open visible application windows on the desktop."""
    ensure_desktop()
    windows = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd) and not is_window_cloaked(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()

                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top

                if w > 20 and h > 20 and title not in ("Program Manager", ""):
                    windows.append({
                        "hwnd": int(hwnd),
                        "title": title,
                        "rect": {
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                            "width": w,
                            "height": h,
                        },
                    })
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return windows


def window_info(hwnd: int) -> dict:
    """{"hwnd", "title", "rect"} of a window, in the same shape list_windows() returns."""
    rect = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect))
    length = user32.GetWindowTextLengthW(wintypes.HWND(hwnd))
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(wintypes.HWND(hwnd), buff, length + 1)
    return {
        "hwnd": int(hwnd),
        "title": buff.value.strip(),
        "rect": {
            "left": rect.left,
            "top": rect.top,
            "right": rect.right,
            "bottom": rect.bottom,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        },
    }


def window_at(x: int, y: int) -> dict | None:
    """Top-level window under a screen point."""
    hwnd = user32.WindowFromPoint(wintypes.POINT(int(x), int(y)))
    if not hwnd:
        return None
    root = user32.GetAncestor(wintypes.HWND(hwnd), 2) or hwnd  # GA_ROOT
    return window_info(int(root))


def find_window_hwnd(hwnd_or_title: int | str) -> int | None:
    """Resolve an HWND or partial window title to an active HWND. An empty title means the foreground window."""
    if isinstance(hwnd_or_title, int):
        return hwnd_or_title if user32.IsWindow(hwnd_or_title) else None
    q = str(hwnd_or_title).lower().strip()
    if not q:
        return user32.GetForegroundWindow() or None
    for w in list_windows():
        if q in w["title"].lower():
            return w["hwnd"]
    return None


def focus_window(hwnd_or_title: int | str) -> bool:
    """Bring a window to the foreground reliably using AttachThreadInput and SW_RESTORE."""
    ensure_desktop()
    target_hwnd = find_window_hwnd(hwnd_or_title)
    if not target_hwnd:
        return False

    def in_front() -> bool:
        fg = user32.GetForegroundWindow()
        return bool(fg) and int(user32.GetAncestor(fg, 2) or fg) == int(target_hwnd)  # GA_ROOT

    try:
        if user32.IsIconic(target_hwnd):
            user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE (only when minimized, so maximized windows stay maximized)
        if in_front():
            return True

        for attempt in range(3):
            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
            cur_thread = kernel32.GetCurrentThreadId()
            # Windows only lets the process that received the last input event change
            # the foreground window. A background process (the MCP server, the
            # dashboard) earns that right by sending input: first a zero-length mouse
            # move, then an Alt tap (which can flash the old window's menu bar).
            if attempt == 1:
                user32.mouse_event(0x0001, 0, 0, 0, 0)  # MOUSEEVENTF_MOVE by (0, 0)
            elif attempt == 2:
                user32.keybd_event(0x12, 0, 0, 0)  # VK_MENU down
                user32.keybd_event(0x12, 0, 2, 0)  # VK_MENU up (KEYEVENTF_KEYUP)
            attached = fg_thread != cur_thread and user32.AttachThreadInput(cur_thread, fg_thread, True)
            try:
                user32.BringWindowToTop(target_hwnd)
                user32.SetForegroundWindow(target_hwnd)
            finally:
                if attached:
                    user32.AttachThreadInput(cur_thread, fg_thread, False)
            time.sleep(0.1)
            if in_front():
                return True
        # Report failure: clicks and keystrokes would land in whatever window is in front
        return False
    except Exception:
        return False


def maximize_window(hwnd_or_title: int | str) -> bool:
    """Maximize a window by HWND or partial title."""
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False
    return bool(user32.ShowWindow(hwnd, 3))  # SW_MAXIMIZE = 3


def minimize_window(hwnd_or_title: int | str) -> bool:
    """Minimize a window by HWND or partial title."""
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False
    return bool(user32.ShowWindow(hwnd, 6))  # SW_MINIMIZE = 6


def restore_window(hwnd_or_title: int | str) -> bool:
    """Restore a window to its normal position and size."""
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False
    return bool(user32.ShowWindow(hwnd, 9))  # SW_RESTORE = 9


def move_window(hwnd_or_title: int | str, x: int, y: int, width: int, height: int) -> bool:
    """Reposition and resize a window."""
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False
    restore_window(hwnd)
    return bool(user32.MoveWindow(hwnd, int(x), int(y), int(width), int(height), True))


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def get_window_monitor_work_area(hwnd: int) -> dict:
    """Get the usable desktop bounds (excluding taskbar) for the monitor displaying this window."""
    try:
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        hmon = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST = 2
        if hmon and user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            r = mi.rcWork
            return {
                "left": r.left,
                "top": r.top,
                "right": r.right,
                "bottom": r.bottom,
                "width": r.right - r.left,
                "height": r.bottom - r.top,
            }
    except Exception:
        pass

    # Fallback to primary work area
    rect = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA = 0x0030
    return {
        "left": rect.left,
        "top": rect.top,
        "right": rect.right,
        "bottom": rect.bottom,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }


def snap_window(hwnd_or_title: int | str, side: str = "left") -> bool:
    """
    Snap a window to screen halves or layout quadrants on its current monitor.
    Supports multi-monitor setups automatically.
    Sides: 'left', 'right', 'top', 'bottom', 'center', 'full', 'minimize'.
    """
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False

    s = side.lower().strip()
    if s in ("full", "maximize"):
        return maximize_window(hwnd)
    if s in ("minimize", "min"):
        minimize_window(hwnd)
        return bool(user32.IsIconic(hwnd))

    restore_window(hwnd)

    # Multi-monitor work area detection (excludes taskbar on that specific display)
    work = get_window_monitor_work_area(hwnd)
    sw = work["width"]
    sh = work["height"]
    sx = work["left"]
    sy = work["top"]

    if s == "left":
        x, y, w, h = sx, sy, sw // 2, sh
    elif s == "right":
        x, y, w, h = sx + sw // 2, sy, sw - (sw // 2), sh
    elif s == "top":
        x, y, w, h = sx, sy, sw, sh // 2
    elif s == "bottom":
        x, y, w, h = sx, sy + sh // 2, sw, sh - (sh // 2)
    elif s == "center":
        w, h = int(sw * 0.7), int(sh * 0.7)
        x = sx + (sw - w) // 2
        y = sy + (sh - h) // 2
    else:
        return False

    return bool(user32.MoveWindow(hwnd, x, y, w, h, True))


def wait_for_window(
    hwnd_or_title: int | str, timeout: float = 3.0, poll_interval: float = 0.05
) -> dict | None:
    """
    Poll until a target window appears and becomes visible, or timeout expires.
    Eliminates arbitrary sleep delays in agent execution.
    Returns window dict (with hwnd, title, rect) or None on timeout.
    """
    start = time.time()
    q = str(hwnd_or_title).lower().strip()
    while time.time() - start < timeout:
        for w in list_windows():
            if isinstance(hwnd_or_title, int):
                if w["hwnd"] == hwnd_or_title:
                    return w
            elif q in w["title"].lower():
                return w
        time.sleep(poll_interval)
    return None




def foreground_root() -> int:
    """Top-level window that currently has the foreground (0 if none)."""
    fg = user32.GetForegroundWindow()
    return int(user32.GetAncestor(fg, 2) or fg or 0)  # GA_ROOT


def client_rect(hwnd: int) -> dict:
    """The window's client area (no title bar / borders) in screen coordinates."""
    rect = wintypes.RECT()
    user32.GetClientRect(wintypes.HWND(hwnd), ctypes.byref(rect))
    origin = wintypes.POINT(0, 0)
    user32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(origin))
    return {
        "left": origin.x,
        "top": origin.y,
        "right": origin.x + rect.right,
        "bottom": origin.y + rect.bottom,
        "width": rect.right,
        "height": rect.bottom,
    }
