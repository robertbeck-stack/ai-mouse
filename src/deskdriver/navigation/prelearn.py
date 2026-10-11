"""
System Pre-Learn Engine.
Scans active application windows, desktop taskbar, and controls to pre-populate
the UI Roadmap database before the user or AI starts issuing tasks.
"""

import time
from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import list_windows
from deskdriver.automation.appid import identify_window
from deskdriver.navigation.interact import list_clickable_elements  # learns what it scans
from deskdriver.navigation.roadmap import roadmap
import uiautomation as auto


def run_system_prelearn(max_elements_per_app: int = 150) -> dict:
    """
    Scan all open windows and the taskbar, indexing their interactive elements
    into the persistent ui_roadmap/ database.
    """
    ensure_desktop()
    results = {
        "scanned_apps": [],
        "total_elements": 0,
        "total_new_elements": 0,
        "new_elements": [],
        "duration_seconds": 0.0,
    }

    t0 = time.perf_counter()
    all_new_elements = []
    total_elements_count = 0

    # 1. Scan open application windows
    windows = list_windows()
    scanned_keys = set()

    for win in windows:
        title = win["title"]
        app_key = identify_window(win["hwnd"]).key

        # Avoid duplicate scans for identical app instances
        if app_key in scanned_keys:
            continue
        scanned_keys.add(app_key)

        existing_keys = set(roadmap.map.get(app_key, {}).get("elements", {}).keys())

        try:
            # Find elements in window with higher depth and element cap
            elements = list_clickable_elements(hwnd=win["hwnd"], max_elements=max_elements_per_app)
            if elements:
                current_map = roadmap.map.get(app_key, {}).get("elements", {})
                new_app_elements = []
                for k, v in current_map.items():
                    if k not in existing_keys:
                        el_name = v.get("name") or k
                        new_app_elements.append(f"{app_key}: {el_name}")
                all_new_elements.extend(new_app_elements)

                results["scanned_apps"].append({
                    "app": app_key,
                    "window_title": title[:40],
                    "elements_count": len(elements),
                    "new_count": len(new_app_elements),
                    "new_elements": new_app_elements,
                })
                total_elements_count += len(elements)
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
                tb_identity = identify_window(taskbar.NativeWindowHandle)
                tb_key = tb_identity.key
                existing_tb = set(roadmap.map.get(tb_key, {}).get("elements", {}).keys())
                roadmap.learn_window(
                    tb_identity,
                    elements=tb_elements,
                    window_rect={"left": t_rect.left, "top": t_rect.top, "right": t_rect.right, "bottom": t_rect.bottom},
                )
                current_tb = roadmap.map.get(tb_key, {}).get("elements", {})
                new_tb = []
                for k, v in current_tb.items():
                    if k not in existing_tb:
                        el_name = v.get("name") or k
                        new_tb.append(f"taskbar: {el_name}")
                all_new_elements.extend(new_tb)

                results["scanned_apps"].append({
                    "app": tb_key,
                    "window_title": "Windows Taskbar",
                    "elements_count": len(tb_elements),
                    "new_count": len(new_tb),
                    "new_elements": new_tb,
                })
                total_elements_count += len(tb_elements)
    except Exception:
        pass


    results["duration_seconds"] = round(time.perf_counter() - t0, 2)
    results["total_elements"] = total_elements_count
    results["total_new_elements"] = len(all_new_elements)
    results["new_elements"] = all_new_elements
    results["total_mapped_apps"] = len(roadmap.map)
    results["total_mapped_elements"] = sum(len(a.get("elements", {})) for a in roadmap.map.values())

    return results
