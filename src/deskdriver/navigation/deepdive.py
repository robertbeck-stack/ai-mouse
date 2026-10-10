"""
Total Deep-Dive Engine for DeskDriver.
Performs an exhaustive inspection of any application—whether legacy Win32 (C/C++, MFC, VB6)
or modern (WPF, WinUI, Electron, Chromium, React Native)—extracting every menu, command,
toolbar button, input, tab, and keyboard accelerator.
"""

import ctypes
from ctypes import wintypes
import time
from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import list_windows, focus_window, user32
from deskdriver.automation.uia import is_interactive_control, get_element_name
from deskdriver.navigation.hotkeys import extract_shortcut_from_name
from deskdriver.navigation.roadmap import roadmap
import uiautomation as auto
import winsound

# Win32 Legacy Menu APIs
MF_BYPOSITION = 0x0400

try:
    user32.GetMenu.restype = wintypes.HMENU
    user32.GetMenu.argtypes = [wintypes.HWND]
    user32.GetMenuItemCount.restype = ctypes.c_int
    user32.GetMenuItemCount.argtypes = [wintypes.HMENU]
    user32.GetSubMenu.restype = wintypes.HMENU
    user32.GetSubMenu.argtypes = [wintypes.HMENU, ctypes.c_int]
    user32.GetMenuStringW.restype = ctypes.c_int
    user32.GetMenuStringW.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.LPWSTR, ctypes.c_int, wintypes.UINT]
    user32.GetMenuItemID.restype = wintypes.UINT
    user32.GetMenuItemID.argtypes = [wintypes.HMENU, ctypes.c_int]
except Exception:
    pass


def extract_win32_menu_items(hwnd: int) -> list[dict]:
    """
    Exhaustively extracts all legacy Win32 menu commands (File, Edit, View, Help, etc.)
    and their sub-menus directly from the OS menu handle, even when menus are closed.
    """
    items = []
    hmenu = user32.GetMenu(hwnd)
    if not hmenu:
        return items

    def recurse_menu(h_sub, parent_path=""):
        count = user32.GetMenuItemCount(h_sub)
        if count <= 0:
            return

        buff = ctypes.create_unicode_buffer(256)
        for i in range(count):
            length = user32.GetMenuStringW(h_sub, i, buff, 256, MF_BYPOSITION)
            if length > 0:
                raw_text = buff.value.replace("&", "").strip()
                if not raw_text or raw_text.startswith("---"):
                    continue

                full_name = f"{parent_path} > {raw_text}" if parent_path else raw_text
                clean_name, sc = extract_shortcut_from_name(raw_text)

                h_child = user32.GetSubMenu(h_sub, i)
                if h_child:
                    # It's a submenu (e.g. File, Edit, Tools)
                    recurse_menu(h_child, full_name)
                else:
                    # Leaf action item
                    items.append({
                        "name": clean_name,
                        "menu_path": full_name,
                        "control_type": "MenuItemControl",
                        "shortcut": sc,
                        "center_x": 0,
                        "center_y": 0,
                        "rect": {"left": 0, "top": 0, "width": 0, "height": 0},
                    })

    recurse_menu(hmenu)
    return items


