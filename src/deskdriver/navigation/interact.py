"""
Roadmap-driven desktop actions: click, fill, wait for and record named UI elements.

Resolution order for a named target: OS fastpath -> universal hotkey -> cached
element (roadmap) -> live UI Automation scan, which is learned into the roadmap.
"""

import time

from deskdriver.core.desktop import ensure_desktop
from deskdriver.core.keyboard import press_hotkey, type_text, COMMON_HOTKEYS
from deskdriver.core.mouse import move_and_click, mouse_click, get_mouse_position, user32
from deskdriver.automation.windows import list_windows, focus_window, window_at, window_info
from deskdriver.automation.uia import elements_at, inspect_at, scan_clickable_elements
from deskdriver.automation.appid import identify_window, find_app_window
from deskdriver.navigation.fastpaths import execute_fastpath
from deskdriver.navigation.roadmap import roadmap, match_element_key
from deskdriver.navigation.deepdive import deep_dive_app


def cached_target_present(cached: dict) -> bool:
    """
    Is the cached element still where the roadmap says? Checks the element at its
    position (and a few ancestors, since the hit is often the label inside a button)
    by name, or by control type for unnamed controls ("button @ 62,985").
    A position UIA can't read counts as absent (the caller rescans): it is usually
    an elevated or protected window, which wouldn't accept the click anyway.
    """
    found = elements_at(cached["center_x"], cached["center_y"])
    if not found:
        return False
    name = (cached.get("name") or "").strip().lower()
    if " @ " in name:
        return any(ct == cached.get("control_type") for _, ct in found)
    return any(n.lower() == name or (n and (n.lower() in name or name in n.lower())) for n, _ in found)


def _target_window(window_search: str, wins: list[dict]) -> dict | None:
    """The window an action is aimed at: the named app / title, else the topmost window."""
    if window_search:
        return find_app_window(window_search, wins)
    return wins[0] if wins else None


def list_clickable_elements(
    window_search: str | None = None, max_elements: int = 150, hwnd: int | None = None
) -> list[dict]:
    """
    Find clickable interactive elements in the target (or foreground) window and
    learn them into the roadmap so later lookups hit the cache.
    window_search may name the app ("notepad", "Settings") or part of a title.
    """
    if hwnd is None and window_search:
        win = find_app_window(window_search, list_windows())
        hwnd = win["hwnd"] if win else None
    elements, window = scan_clickable_elements(window_search, max_elements, hwnd=hwnd)
    # Prefer the window we asked for and its Win32 rect: UIA's top-level control can
    # report a bogus (even zero-size) rectangle for Qt apps such as VLC.
    target = hwnd or (window or {}).get("hwnd")
    if elements and target:
        try:
            roadmap.learn_window(identify_window(target), elements=elements, window_rect=window_info(target)["rect"])
        except Exception:
            pass
    return elements


def fast_click_element(element_name: str, window_search: str = "", instant: bool = True) -> dict:
    """
    High-speed click on an element by name.
    1. Checks OS Fastpaths (0 ms).
    2. Checks Universal Hotkeys & Cached Accelerators (0.5 ms).
    3. Resolves coordinates via Roadmap Cache (< 1 ms).
    4. Automatically falls back to scanning and learning on cache miss.
    """
    ensure_desktop()

    target_clean = element_name.lower().strip()

    # 1. Check OS Fastpaths
    if execute_fastpath(target_clean):
        return {"status": "fastpath_executed", "target": element_name}

    # 2. Check Universal Hotkey shortcuts
    if target_clean in COMMON_HOTKEYS:
        hk = COMMON_HOTKEYS[target_clean]
        if window_search:
            win = find_app_window(window_search, list_windows())
            if win and not focus_window(win["hwnd"]):
                return {"error": f"Could not bring {win['title']!r} to the front; hotkey not sent"}
        press_hotkey(hk)
        return {"status": "universal_hotkey_executed", "action": element_name, "hotkey": hk}

    # 3. Find target window
    target_win = _target_window(window_search, list_windows())
    if not target_win:
        return {"error": "Target window not found"}

    if not focus_window(target_win["hwnd"]):
        # Clicking anyway would hit whatever window is in front instead
        return {"error": f"Could not bring {target_win['title']!r} to the front; nothing was clicked"}
    app_key = identify_window(target_win["hwnd"]).key

    # 4. Check Roadmap Cache
    cached = roadmap.find_cached_element(app_key, element_name, target_win["rect"])
    if cached and cached.get("shortcut"):
        # A known accelerator is faster and position-independent
        press_hotkey(cached["shortcut"])
        return {"status": "accelerator_hotkey_executed", "name": cached["name"], "shortcut": cached["shortcut"]}
    if cached and not cached_target_present(cached):
        cached = None  # layout changed: rescan below (which re-learns the new position)
    if cached:
        cx = cached["center_x"]
        cy = cached["center_y"]
        if instant:
            user32.SetCursorPos(cx, cy)
            mouse_click()
        else:
            move_and_click(cx, cy, smooth=True, duration=0.15)
        return {"status": "clicked_from_roadmap", "name": cached["name"], "x": cx, "y": cy, "source": "cache"}


    # 5. Cache miss: scan (which also learns the window), then click
    elements = list_clickable_elements(hwnd=target_win["hwnd"], max_elements=50)
    by_name = {el["name"].strip().lower(): el for el in elements if el.get("name")}
    key = match_element_key(by_name, element_name)
    matched = by_name.get(key) if key else None

    if matched:
        cx = matched["center_x"]
        cy = matched["center_y"]
        if instant:
            user32.SetCursorPos(cx, cy)
            mouse_click()
        else:
            move_and_click(cx, cy, smooth=True, duration=0.15)
        return {"status": "clicked_and_learned", "name": matched["name"], "x": cx, "y": cy, "source": "scan"}

    return {"error": f"Element {element_name!r} not found in window {target_win['title']!r}"}


