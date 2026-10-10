"""
UI Automation element detection, cursor inspection, and interactive control scanning.
"""

from ai_mouse.core.desktop import ensure_desktop
from ai_mouse.core.mouse import get_mouse_position
from ai_mouse.automation.windows import list_windows, user32
import uiautomation as auto

# Comprehensive set of interactive control types across Windows & web apps
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
    auto.ControlType.TreeItemControl,
    auto.ControlType.SliderControl,
    auto.ControlType.ThumbControl,
    auto.ControlType.HeaderItemControl,
    auto.ControlType.DataItemControl,
    auto.ControlType.SpinnerControl,
    auto.ControlType.ToolBarControl,
}


def is_interactive_control(child) -> bool:
    """
    Determine if a control is interactive either via its ControlType
    or by detecting Windows Automation interaction patterns (Invoke, Toggle, Selection, etc.).
    """
    if child.ControlType in CLICKABLE_TYPES:
        return True

    # Check for actionable patterns on Custom or generic controls (common in Electron, React, Chrome)
    try:
        if (
            child.GetInvokePattern() is not None
            or child.GetTogglePattern() is not None
            or child.GetSelectionItemPattern() is not None
            or child.GetExpandCollapsePattern() is not None
        ):
            return True
    except Exception:
        pass

    return False


def get_element_name(ctrl) -> str:
    """Extract the best descriptive name with fallbacks to AutomationId, HelpText, or coordinate tag."""
    name = (ctrl.Name or "").strip()
    if name:
        return name

    # Fallback to AutomationId
    auto_id = getattr(ctrl, "AutomationId", "")
    if auto_id and str(auto_id).strip():
        return f"id:{auto_id.strip()}"

    # Fallback to HelpText/Tooltip
    help_text = getattr(ctrl, "HelpText", "")
    if help_text and str(help_text).strip():
        return help_text.strip()

    rect = ctrl.BoundingRectangle
    cx = (rect.left + rect.right) // 2
    cy = (rect.top + rect.bottom) // 2
    return f"unnamed_{ctrl.ControlTypeName.lower()}_{cx}_{cy}"


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


def list_clickable_elements(window_search: str | None = None, max_elements: int = 150) -> list[dict]:
    """
    Find clickable interactive elements in the active window or target window.
    Deep traversal with high coverage for web browsers, settings, and desktop apps.
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
        if depth > 12 or len(elements) >= max_elements:
            return
        try:
            for child in ctrl.GetChildren():
                rect = child.BoundingRectangle
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if is_interactive_control(child) and w > 0 and h > 0:
                    raw_name = get_element_name(child)
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    sc = getattr(child, "AcceleratorKey", "") or getattr(child, "AccessKey", "")
                    
                    from ai_mouse.navigation.hotkeys import extract_shortcut_from_name
                    clean_name, final_shortcut = extract_shortcut_from_name(raw_name, fallback_shortcut=sc.strip() if sc else "")

                    elements.append({
                        "name": clean_name,
                        "control_type": child.ControlTypeName,
                        "shortcut": final_shortcut,
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
