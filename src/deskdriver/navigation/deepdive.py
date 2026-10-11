"""
Total Deep-Dive Engine for DeskDriver.
Performs an exhaustive inspection of any application—whether legacy Win32 (C/C++, MFC, VB6)
or modern (WPF, WinUI, Electron, Chromium, React Native)—extracting every menu, command,
toolbar button, input, tab, toggle, tooltip, and keyboard accelerator.
"""

import ctypes
from ctypes import wintypes
import time
from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import list_windows, focus_window, user32
from deskdriver.automation.appid import identify_window, find_app_window
from deskdriver.automation.uia import is_interactive_control, get_element_name
from deskdriver.core.shortcuts import extract_shortcut_from_name
from deskdriver.navigation.roadmap import roadmap
from deskdriver.navigation.history import record_scan_log
import uiautomation as auto
import winsound

# Win32 Legacy Menu APIs
MF_BYPOSITION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

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


def get_window_process_specs(hwnd: int) -> dict:
    """Extract comprehensive OS and process metadata for any target window."""
    specs = {
        "hwnd": hwnd,
        "pid": 0,
        "class_name": "",
        "exe_name": "",
        "exe_path": "",
        "is_maximized": False,
        "dpi": 96,
        "architecture": "x64",
    }
    try:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        specs["pid"] = pid.value

        buf = ctypes.create_unicode_buffer(512)
        user32.GetClassNameW(hwnd, buf, 512)
        specs["class_name"] = buf.value

        specs["is_maximized"] = bool(user32.IsZoomed(hwnd))
        if hasattr(user32, "GetDpiForWindow"):
            dpi = user32.GetDpiForWindow(hwnd)
            if dpi:
                specs["dpi"] = dpi

        kernel32 = ctypes.windll.kernel32
        hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if hproc:
            size = wintypes.DWORD(512)
            pbuf = ctypes.create_unicode_buffer(512)
            if kernel32.QueryFullProcessImageNameW(hproc, 0, pbuf, ctypes.byref(size)):
                specs["exe_path"] = pbuf.value
                specs["exe_name"] = pbuf.value.split("\\")[-1]

            is_wow64 = wintypes.BOOL()
            if hasattr(kernel32, "IsWow64Process") and kernel32.IsWow64Process(hproc, ctypes.byref(is_wow64)):
                specs["architecture"] = "x86 (32-bit)" if is_wow64.value else "x64 (64-bit)"
            kernel32.CloseHandle(hproc)
    except Exception:
        pass
    return specs


KNOWN_CANVAS_CLASSES = {
    "unitywndclass": "Unity Engine Game",
    "unrealwindow": "Unreal Engine Game",
    "glfw30": "OpenGL / GLFW Canvas",
    "sdl_app": "SDL2 Game / Canvas",
    "ogrewindow": "Ogre3D Engine",
    "valve001": "Valve Source Engine",
    "sunawtframe": "Java AWT / Swing Frame",
    "chrome_renderwidgethosthwnd": "Chromium WebGL / Canvas",
}


# Top-level frame classes of UI frameworks that always expose a real UIA tree.
# A sparse scan of these means the walk was cut short (still loading, capped,
# cross-process UWP content), never that the window is a GPU canvas.
KNOWN_UIA_HOST_CLASSES = {
    "applicationframewindow",        # UWP host (Settings, Calculator, Store)
    "windows.ui.core.corewindow",
    "winuidesktopwin32windowclass",  # WinUI 3
    "chrome_widgetwin_1",            # Chromium / Electron (Brave, Chrome, Edge, VS Code)
    "mozillawindowclass",
    "cabinetwclass",                 # File Explorer
    "notepad",
    "#32770",                        # Win32 dialog
    "shell_traywnd",
    "consolewindowclass",
    "cascadia_hosting_window_class", # Windows Terminal
    "mspaintapp",                    # Paint (WinUI content island)
}

# Child window classes that host XAML / WinUI content. Their UIA tree can be empty
# while the window is behind others or still loading, which must not read as a canvas.
XAML_CONTENT_CHILD_CLASSES = {
    "microsoft.ui.content.desktopchildsitebridge",       # WinUI 3
    "windows.ui.composition.desktopwindowcontentbridge",  # UWP XAML islands
}


