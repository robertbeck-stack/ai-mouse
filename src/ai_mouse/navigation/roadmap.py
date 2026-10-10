"""
Persistent UI Roadmap engine for spatial UI element caching and fast O(1) retrieval.
"""

import json
import time
from pathlib import Path
from ai_mouse.core.desktop import ensure_desktop
from ai_mouse.core.mouse import move_and_click, mouse_click, user32
from ai_mouse.automation.windows import list_windows, focus_window
from ai_mouse.navigation.fastpaths import execute_fastpath

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

        for el in elements:
            name = (el.get("name") or "").strip().lower()
            if not name or name.startswith("("):
                continue

            rel_x = el["center_x"] - win_left
            rel_y = el["center_y"] - win_top

            self.map[app_key]["elements"][name] = {
                "name": el["name"],
                "control_type": el["control_type"],
                "rel_x": rel_x,
                "rel_y": rel_y,
                "width": el.get("rect", {}).get("width", 0),
                "height": el.get("rect", {}).get("height", 0),
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
            abs_x = window_rect["left"] + matched["rel_x"]
            abs_y = window_rect["top"] + matched["rel_y"]
            return {
                "name": matched["name"],
                "control_type": matched["control_type"],
                "center_x": abs_x,
                "center_y": abs_y,
                "source": "roadmap_cache",
            }
        return None


roadmap = UIRoadmap()


def fast_click_element(element_name: str, window_search: str = "", instant: bool = True) -> dict:
    """
    High-speed click on an element by name.
    Uses Roadmap Cache to resolve coordinates in < 1ms if learned previously.
    Automatically falls back to scanning and learning on cache miss.
    """
    ensure_desktop()

    # 1. Check if target matches OS Fastpath
    target_clean = element_name.lower().strip()
    if execute_fastpath(target_clean):
        return {"status": "fastpath_executed", "target": element_name}

    # 2. Find target window
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

    # 3. Check Roadmap Cache
    cached = roadmap.find_cached_element(target_win["title"], element_name, target_win["rect"])
    if cached:
        cx = cached["center_x"]
        cy = cached["center_y"]
        if instant:
            user32.SetCursorPos(cx, cy)
            mouse_click()
        else:
            move_and_click(cx, cy, smooth=True, duration=0.15)
        return {"status": "clicked_from_roadmap", "name": cached["name"], "x": cx, "y": cy, "source": "cache"}

    # 4. Cache miss: Scan, learn, and click
    from ai_mouse.automation.uia import list_clickable_elements

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
