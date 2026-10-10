"""
Windows enumeration, bounding boxes, and reliable foreground activation.
"""

import ctypes
from ctypes import wintypes
import time
from ai_mouse.core.desktop import ensure_desktop

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


def focus_window(hwnd_or_title: int | str) -> bool:
    """Bring a window to the foreground reliably using AttachThreadInput and SW_RESTORE."""
    ensure_desktop()
    target_hwnd = None
    if isinstance(hwnd_or_title, int):
        target_hwnd = hwnd_or_title
    else:
        wins = list_windows()
        q = str(hwnd_or_title).lower()
        for w in wins:
            if q in w["title"].lower():
                target_hwnd = w["hwnd"]
                break

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
