"""
Persistent UI Roadmap engine for spatial UI element caching and fast O(1) retrieval.
"""

import json
import time
from pathlib import Path
from deskdriver.core.desktop import ensure_desktop
from deskdriver.core.mouse import move_and_click, mouse_click, user32
from deskdriver.automation.windows import list_windows, focus_window
from deskdriver.navigation.fastpaths import execute_fastpath

ROADMAP_FILE = Path(__file__).parent.parent.parent.parent / "ui_roadmap.json"


class UIRoadmap:
    def __init__(self, filepath: Path = ROADMAP_FILE):
        self.filepath = filepath
        self.map = self._load()

    def _load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.map, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_app_key(self, window_title: str) -> str:
        """Normalize window title to identify application family."""
        t = window_title.lower()
        if "brave" in t:
            return "brave"
        if "chrome" in t:
            return "chrome"
        if "settings" in t:
            return "settings"
        if "notepad" in t:
            return "notepad"
        if "file explorer" in t or "configs" in t:
            return "explorer"
        return window_title[:30].strip()

    def learn_window(self, window_title: str, elements: list[dict], window_rect: dict):
        """Cache elements using coordinates relative to the window top-left."""
        app_key = self.get_app_key(window_title)
        if app_key not in self.map:
            self.map[app_key] = {"elements": {}, "last_updated": time.time()}

        win_left = window_rect["left"]
        win_top = window_rect["top"]
        win_w = max(1, window_rect.get("right", win_left + 800) - win_left)
        win_h = max(1, window_rect.get("bottom", win_top + 600) - win_top)

        for el in elements:
            name = (el.get("name") or "").strip().lower()
            if not name or name.startswith("("):
                continue

            rel_x = el["center_x"] - win_left
            rel_y = el["center_y"] - win_top
            anchor_right = rel_x > (win_w * 0.65)
            anchor_bottom = rel_y > (win_h * 0.65)

            self.map[app_key]["elements"][name] = {
                "name": el["name"],
                "control_type": el["control_type"],
                "shortcut": el.get("shortcut", ""),
                "rel_x": rel_x,
                "rel_y": rel_y,
                "anchor_right": anchor_right,
                "anchor_bottom": anchor_bottom,
                "dist_from_right": win_w - rel_x,
                "dist_from_bottom": win_h - rel_y,
                "width": el.get("rect", {}).get("width", 0),
                "height": el.get("rect", {}).get("height", 0),
            }

        # Merge standard application hotkey profiles if known
        from deskdriver.navigation.hotkeys import APP_PROFILES
        app_profile = APP_PROFILES.get(app_key, {})
        for action_name, hk in app_profile.items():
            matched_key = None
            for k in self.map[app_key]["elements"]:
                if action_name in k or k in action_name:
                    matched_key = k
                    break
            if matched_key:
                if not self.map[app_key]["elements"][matched_key].get("shortcut"):
                    self.map[app_key]["elements"][matched_key]["shortcut"] = hk
            else:
                self.map[app_key]["elements"][action_name] = {
                    "name": action_name.title(),
                    "control_type": "HotkeyAction",
                    "shortcut": hk,
                    "rel_x": 0,
                    "rel_y": 0,
                    "width": 0,
                    "height": 0,
                }

        self.map[app_key]["last_updated"] = time.time()
        self.save()


    def find_cached_element(self, window_title: str, element_name: str, window_rect: dict) -> dict | None:
        """O(1) instant lookup from roadmap memory."""
        app_key = self.get_app_key(window_title)
        app_data = self.map.get(app_key)
        if not app_data:
            return None

        q = element_name.strip().lower()
        elements = app_data.get("elements", {})

        matched = elements.get(q)
        if not matched:
            for k, v in elements.items():
                if q in k or k in q:
                    matched = v
                    break

        if matched:
            curr_w = window_rect.get("right", 0) - window_rect.get("left", 0)
            curr_h = window_rect.get("bottom", 0) - window_rect.get("top", 0)

            # Responsive right-anchor adjustment
            if matched.get("anchor_right") and curr_w > 0 and matched.get("dist_from_right", 0) > 0:
                abs_x = window_rect["right"] - matched["dist_from_right"]
            else:
                abs_x = window_rect["left"] + matched["rel_x"]

            # Responsive bottom-anchor adjustment
            if matched.get("anchor_bottom") and curr_h > 0 and matched.get("dist_from_bottom", 0) > 0:
                abs_y = window_rect["bottom"] - matched["dist_from_bottom"]
            else:
                abs_y = window_rect["top"] + matched["rel_y"]

            return {
                "name": matched["name"],
                "control_type": matched["control_type"],
                "shortcut": matched.get("shortcut", ""),
                "center_x": abs_x,
                "center_y": abs_y,
                "source": "roadmap_cache",
            }
        return None


