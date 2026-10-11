"""
Freehand drawing in a window (Paint, whiteboards, canvases) in a single call.

An AI drawing stroke by stroke pays a full model round trip per line; draw_strokes
takes the whole picture at once and replays it at mouse speed. Coordinates are
relative to the target window's client area, so they stay valid if the window moves.

The drawing stops as soon as the user takes over: another window comes to the
front, or the mouse is moved by hand. It never draws into a window it didn't target.
"""

import time

from deskdriver.core.desktop import ensure_desktop
from deskdriver.core.mouse import MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, get_mouse_position, send_move, user32
from deskdriver.automation.windows import client_rect, focus_window, foreground_root, list_windows
from deskdriver.automation.appid import find_app_window

# Pixels between interpolated points: small enough for smooth lines, large enough to be quick
STEP_PX = 6
# Pause per interpolated point so the app sees every move
POINT_DELAY = 0.004
# Cursor drift (px) from where we last put it that counts as the user moving the mouse
HAND_MOVE_TOLERANCE = 3


def _interpolate(a: tuple[int, int], b: tuple[int, int]):
    """Points from a (exclusive) to b (inclusive), STEP_PX apart."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = max(1, int(max(abs(dx), abs(dy)) / STEP_PX))
    for i in range(1, n + 1):
        yield a[0] + dx * i // n, a[1] + dy * i // n


def _normalize(strokes) -> list[list[tuple[int, int]]]:
    """[[x, y], ...] polylines (single points allowed) -> integer tuples; raises ValueError."""
    out = []
    for s, stroke in enumerate(strokes or []):
        pts = []
        for p in stroke:
            if not isinstance(p, (list, tuple)) or len(p) != 2:
                raise ValueError(f"stroke {s}: points must be [x, y] pairs, got {p!r}")
            pts.append((int(round(p[0])), int(round(p[1]))))
        if pts:
            out.append(pts)
    return out


def draw_strokes(window_search: str, strokes: list, button_delay: float = 0.03) -> dict:
    """
    Draw polylines in a window. `strokes` is a list of strokes, each a list of
    [x, y] points relative to the window's client area (0,0 = top-left inside the
    window, below the title bar). Each stroke is drawn with the left button held.
    """
    ensure_desktop()
    try:
        paths = _normalize(strokes)
    except (TypeError, ValueError) as e:
        return {"error": str(e)}

    win = find_app_window(window_search, list_windows()) if window_search else None
    if not win:
        return {"error": f"Window {window_search!r} not found"}
    hwnd = win["hwnd"]

    focus_window(hwnd)
    if foreground_root() != hwnd:
        return {"error": f"Could not bring {win['title']!r} to the front; nothing was drawn"}

    area = client_rect(hwnd)
    outside = [p for path in paths for p in path
               if not (0 <= p[0] < area["width"] and 0 <= p[1] < area["height"])]
    if outside:
        return {
            "error": f"{len(outside)} point(s) fall outside the window's client area "
                     f"({area['width']}x{area['height']}), e.g. {outside[0]}; nothing was drawn",
            "client_size": [area["width"], area["height"]],
        }

    def to_screen(p):
        return area["left"] + p[0], area["top"] + p[1]

    t0 = time.perf_counter()
    done = 0
    stopped = ""
    button_down = False
    try:
        for path in paths:
            if foreground_root() != hwnd:
                stopped = "another window came to the front"
                break
            start = to_screen(path[0])
            send_move(*start)
            expected = start
            time.sleep(button_delay)
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            button_down = True
            time.sleep(button_delay)

            prev = path[0]
            for point in path[1:]:
                for q in _interpolate(prev, point):
                    cur = get_mouse_position()
                    if abs(cur[0] - expected[0]) > HAND_MOVE_TOLERANCE or abs(cur[1] - expected[1]) > HAND_MOVE_TOLERANCE:
                        stopped = "the mouse was moved by hand"
                        break
                    expected = to_screen(q)
                    send_move(*expected)
                    time.sleep(POINT_DELAY)
                if stopped:
                    break
                prev = point

            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            button_down = False
            if stopped:
                break
            done += 1
    finally:
        if button_down:  # never leave the button held down
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    result = {
        "status": "interrupted" if stopped else "drawn",
        "window": win["title"],
        "strokes_drawn": done,
        "strokes_total": len(paths),
        "client_size": [area["width"], area["height"]],
        "duration_seconds": round(time.perf_counter() - t0, 2),
    }
    if stopped:
        result["reason"] = f"Stopped because {stopped}. The user may have taken over; ask before continuing."
    return result


def window_geometry(window_search: str) -> dict:
    """Window and client-area rectangles (screen coordinates) of the named app's window."""
    win = find_app_window(window_search, list_windows()) if window_search else None
    if not win:
        return {"error": f"Window {window_search!r} not found"}
    return {"window": win["title"], "hwnd": win["hwnd"], "window_rect": win["rect"], "client_rect": client_rect(win["hwnd"])}


__all__ = ["draw_strokes", "window_geometry"]