def deep_dive_app(
    window_search: str = "",
    max_depth: int = 15,
    max_elements: int = 500,
) -> dict:
    """
    Total Deep Dive: Discovers every menu item, toolbar button, input field,
    tab, and keyboard accelerator in a target window and indexes it into ui_roadmap.json.
    """
    ensure_desktop()
    t0 = time.perf_counter()

    wins = list_windows()
    target_win = None
    if window_search:
        q = window_search.lower()
        for w in wins:
            if q in w["title"].lower():
                target_win = w
                break
    elif wins:
        # Avoid picking the dashboard itself
        for w in wins:
            t = w["title"].lower()
            if "dashboard" not in t and "cmd" not in t and "terminal" not in t:
                target_win = w
                break
        if not target_win:
            target_win = wins[0]

    if not target_win:
        return {"error": "Target window not found"}

    hwnd = target_win["hwnd"]
    title = target_win["title"]
    win_rect = target_win["rect"]
    app_key = roadmap.get_app_key(title)

    focus_window(hwnd)
    time.sleep(0.15)

    all_discovered = []
    seen_names = set()

    # 1. Legacy Win32 Menus (File -> Save, Edit -> Find, etc.)
    try:
        menu_items = extract_win32_menu_items(hwnd)
        for mi in menu_items:
            k = mi["name"].lower()
            if k not in seen_names:
                seen_names.add(k)
                all_discovered.append(mi)
    except Exception:
        pass

    # 2. Complete UIA Tree Traversal (buttons, toolbars, inputs, tabs, lists, trees)
    try:
        ctrl = auto.ControlFromHandle(hwnd)
        if ctrl:
            def walk(child_ctrl, depth=0):
                if depth > max_depth or len(all_discovered) >= max_elements:
                    return

                try:
                    for child in child_ctrl.GetChildren():
                        r = child.BoundingRectangle
                        w = r.right - r.left
                        h = r.bottom - r.top

                        if is_interactive_control(child) and w > 0 and h > 0:
                            raw_name = get_element_name(child)
                            sc = getattr(child, "AcceleratorKey", "") or getattr(child, "AccessKey", "")
                            clean_name, final_sc = extract_shortcut_from_name(raw_name, fallback_shortcut=sc.strip() if sc else "")

                            k = clean_name.lower().strip()
                            if k and not k.startswith("(") and k not in seen_names:
                                seen_names.add(k)
                                all_discovered.append({
                                    "name": clean_name,
                                    "control_type": child.ControlTypeName,
                                    "shortcut": final_sc,
                                    "center_x": (r.left + r.right) // 2,
                                    "center_y": (r.top + r.bottom) // 2,
                                    "rect": {
                                        "left": r.left,
                                        "top": r.top,
                                        "width": w,
                                        "height": h,
                                    },
                                })

                        walk(child, depth + 1)
                except Exception:
                    pass

            walk(ctrl)
    except Exception:
        pass

    # 3. Categorize results for rich Wikipedia breakdown
    categories = {
        "menus": [],
        "buttons": [],
        "inputs": [],
        "tabs": [],
        "others": [],
        "shortcuts": [],
    }

    for item in all_discovered:
        ct = item.get("control_type", "")
        sc = item.get("shortcut", "")
        if sc:
            categories["shortcuts"].append({"name": item["name"], "shortcut": sc})

        if "Menu" in ct:
            categories["menus"].append(item["name"])
        elif "Button" in ct or "ToolBar" in ct:
            categories["buttons"].append(item["name"])
        elif "Edit" in ct or "ComboBox" in ct or "Spinner" in ct:
            categories["inputs"].append(item["name"])
        elif "Tab" in ct or "Tree" in ct or "List" in ct or "Item" in ct:
            categories["tabs"].append(item["name"])
        else:
            categories["others"].append(item["name"])

    # 4. Save into persistent UI Roadmap
    roadmap.learn_window(title, all_discovered, win_rect)
    roadmap.save()

    # Play completion chime
    try:
        winsound.MessageBeep(0)
    except Exception:
        pass

    duration = round(time.perf_counter() - t0, 2)

    return {
        "status": "deep_dive_complete",
        "app": app_key,
        "window_title": title,
        "total_elements": len(all_discovered),
        "total_shortcuts": len(categories["shortcuts"]),
        "duration_seconds": duration,
        "categories": {
            "menu_items": len(categories["menus"]),
            "buttons_toolbars": len(categories["buttons"]),
            "inputs": len(categories["inputs"]),
            "navigation_tabs": len(categories["tabs"]),
        },
        "discovered_elements": all_discovered,
    }