def fill_input(
    element_name: str,
    text: str,
    window_search: str = "",
    submit: bool = False,
    clear_existing: bool = True,
    instant: bool = True,
) -> dict:
    """
    Combined fluid action for AI:
    1. Focuses window and clicks directly into the input control (via cache or fast UIA scan).
    2. Clears any existing text (Ctrl+A, Backspace) if clear_existing is True.
    3. Types Unicode text.
    4. Optionally submits with Enter if submit=True.
    """
    click_res = fast_click_element(element_name, window_search=window_search, instant=instant)
    if "error" in click_res:
        return click_res

    time.sleep(0.04)

    if clear_existing:
        press_hotkey("ctrl+a")
        time.sleep(0.02)
        press_hotkey("backspace")
        time.sleep(0.02)

    type_text(text, enter=submit)
    return {
        "status": "input_filled",
        "element": element_name,
        "text_length": len(text),
        "submitted": submit,
        "click_details": click_res,
    }


def record_element_at_cursor(custom_name: str = "") -> dict:
    """
    Record on Hover: captures the interactive element directly under the cursor,
    calculates responsive edge-anchors, and persists it into ui_roadmap/.
    """
    x, y = get_mouse_position()
    info = inspect_at(x, y)
    win = window_at(x, y)
    if not win:
        return {"error": f"No window under the cursor at ({x}, {y})"}
    identity = identify_window(win["hwnd"])

    rect = info.get("bounding_rect") or {"left": x - 10, "top": y - 10, "width": 20, "height": 20}
    name = custom_name.strip() or info.get("name", "").strip() or f"Control_{x}_{y}"

    element_dict = {
        "name": name,
        "control_type": info.get("control_type", "CustomControl"),
        "center_x": rect.get("left", x) + max(1, rect.get("width", 20) // 2),
        "center_y": rect.get("top", y) + max(1, rect.get("height", 20) // 2),
        "rect": rect,
    }

    roadmap.learn_window(identity, [element_dict], win["rect"])
    return {
        "status": "element_recorded",
        "app": identity.key,
        "display_name": identity.display_name,
        "element": element_dict["name"],
        "control_type": element_dict["control_type"],
        "center_x": element_dict["center_x"],
        "center_y": element_dict["center_y"],
    }


def wait_for_element(
    element_name: str,
    window_search: str = "",
    timeout: float = 3.0,
    poll_interval: float = 0.05,
) -> dict | None:
    """
    Poll until an element becomes available in the target window or timeout expires.
    Checks roadmap cache first, then scans UIA tree dynamically.
    Returns the resolved element dict with center coordinates, or None on timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        wins = list_windows()
        target_win = _target_window(window_search, wins)

        if target_win:
            # A cached position only counts once the element is actually there
            cached = roadmap.find_cached_element(identify_window(target_win["hwnd"]).key, element_name, target_win["rect"])
            if cached and cached_target_present(cached):
                return cached

            if not window_search:
                for w in wins:
                    cached_other = roadmap.find_cached_element(identify_window(w["hwnd"]).key, element_name, w["rect"])
                    if cached_other and cached_target_present(cached_other):
                        return cached_other

            elements = list_clickable_elements(hwnd=target_win["hwnd"], max_elements=50)
            by_name = {el["name"].strip().lower(): el for el in elements if el.get("name")}
            key = match_element_key(by_name, element_name)
            if key:
                return by_name[key]

        time.sleep(poll_interval)
    return None


def wait_and_click(
    element_name: str,
    window_search: str = "",
    timeout: float = 3.0,
    instant: bool = True,
) -> dict:
    """
    Wait for an element to appear in a window and click it immediately (atomic agent action).
    """
    el = wait_for_element(element_name, window_search=window_search, timeout=timeout)
    if not el:
        return {"error": f"Timed out waiting for element {element_name!r} after {timeout}s"}
    return fast_click_element(element_name, window_search=window_search, instant=instant)


def auto_record_window(
    window_search: str = "",
    move_cursor: bool = False,
    max_elements: int = 150,
) -> dict:
    """
    Quiet, non-intrusive scan alias. Discovers and indexes application controls
    without moving the physical mouse cursor.
    """
    res = deep_dive_app(window_search=window_search, max_elements=max_elements)
    if isinstance(res, dict) and res.get("status") == "deep_dive_complete":
        return {
            "status": "auto_recorded",
            "app": res.get("app", ""),
            "window_title": res.get("window_title", ""),
            "recorded_elements": [e.get("name") for e in res.get("discovered_elements", []) if e.get("name")],
            "new_elements": res.get("new_elements", []),
            "new_count": res.get("new_count", 0),
            "count": res.get("total_elements", 0),
        }
    return res
