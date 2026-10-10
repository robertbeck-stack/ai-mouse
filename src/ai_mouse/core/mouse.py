"""
Low-level cursor positioning, human-like Bézier movement, and click dispatching.
"""

import ctypes
from ctypes import wintypes
import time
import math
import random
from ai_mouse.core.desktop import ensure_desktop

user32 = ctypes.windll.user32

# Mouse Win32 flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040


def get_mouse_position() -> tuple[int, int]:
    """Get the current screen coordinates (x, y) of the cursor."""
    ensure_desktop()
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def _cubic_bezier(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Cubic bezier curve interpolation."""
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


def move_mouse(x: int, y: int, smooth: bool = True, duration: float = 0.25):
    """
    Move mouse to (x, y). If smooth is True, generates a natural human-like Bézier curve.
    """
    ensure_desktop()
    start_x, start_y = get_mouse_position()

    if start_x == x and start_y == y:
        return

    if not smooth:
        user32.SetCursorPos(int(x), int(y))
        return

    dist = math.hypot(x - start_x, y - start_y)
    if dist < 5:
        user32.SetCursorPos(int(x), int(y))
        return

    steps = max(15, min(60, int(dist / 15)))
    delay = max(0.003, duration / steps)

    mid_x = (start_x + x) / 2
    mid_y = (start_y + y) / 2
    dev = min(100.0, dist * 0.2)
    ctrl1_x = start_x + (mid_x - start_x) * 0.6 + random.uniform(-dev, dev)
    ctrl1_y = start_y + (mid_y - start_y) * 0.6 + random.uniform(-dev, dev)
    ctrl2_x = mid_x + (x - mid_x) * 0.4 + random.uniform(-dev, dev)
    ctrl2_y = mid_y + (y - mid_y) * 0.4 + random.uniform(-dev, dev)

    for i in range(1, steps + 1):
        t = i / steps
        t_ease = t * t * (3 - 2 * t)  # Smoothstep easing
        cx = int(_cubic_bezier(start_x, ctrl1_x, ctrl2_x, x, t_ease))
        cy = int(_cubic_bezier(start_y, ctrl1_y, ctrl2_y, y, t_ease))
        user32.SetCursorPos(cx, cy)
        time.sleep(delay)

    user32.SetCursorPos(int(x), int(y))


def mouse_click(button: str = "left", clicks: int = 1, interval: float = 0.08):
    """Perform a mouse click (left, right, middle) with optional double click."""
    ensure_desktop()
    btn = button.lower().strip()

    down_flag = MOUSEEVENTF_LEFTDOWN
    up_flag = MOUSEEVENTF_LEFTUP
    if btn == "right":
        down_flag = MOUSEEVENTF_RIGHTDOWN
        up_flag = MOUSEEVENTF_RIGHTUP
    elif btn == "middle":
        down_flag = MOUSEEVENTF_MIDDLEDOWN
        up_flag = MOUSEEVENTF_MIDDLEUP

    for i in range(clicks):
        user32.mouse_event(down_flag, 0, 0, 0, 0)
        time.sleep(0.03 + random.uniform(0.01, 0.03))
        user32.mouse_event(up_flag, 0, 0, 0, 0)
        if i < clicks - 1:
            time.sleep(interval)


def move_and_click(
    x: int, y: int, button: str = "left", clicks: int = 1, smooth: bool = True, duration: float = 0.25
):
    """Move cursor to (x, y) and click."""
    move_mouse(x, y, smooth=smooth, duration=duration)
    time.sleep(0.04)
    mouse_click(button=button, clicks=clicks)