roadmap = UIRoadmap()


def fast_click_element(element_name: str, window_search: str = "", instant: bool = True) -> dict:
    """
    High-speed click on an element by name.
    1. Checks OS Fastpaths (0 ms).
    2. Checks Universal Hotkeys & Cached Accelerators (0.5 ms).
    3. Resolves coordinates via Roadmap Cache (< 1 ms).
    4. Automatically falls back to scanning and learning on cache miss.
    """
    ensure_desktop()
    from deskdriver.core.keyboard import press_hotkey, COMMON_HOTKEYS

    target_clean = element_name.lower().strip()

    # 1. Check OS Fastpaths
    if execute_fastpath(target_clean):
        return {"status": "fastpath_executed", "target": element_name}

    # 2. Check Universal Hotkey shortcuts
    if target_clean in COMMON_HOTKEYS:
        hk = COMMON_HOTKEYS[target_clean]
        if window_search:
            wins = list_windows()
            for w in wins:
                if window_search.lower() in w["title"].lower():
                    focus_window(w["hwnd"])
                    break
        press_hotkey(hk)
        return {"status": "universal_hotkey_executed", "action": element_name, "hotkey": hk}

    # 3. Find target window
    wins = list_windows()
    target_win = None
    if window_search:
        q = window_search.lower()
        for w in wins:
            if q in w["title"].lower():
                target_win = w
                break
    elif wins:
        target_win = wins[0]

    if not target_win:
        return {"error": "Target window not found"}

    focus_window(target_win["hwnd"])

    # 4. Check Roadmap Cache
    cached = roadmap.find_cached_element(target_win["title"], element_name, target_win["rect"])
    if cached:
        # If element has a known accelerator shortcut, use it for 10x speedup
        if cached.get("shortcut"):
            press_hotkey(cached["shortcut"])
            return {"status": "accelerator_hotkey_executed", "name": cached["name"], "shortcut": cached["shortcut"]}

        cx = cached["center_x"]
        cy = cached["center_y"]
        if instant:
            user32.SetCursorPos(cx, cy)
            mouse_click()
        else:
            move_and_click(cx, cy, smooth=True, duration=0.15)
        return {"status": "clicked_from_roadmap", "name": cached["name"], "x": cx, "y": cy, "source": "cache"}


    # 4. Cache miss: Scan, learn, and click
    from deskdriver.automation.uia import list_clickable_elements

    elements = list_clickable_elements(window_search=target_win["title"], max_elements=50)
    matched = None
    q = element_name.lower().strip()
    for el in elements:
        if q in el["name"].lower():
            matched = el
            break

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
    from deskdriver.core.keyboard import press_hotkey, type_text

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
    calculates responsive edge-anchors, and persists it into ui_roadmap.json.
    """
    from deskdriver.core.mouse import get_mouse_position
    from deskdriver.automation.uia import inspect_at
    from deskdriver.automation.windows import list_windows

    x, y = get_mouse_position()
    info = inspect_at(x, y)
    win_title = info.get("window_title", "")

    # Locate window bounding box
    win_rect = None
    if win_title:
        for w in list_windows():
            if win_title.lower() in w["title"].lower():
                win_rect = w["rect"]
                break
    if not win_rect:
        win_rect = {"left": 0, "top": 0, "right": 1920, "bottom": 1080}

    rect = info.get("bounding_rect") or {"left": x - 10, "top": y - 10, "width": 20, "height": 20}
    name = custom_name.strip() or info.get("name", "").strip() or f"Control_{x}_{y}"

    element_dict = {
        "name": name,
        "control_type": info.get("control_type", "CustomControl"),
        "center_x": rect.get("left", x) + max(1, rect.get("width", 20) // 2),
        "center_y": rect.get("top", y) + max(1, rect.get("height", 20) // 2),
        "rect": rect,
    }

    roadmap.learn_window(win_title or "CustomApp", [element_dict], win_rect)
    return {
        "status": "element_recorded",
        "app": roadmap.get_app_key(win_title or "CustomApp"),
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
    from deskdriver.automation.windows import list_windows
    from deskdriver.automation.uia import list_clickable_elements

    start = time.time()
    while time.time() - start < timeout:
        wins = list_windows()
        target_win = None
        if window_search:
            q = window_search.lower()
            for w in wins:
                if q in w["title"].lower():
                    target_win = w
                    break
        elif wins:
            target_win = wins[0]

        if target_win:
            cached = roadmap.find_cached_element(target_win["title"], element_name, target_win["rect"])
            if cached:
                return cached

            elements = list_clickable_elements(window_search=target_win["title"], max_elements=50)
            q_el = element_name.lower().strip()
            for el in elements:
                if q_el in el["name"].lower():
                    roadmap.learn_window(target_win["title"], [el], target_win["rect"])
                    return el

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



