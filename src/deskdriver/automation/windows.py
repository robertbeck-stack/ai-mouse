"""
Windows enumeration, bounding boxes, and reliable foreground activation.
"""

import ctypes
from ctypes import wintypes
import time
from deskdriver.core.desktop import ensure_desktop

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def list_windows() -> list[dict]:
    """List all open visible application windows on the desktop."""
    ensure_desktop()
    windows = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
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


def find_window_hwnd(hwnd_or_title: int | str) -> int | None:
    """Resolve an HWND or partial window title to an active HWND."""
    if isinstance(hwnd_or_title, int):
        return hwnd_or_title if user32.IsWindow(hwnd_or_title) else None
    q = str(hwnd_or_title).lower().strip()
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

    try:
        fg_hwnd = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
        cur_thread = kernel32.GetCurrentThreadId()

        if fg_thread != cur_thread:
            user32.AttachThreadInput(cur_thread, fg_thread, True)

        user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(target_hwnd)
        user32.SetForegroundWindow(target_hwnd)

        if fg_thread != cur_thread:
            user32.AttachThreadInput(cur_thread, fg_thread, False)

        time.sleep(0.15)
        return True
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


def snap_window(hwnd_or_title: int | str, side: str = "left") -> bool:
    """
    Snap a window to screen halves or layout quadrants.
    Supports: 'left', 'right', 'top', 'bottom', 'center', 'full'.
    """
    ensure_desktop()
    hwnd = find_window_hwnd(hwnd_or_title)
    if not hwnd:
        return False

    # Get primary display usable work area (excluding taskbar)
    rect = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA = 0x0030
    sw = rect.right - rect.left
    sh = rect.bottom - rect.top
    sx = rect.left
    sy = rect.top

    s = side.lower().strip()
    if s in ("full", "maximize"):
        return maximize_window(hwnd)

    restore_window(hwnd)
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

