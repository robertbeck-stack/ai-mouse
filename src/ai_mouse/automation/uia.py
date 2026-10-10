"""
UI Automation element detection, cursor inspection, and interactive control scanning.
"""

from ai_mouse.core.desktop import ensure_desktop
from ai_mouse.core.mouse import get_mouse_position
from ai_mouse.automation.windows import list_windows, user32
import uiautomation as auto

CLICKABLE_TYPES = {
    auto.ControlType.ButtonControl,
    auto.ControlType.HyperlinkControl,
    auto.ControlType.MenuItemControl,
    auto.ControlType.CheckBoxControl,
    auto.ControlType.RadioButtonControl,
    auto.ControlType.TabItemControl,
    auto.ControlType.SplitButtonControl,
    auto.ControlType.ComboBoxControl,
    auto.ControlType.EditControl,
    auto.ControlType.ListItemControl,
}


def get_element_under_cursor() -> dict:
    """Inspect and return UI details for the element directly under the cursor."""
    ensure_desktop()
    x, y = get_mouse_position()
    return get_element_at(x, y)


def get_element_at(x: int, y: int) -> dict:
    """Inspect and return UI details for the element at coordinates (x, y)."""
    ensure_desktop()
    try:
        ctrl = auto.ControlFromPoint(x, y)
        if not ctrl:
            return {"error": "No element found at coordinates", "x": x, "y": y}

        rect = ctrl.BoundingRectangle
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        top_window = ctrl.GetTopLevelControl()
        window_title = top_window.Name if top_window else ""

        return {
            "name": ctrl.Name or "(no text)",
            "control_type": ctrl.ControlTypeName,
            "x": x,
            "y": y,
            "bounding_rect": {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": w,
                "height": h,
                "center_x": (rect.left + rect.right) // 2,
                "center_y": (rect.top + rect.bottom) // 2,
            },
            "is_enabled": getattr(ctrl, "IsEnabled", True),
            "window_title": window_title,
            "class_name": ctrl.ClassName,
        }
    except Exception as e:
        return {"error": str(e), "x": x, "y": y}


def list_clickable_elements(window_search: str | None = None, max_elements: int = 50) -> list[dict]:
    """
    Find clickable interactive elements in the active window or target window.
    Automatically caches discovered elements into the roadmap.
    """
    ensure_desktop()

    target_ctrl = None
    if window_search:
        wins = list_windows()
        q = window_search.lower()
        for w in wins:
            if q in w["title"].lower():
                target_ctrl = auto.ControlFromHandle(w["hwnd"])
                break

    if not target_ctrl:
        fg_hwnd = user32.GetForegroundWindow()
        target_ctrl = auto.ControlFromHandle(fg_hwnd)

    if not target_ctrl:
        return []

    elements = []

    def walk(ctrl, depth=0):
        if depth > 7 or len(elements) >= max_elements:
            return
        try:
            for child in ctrl.GetChildren():
                rect = child.BoundingRectangle
                w = rect.right - rect.left
                h = rect.bottom - rect.top

                if child.ControlType in CLICKABLE_TYPES and w > 0 and h > 0:
                    name = (child.Name or "").strip()
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    elements.append({
                        "name": name if name else f"({child.ControlTypeName})",
                        "control_type": child.ControlTypeName,
                        "center_x": cx,
                        "center_y": cy,
                        "rect": {
                            "left": rect.left,
                            "top": rect.top,
                            "width": w,
                            "height": h,
                        },
                    })
                    if len(elements) >= max_elements:
                        return
                walk(child, depth + 1)
        except Exception:
            pass

    walk(target_ctrl)

    # Automatically learn discovered elements into the roadmap
    try:
        from ai_mouse.navigation.roadmap import roadmap
        top_win = target_ctrl.GetTopLevelControl() or target_ctrl
        w_rect = top_win.BoundingRectangle
        roadmap.learn_window(
            window_title=top_win.Name or "unknown",
            elements=elements,
            window_rect={
                "left": w_rect.left,
                "top": w_rect.top,
                "right": w_rect.right,
                "bottom": w_rect.bottom,
            },
        )
    except Exception:
        pass

    return elements
