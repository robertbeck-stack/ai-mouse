"""
DeskDriver Application Hierarchy & Tree Mapping Engine.
Builds dynamic, semantic parent-child trees of desktop applications and Windows OS settings.
Maps exact navigation pathways (action chains) from root menus down to leaf actions
so AI agents and users can dynamically explore and execute nested commands with zero guesswork.
"""

from typing import Any

from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import list_windows
from deskdriver.automation.appid import identify_window, find_app_window
from deskdriver.navigation.roadmap import roadmap


WINDOWS_SETTINGS_TREE = {
    "System": [
        {"name": "Display (Scaling & Resolution)", "fastpath": "ms-settings:display", "action": "open:display"},
        {"name": "Sound (Volume & Output Devices)", "fastpath": "ms-settings:sound", "action": "open:sound"},
        {"name": "Notifications & Alerts", "fastpath": "ms-settings:notifications", "action": "open:notifications"},
        {"name": "Power & Battery (Sleep Timers)", "fastpath": "ms-settings:power", "action": "open:power"},
        {"name": "Storage (Storage Sense & Cleanup)", "fastpath": "ms-settings:storage", "action": "open:storage"},
        {"name": "About System (Specs & Windows Info)", "fastpath": "ms-settings:about", "action": "open:about"},
    ],
    "Bluetooth & Devices": [
        {"name": "Bluetooth Devices", "fastpath": "ms-settings:bluetooth", "action": "open:bluetooth"},
        {"name": "Printers & Scanners", "fastpath": "ms-settings:printers", "action": "open:printers"},
        {"name": "Mouse & Touchpad Settings", "fastpath": "ms-settings:mouse", "action": "open:mouse"},
    ],
    "Network & Internet": [
        {"name": "Wi-Fi Connections", "fastpath": "ms-settings:wifi", "action": "open:wifi"},
        {"name": "VPN Settings", "fastpath": "ms-settings:vpn", "action": "open:vpn"},
        {"name": "Network Status & Properties", "fastpath": "ms-settings:network", "action": "open:network"},
    ],
    "Personalization": [
        {"name": "Background & Wallpaper", "fastpath": "ms-settings:background", "action": "open:background"},
        {"name": "Colors (Dark / Light Theme)", "fastpath": "ms-settings:colors", "action": "open:colors"},
        {"name": "Themes & Sounds", "fastpath": "ms-settings:themes", "action": "open:themes"},
        {"name": "Lock Screen", "fastpath": "ms-settings:lockscreen", "action": "open:lockscreen"},
    ],
    "Apps": [
        {"name": "Installed Apps & Features", "fastpath": "ms-settings:apps", "action": "open:apps"},
        {"name": "Default Apps", "fastpath": "ms-settings:defaultapps", "action": "open:defaultapps"},
        {"name": "Startup Apps (Boot speed)", "fastpath": "ms-settings:startup", "action": "open:startup"},
    ],
    "Time & Language": [
        {"name": "Date & Time", "fastpath": "ms-settings:time", "action": "open:time"},
        {"name": "Region & Regional Format", "fastpath": "ms-settings:region", "action": "open:region"},
        {"name": "Language & Keyboard Layouts", "fastpath": "ms-settings:language", "action": "open:language"},
    ],
    "Privacy, Update & Security": [
        {"name": "Windows Update", "fastpath": "ms-settings:update", "action": "open:update"},
        {"name": "Windows Security (Defender)", "fastpath": "windowsdefender:", "action": "open:security"},
        {"name": "Accessibility (Display Scaling, High Contrast)", "fastpath": "ms-settings:accessibility", "action": "open:accessibility"},
    ],
}


