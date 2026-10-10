"""
System Pre-Learn Engine.
Scans active application windows, desktop taskbar, and controls to pre-populate
the UI Roadmap database before the user or AI starts issuing tasks.
"""

import time
from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import list_windows, focus_window
from deskdriver.automation.uia import list_clickable_elements
from deskdriver.navigation.roadmap import roadmap
import uiautomation as auto


def run_system_prelearn(max_elements_per_app: int = 150) -> dict:
    """
    Scan all open windows and the taskbar, indexing their interactive elements
    into the persistent ui_roadmap.json database.
    """
    ensure_desktop()
    results = {
        "scanned_apps": [],
        "total_new_elements": 0,
        "duration_seconds": 0.0,
    }

    t0 = time.perf_counter()

    # 1. Scan open application windows
    windows = list_windows()
    scanned_keys = set()

    for win in windows:
        title = win["title"]
        app_key = roadmap.get_app_key(title)
        
        # Avoid duplicate scans for identical app instances
        if app_key in scanned_keys:
            continue
        scanned_keys.add(app_key)

        try:
            # Find elements in window with higher depth and element cap
            elements = list_clickable_elements(window_search=title, max_elements=max_elements_per_app)
            if elements:
                results["scanned_apps"].append({
                    "app": app_key,
                    "window_title": title[:40],
                    "elements_count": len(elements),
                })
                results["total_new_elements"] += len(elements)
        except Exception as e:
            results["scanned_apps"].append({
                "app": app_key,
                "error": str(e),
            })

    # 2. Deep scan Windows Taskbar (Start, Search, Running Apps, System Tray)
    try:
        taskbar = auto.PaneControl(ClassName="Shell_TrayWnd")
        if taskbar.Exists(0, 0):
            t_rect = taskbar.BoundingRectangle
            tb_elements = []
            visited_names = set()

            def walk_taskbar(ctrl, depth=0):
                if depth > 6 or len(tb_elements) >= 40:
                    return
                for child in ctrl.GetChildren():
                    name = (child.Name or "").strip()
                    r = child.BoundingRectangle
                    w = r.right - r.left
                    h = r.bottom - r.top

                    # If has name or is button, and valid size
                    if name and name not in visited_names and w > 0 and h > 0:
                        # Exclude non-descriptive icon glyphs like single unknown unicode char
                        if len(name) > 1 or name.isalnum():
                            visited_names.add(name)
                            tb_elements.append({
                                "name": name,
                                "control_type": child.ControlTypeName,
                                "center_x": (r.left + r.right) // 2,
                                "center_y": (r.top + r.bottom) // 2,
                                "rect": {"left": r.left, "top": r.top, "width": w, "height": h},
                            })
                    walk_taskbar(child, depth + 1)

            walk_taskbar(taskbar)

            if tb_elements:
                roadmap.learn_window(
                    window_title="taskbar",
                    elements=tb_elements,
                    window_rect={"left": t_rect.left, "top": t_rect.top, "right": t_rect.right, "bottom": t_rect.bottom},
                )
                results["scanned_apps"].append({
                    "app": "taskbar",
                    "window_title": "Windows Taskbar",
                    "elements_count": len(tb_elements),
                })
                results["total_new_elements"] += len(tb_elements)
    except Exception:
        pass


    results["duration_seconds"] = round(time.perf_counter() - t0, 2)
    results["total_mapped_apps"] = len(roadmap.map)
    results["total_mapped_elements"] = sum(len(a.get("elements", {})) for a in roadmap.map.values())

    return results