def hosts_xaml_content(hwnd: int) -> bool:
    """Does the window contain a XAML / WinUI content island?"""
    found = []
    buf = ctypes.create_unicode_buffer(256)

    def cb(child, _):
        user32.GetClassNameW(child, buf, 256)
        if buf.value.lower() in XAML_CONTENT_CHILD_CLASSES:
            found.append(child)
            return False
        return True

    user32.EnumChildWindows(wintypes.HWND(hwnd), ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return bool(found)


def detect_canvas_game_surface(
    class_name: str,
    discovered_count: int,
    width: int,
    height: int,
    known_count: int = 0,
    truncated: bool = False,
    xaml_host: bool = False,
) -> dict:
    """Detect whether a window is a hardware-accelerated GPU canvas, game, or non-UIA surface.

    known_count is the number of real controls already cached for the app; truncated
    means the walk hit max_elements; xaml_host means the window embeds XAML / WinUI
    content (hosts_xaml_content). Any of them rules out the sparse-tree heuristic.
    """
    cn = (class_name or "").lower()
    engine_name = KNOWN_CANVAS_CLASSES.get(cn, "")
    sparse_tree = (
        discovered_count <= 4
        and known_count <= 4
        and not truncated
        and not xaml_host
        and cn not in KNOWN_UIA_HOST_CLASSES
        and width >= 400
        and height >= 300
    )
    is_canvas = bool(engine_name) or sparse_tree

    if is_canvas and not engine_name:
        engine_name = "Custom GPU Surface / Game Canvas"

    return {
        "is_canvas_game": is_canvas,
        "engine": engine_name,
        "advice": (
            "Hardware-accelerated canvas detected without OS UIA tree. "
            "Controlled via keyboard accelerators and spatial grid anchors."
        ) if is_canvas else "",
    }


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
                    action_cmd = f"hotkey:{sc.lower()}" if sc else f"click:{clean_name}"
                    items.append({
                        "name": clean_name,
                        "menu_path": full_name,
                        "container_path": parent_path,
                        "control_type": "MenuItemControl",
                        "shortcut": sc,
                        "ai_action": action_cmd,
                        "center_x": 0,
                        "center_y": 0,
                        "rect": {"left": 0, "top": 0, "width": 0, "height": 0},
                        "is_enabled": True,
                    })

    recurse_menu(hmenu)
    return items


def extract_uia_control_meta(child) -> dict:
    """Safely extracts value, tooltip, toggle state, automation ID and class from a UIA element."""
    meta = {
        "automation_id": "",
        "class_name": "",
        "help_text": "",
        "value": "",
        "toggle_state": None,
        "is_enabled": True,
    }
    try:
        meta["automation_id"] = getattr(child, "AutomationId", "") or ""
        meta["class_name"] = getattr(child, "ClassName", "") or ""
        meta["help_text"] = getattr(child, "HelpText", "") or ""
        meta["is_enabled"] = getattr(child, "IsEnabled", True)
    except Exception:
        pass

    try:
        vp = child.GetPattern(auto.PatternId.ValuePattern)
        if vp:
            meta["value"] = vp.Value or ""
    except Exception:
        pass

    try:
        tp = child.GetPattern(auto.PatternId.TogglePattern)
        if tp:
            # 0: Off, 1: On, 2: Indeterminate
            meta["toggle_state"] = tp.ToggleState
    except Exception:
        pass

    return meta


def deep_dive_app(
    window_search: str = "",
    max_depth: int = 25,
    max_elements: int = 1000,
    hwnd: int | None = None,
    background: bool = False,
) -> dict:
    """
    Supercharged Deep Dive Engine:
    Exhaustively indexes every menu hierarchy, toolbar, input field, tab, toggle,
    value, tooltip, and keyboard accelerator into persistent roadmap memory without cursor disruption.

    window_search may name the app ("notepad", "notepad.exe", "Settings") or part of a
    window title. hwnd targets an exact window instead. background=True is for scans
    the user did not ask for (session recorder): no focus change, no beep.
    """
    ensure_desktop()
    t0 = time.perf_counter()

    wins = list_windows()
    target_win = None
    if hwnd is not None:
        target_win = next((w for w in wins if w["hwnd"] == hwnd), None)
    elif window_search:
        target_win = find_app_window(window_search, wins)
    elif wins:
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
    identity = identify_window(hwnd)
    app_key = identity.key
    roadmap.refresh_app(app_key)

    if not background:
        focus_window(hwnd)
        time.sleep(0.12)

    # 1. Process Specs (for UWP apps, report the app's process, not ApplicationFrameHost)
    specs = get_window_process_specs(hwnd)
    if identity.exe and identity.exe != specs["exe_name"].lower():
        specs["host_exe"] = specs["exe_name"]
        specs["exe_name"] = identity.exe

    all_discovered = []
    seen_names = set()

    # 2. Legacy Win32 Menus (File -> Save As..., Edit -> Replace, etc.)
    try:
        menu_items = extract_win32_menu_items(hwnd)
        for mi in menu_items:
            k = mi["name"].lower()
            if k not in seen_names:
                seen_names.add(k)
                all_discovered.append(mi)
    except Exception:
        pass

    # 3. Exhaustive UIA Hierarchy Walk
    try:
        ctrl = auto.ControlFromHandle(hwnd)
        if ctrl:
            def walk(child_ctrl, depth=0, parent_breadcrumb=""):
                if depth > max_depth or len(all_discovered) >= max_elements:
                    return

                try:
                    for child in child_ctrl.GetChildren():
                        r = child.BoundingRectangle
                        w = r.right - r.left
                        h = r.bottom - r.top

                        raw_name = get_element_name(child)
                        current_breadcrumb = parent_breadcrumb
                        if raw_name and child.ControlTypeName in ("PaneControl", "GroupControl", "TabControl", "ToolBarControl"):
                            current_breadcrumb = f"{parent_breadcrumb} > {raw_name}" if parent_breadcrumb else raw_name

                        if is_interactive_control(child) and w > 0 and h > 0:
                            sc = getattr(child, "AcceleratorKey", "") or getattr(child, "AccessKey", "")
                            clean_name, final_sc = extract_shortcut_from_name(raw_name, fallback_shortcut=sc.strip() if sc else "")

                            k = clean_name.lower().strip()
                            if k and not k.startswith("(") and k not in seen_names:
                                seen_names.add(k)
                                meta = extract_uia_control_meta(child)
                                ct = child.ControlTypeName

                                if final_sc:
                                    ai_action = f"hotkey:{final_sc.lower()}"
                                elif any(t in ct for t in ("Edit", "ComboBox", "Spinner", "Document")):
                                    ai_action = f"fill:{clean_name}, <text>"
                                else:
                                    ai_action = f"click:{clean_name}"

                                all_discovered.append({
                                    "name": clean_name,
                                    "control_type": ct,
                                    "shortcut": final_sc,
                                    "access_key": sc.strip() if sc else "",
                                    "container_path": parent_breadcrumb,
                                    "automation_id": meta["automation_id"],
                                    "class_name": meta["class_name"],
                                    "help_text": meta["help_text"],
                                    "value": meta["value"],
                                    "toggle_state": meta["toggle_state"],
                                    "is_enabled": meta["is_enabled"],
                                    "ai_action": ai_action,
                                    "center_x": (r.left + r.right) // 2,
                                    "center_y": (r.top + r.bottom) // 2,
                                    "rect": {
                                        "left": r.left,
                                        "top": r.top,
                                        "width": w,
                                        "height": h,
                                    },
                                })

                        walk(child, depth + 1, current_breadcrumb)
                except Exception:
                    pass

            walk(ctrl)
    except Exception:
        pass

    # 4. Canvas / Game Engine Detection
    win_w = max(1, win_rect.get("right", 0) - win_rect.get("left", 0))
    win_h = max(1, win_rect.get("bottom", 0) - win_rect.get("top", 0))
    cached_elements = roadmap.map.get(app_key, {}).get("elements", {})
    known_count = sum(1 for e in cached_elements.values() if e.get("control_type") != "SpatialAnchor")
    canvas_info = detect_canvas_game_surface(
        specs["class_name"],
        len(all_discovered),
        win_w,
        win_h,
        known_count=known_count,
        truncated=len(all_discovered) >= max_elements,
        xaml_host=hosts_xaml_content(target_win["hwnd"]),
    )
    specs["is_canvas_game"] = canvas_info["is_canvas_game"]
    specs["engine"] = canvas_info["engine"]
    specs["canvas_advice"] = canvas_info["advice"]

    if not canvas_info["is_canvas_game"]:
        # Drop a fallback anchor left behind by an earlier false-positive detection.
        stale = cached_elements.get("canvas center / play")
        if stale and stale.get("control_type") == "SpatialAnchor":
            roadmap.remove_element(app_key, "canvas center / play")

    if canvas_info["is_canvas_game"]:
        cx = win_rect.get("left", 0) + win_w // 2
        cy = win_rect.get("top", 0) + win_h // 2
        if not any("canvas" in e["name"].lower() or "center" in e["name"].lower() for e in all_discovered):
            all_discovered.append({
                "name": "Canvas Center / Play",
                "control_type": "SpatialAnchor",
                "shortcut": "Space",
                "access_key": "",
                "container_path": "Canvas",
                "automation_id": "AnchorCenter",
                "class_name": specs["class_name"],
                "help_text": "Resolution-centered spatial anchor for canvas/game menus",
                "value": "",
                "toggle_state": None,
                "is_enabled": True,
                "ai_action": "click:Canvas Center / Play",
                "center_x": cx,
                "center_y": cy,
                "rect": {"left": cx - 50, "top": cy - 25, "width": 100, "height": 50},
            })

    # 5. Rich Categorization for Encyclopedia and AI Navigation
    categories = {
        "menus": [],
        "buttons": [],
        "inputs": [],
        "tabs": [],
        "toggles": [],
        "sliders": [],
        "links": [],
        "shortcuts": [],
        "others": [],
    }

    for item in all_discovered:
        ct = item.get("control_type", "")
        sc = item.get("shortcut", "")
        name = item.get("name", "")
        if sc:
            categories["shortcuts"].append({"name": name, "shortcut": sc, "action": item.get("ai_action", "")})

        if "Menu" in ct:
            categories["menus"].append(name)
        elif "Button" in ct or "ToolBar" in ct:
            categories["buttons"].append(name)
        elif any(t in ct for t in ("Edit", "ComboBox", "Spinner", "Document")):
            categories["inputs"].append(name)
        elif any(t in ct for t in ("Tab", "List", "Tree", "Item")):
            categories["tabs"].append(name)
        elif any(t in ct for t in ("Check", "Radio", "Toggle")):
            categories["toggles"].append(name)
        elif any(t in ct for t in ("Slider", "Thumb", "Scroll")):
            categories["sliders"].append(name)
        elif "Hyperlink" in ct:
            categories["links"].append(name)
        else:
            categories["others"].append(name)

    # 5. Save into the roadmap. New / cached counts come from what was actually
    # stored: learn_window drops transient content and renames some controls.
    before = set(roadmap.map.get(app_key, {}).get("elements", {}))
    roadmap.learn_window(
        identity,
        elements=all_discovered,
        window_rect=win_rect,
        process_info=specs,
        categories={k: len(v) for k, v in categories.items()},
        complete=len(all_discovered) < max_elements,
    )
    stored = roadmap.map.get(app_key, {}).get("elements", {})
    new_elements = [stored[k].get("name", k) for k in stored if k not in before]
    cached_names = [el.get("name", "") for el in stored.values() if el.get("control_type") != "HotkeyAction"]

    duration = round(time.perf_counter() - t0, 2)

    # 7. Record into unified scan history
    summary = f"Deep Dive found {len(all_discovered)} controls, {len(cached_names)} cached ({len(categories['shortcuts'])} shortcuts, {specs['exe_name'] or 'win32'}, PID: {specs['pid']})"
    if len(new_elements) > 0:
        summary = f"Deep Dive found {len(all_discovered)} controls, {len(cached_names)} cached (✨ {len(new_elements)} new, {specs['exe_name']}, PID: {specs['pid']})"

    record_scan_log(
        action="Deep Dive",
        app=app_key,
        summary=summary,
        count=len(all_discovered),
        new_count=len(new_elements),
        new_items=new_elements[:20],
        shortcuts_count=len(categories["shortcuts"]),
        items=cached_names[:30],
        duration=duration,
        status="success",
    )

    try:
        if not background:
            winsound.MessageBeep(0)
    except Exception:
        pass

    return {
        "status": "deep_dive_complete",
        "app": app_key,
        "window_title": title,
        "process_info": specs,
        "total_elements": len(all_discovered),
        "total_shortcuts": len(categories["shortcuts"]),
        "new_elements": new_elements,
        "new_count": len(new_elements),
        "duration_seconds": duration,
        "categories": {k: len(v) for k, v in categories.items()},
        "category_details": categories,
        "discovered_elements": all_discovered,
    }