STANDARD_MENU_HIERARCHY = {
    "notepad.exe": {
        "File": [
            {"name": "New tab", "shortcut": "Ctrl+N"},
            {"name": "New window", "shortcut": "Ctrl+Shift+N"},
            {"name": "Open...", "shortcut": "Ctrl+O"},
            {"name": "Save", "shortcut": "Ctrl+S"},
            {"name": "Save as...", "shortcut": "Ctrl+Shift+S"},
            {"name": "Save all", "shortcut": "Ctrl+Alt+S"},
            {"name": "Close tab", "shortcut": "Ctrl+W"},
            {"name": "Close window", "shortcut": "Ctrl+Shift+W"},
            {"name": "Exit", "shortcut": "Alt+F4"},
        ],
        "Edit": [
            {"name": "Undo", "shortcut": "Ctrl+Z"},
            {"name": "Redo", "shortcut": "Ctrl+Y"},
            {"name": "Cut", "shortcut": "Ctrl+X"},
            {"name": "Copy", "shortcut": "Ctrl+C"},
            {"name": "Paste", "shortcut": "Ctrl+V"},
            {"name": "Delete", "shortcut": "Del"},
            {"name": "Find", "shortcut": "Ctrl+F"},
            {"name": "Find next", "shortcut": "F3"},
            {"name": "Replace", "shortcut": "Ctrl+H"},
            {"name": "Go to...", "shortcut": "Ctrl+G"},
            {"name": "Select all", "shortcut": "Ctrl+A"},
            {"name": "Time/Date", "shortcut": "F5"},
            {"name": "Font...", "shortcut": ""},
        ],
        "View": [
            {"name": "Zoom in", "shortcut": "Ctrl+Plus"},
            {"name": "Zoom out", "shortcut": "Ctrl+Minus"},
            {"name": "Restore default zoom", "shortcut": "Ctrl+0"},
            {"name": "Status bar", "shortcut": ""},
            {"name": "Word wrap", "shortcut": "Alt+Z"},
        ],
    },
    "mspaint.exe": {
        "File": [
            {"name": "New", "shortcut": "Ctrl+N"},
            {"name": "Open", "shortcut": "Ctrl+O"},
            {"name": "Save", "shortcut": "Ctrl+S"},
            {"name": "Save as", "shortcut": "F12"},
            {"name": "Print", "shortcut": "Ctrl+P"},
            {"name": "Exit", "shortcut": "Alt+F4"},
        ],
        "Edit": [
            {"name": "Undo", "shortcut": "Ctrl+Z"},
            {"name": "Redo", "shortcut": "Ctrl+Y"},
            {"name": "Cut", "shortcut": "Ctrl+X"},
            {"name": "Copy", "shortcut": "Ctrl+C"},
            {"name": "Paste", "shortcut": "Ctrl+V"},
            {"name": "Select all", "shortcut": "Ctrl+A"},
        ],
        "View": [
            {"name": "Zoom in", "shortcut": "Ctrl+Page Up"},
            {"name": "Zoom out", "shortcut": "Ctrl+Page Down"},
            {"name": "Full screen", "shortcut": "F11"},
            {"name": "Rulers", "shortcut": "Ctrl+R"},
            {"name": "Gridlines", "shortcut": "Ctrl+G"},
        ],
    },
}


def build_application_tree(app_query: str) -> dict[str, Any]:
    """
    Build a dynamic hierarchical navigation tree for a desktop application or Windows OS settings.
    Returns branches (parent menus, toolbars, tabs, settings) with pre-computed action chains.
    """
    ensure_desktop()
    q = (app_query or "").strip().lower()

    # 1. OS Settings Tree
    if q in ("settings", "ms-settings", "windows settings", "os settings", "systemsettings", "systemsettings.exe"):
        branches = []
        for cat_name, items in WINDOWS_SETTINGS_TREE.items():
            children = []
            for item in items:
                children.append({
                    "name": item["name"],
                    "control_type": "SettingsOption",
                    "shortcut": "",
                    "parent": cat_name,
                    "action_chain": item["action"],
                    "fastpath": item["fastpath"],
                })
            branches.append({
                "name": cat_name,
                "type": "CategoryFolder",
                "count": len(children),
                "children": children,
            })
        return {
            "app": "Windows Settings",
            "is_settings": True,
            "total_categories": len(branches),
            "total_items": sum(b["count"] for b in branches),
            "tree": branches,
        }

    # 2. Match Target Application Window & Roadmap Cache
    # The cached app (by key, exe or display name) - works even when no window is open
    matched_app_key = roadmap.resolve_app_key(app_query or "")
    target_win = find_app_window(app_query or "", list_windows()) if q else None
    if not matched_app_key and target_win:
        matched_app_key = identify_window(target_win["hwnd"]).key
    if not matched_app_key:
        matched_app_key = app_query if (app_query or "") in roadmap.map else (q or "unknown")

    cached_elements = roadmap.map.get(matched_app_key, {}).get("elements", {})

    # Categorize elements into dynamic tree branches
    menus_branch = []
    tabs_branch = []
    tools_branch = []
    settings_branch = []
    window_branch = []
    other_branch = []

    # Check for known sub-menus
    std_menus = STANDARD_MENU_HIERARCHY.get(matched_app_key.split("/", 1)[0].lower(), {}) if "/" not in matched_app_key else {}
    populated_menus = set()

    # Build Menu Hierarchy from std_menus
    for menu_name, sub_items in std_menus.items():
        children = []
        for item in sub_items:
            sc = item.get("shortcut", "")
            action_chain = f"click:{menu_name} | click:{item['name']}"
            if sc:
                action_chain = f"hotkey:{sc.lower()}"
            children.append({
                "name": item["name"],
                "control_type": "MenuItemControl",
                "shortcut": sc,
                "parent": menu_name,
                "action_chain": action_chain,
            })
        menus_branch.append({
            "name": f"{menu_name} Menu",
            "type": "MenuFolder",
            "parent_button": menu_name,
            "count": len(children),
            "children": children,
        })
        populated_menus.add(menu_name.lower())

    # Now categorize discovered roadmap elements
    for el_name, el_data in cached_elements.items():
        name = el_data.get("name") or el_name
        ct = el_data.get("control_type", "")
        sc = el_data.get("shortcut", "")
        nl = name.lower()

        # If it's a top-level menu button we already expanded, skip duplicate
        if nl in populated_menus:
            continue

        item_entry = {
            "name": name,
            "control_type": ct,
            "shortcut": sc,
            "parent": el_data.get("parent", ""),
            "action_chain": f"click:{name}",
        }
        if sc:
            item_entry["action_chain"] = f"hotkey:{sc.lower()}"

        if "Menu" in ct:
            menus_branch.append({
                "name": name,
                "type": "MenuItemControl",
                "count": 1,
                "children": [item_entry],
            })
        elif "Tab" in ct or "Item" in ct or "tab" in nl:
            tabs_branch.append(item_entry)
        elif "Settings" in name or "Avatar" in name or "Account" in name or "what's new" in nl:
            settings_branch.append(item_entry)
        elif name in ("Minimise", "Maximise", "Close", "Restore"):
            window_branch.append(item_entry)
        elif "Button" in ct or "ToolBar" in ct or "Edit" in ct:
            tools_branch.append(item_entry)
        else:
            other_branch.append(item_entry)

    # Assemble complete tree branches
    final_tree = []
    if menus_branch:
        final_tree.append({
            "name": "📂 Menu Bar & Commands",
            "description": "Top-level application menus and command options",
            "count": sum(b.get("count", len(b.get("children", []))) for b in menus_branch),
            "sub_branches": menus_branch,
        })
    if tabs_branch:
        final_tree.append({
            "name": "🗂️ Tabs & Document Views",
            "description": "Active document tabs and navigation controls",
            "count": len(tabs_branch),
            "children": tabs_branch,
        })
    if tools_branch:
        final_tree.append({
            "name": "🛠️ Tools, Toolbars & Inputs",
            "description": "Buttons, formatting options, and interactive controls",
            "count": len(tools_branch),
            "children": tools_branch,
        })
    if settings_branch:
        final_tree.append({
            "name": "⚙️ Settings & Options",
            "description": "Preferences, profiles, and configuration buttons",
            "count": len(settings_branch),
            "children": settings_branch,
        })
    if window_branch:
        final_tree.append({
            "name": "🪟 Window Controls",
            "description": "Minimize, maximize, restore, and close buttons",
            "count": len(window_branch),
            "children": window_branch,
        })
    if other_branch:
        final_tree.append({
            "name": "📊 Status Bar & Additional Controls",
            "description": "Status panels, zoom controls, and metadata",
            "count": len(other_branch),
            "children": other_branch,
        })

    total_controls = sum(b.get("count", 0) for b in final_tree)

    return {
        "app": matched_app_key,
        "window_title": target_win["title"] if target_win else matched_app_key,
        "total_branches": len(final_tree),
        "total_controls": total_controls,
        "tree": final_tree,
    }
