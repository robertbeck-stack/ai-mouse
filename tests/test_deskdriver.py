"""
Self-check test suite for DeskDriver (and backward compatibility shim ai_mouse).
"""

import atexit
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add src and root to path
root_path = Path(__file__).parent.parent
src_path = root_path / "src"
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Run against a throwaway copy of the data so tests never write to the real roadmap,
# scan history or saved actions (the copy keeps tests that need learned apps working).
REAL_DATA_FILES = ["ui_roadmap", "scan_history.json", "saved_actions.json"]
TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="deskdriver-test-"))
for _name in REAL_DATA_FILES:
    _src = root_path / _name
    if _src.is_dir():
        shutil.copytree(_src, TEST_DATA_DIR / _name)
    elif _src.exists():
        shutil.copy2(_src, TEST_DATA_DIR / _name)
os.environ["DESKDRIVER_DATA_DIR"] = str(TEST_DATA_DIR)
atexit.register(shutil.rmtree, TEST_DATA_DIR, True)


def _real_data_fingerprint() -> str:
    h = hashlib.sha256()
    for name in REAL_DATA_FILES:
        base = root_path / name
        files = sorted(base.rglob("*")) if base.is_dir() else [base]
        for f in files:
            if f.is_file():
                h.update(str(f.relative_to(root_path)).encode())
                h.update(f.read_bytes())
    return h.hexdigest()


REAL_DATA_BEFORE = _real_data_fingerprint()

import deskdriver as dd  # noqa: E402  (must come after DESKDRIVER_DATA_DIR is set)
import ai_mouse as am  # noqa: E402


def test_shim_parity():
    print("Testing backward-compatibility shim parity (deskdriver vs ai_mouse)...")
    assert am.get_mouse_position is dd.get_mouse_position
    assert am.move_mouse is dd.move_mouse
    assert am.mouse_click is dd.mouse_click
    assert am.type_text is dd.type_text
    assert am.press_hotkey is dd.press_hotkey
    assert am.list_windows is dd.list_windows
    assert am.roadmap is dd.roadmap
    assert am.snap_window is dd.snap_window
    assert am.clipboard_paste is dd.clipboard_paste
    assert am.record_element_at_cursor is dd.record_element_at_cursor
    assert am.wait_for_window is dd.wait_for_window
    assert am.wait_for_element is dd.wait_for_element
    assert am.wait_and_click is dd.wait_and_click
    assert am.auto_record_window is dd.auto_record_window
    assert am.deep_dive_app is dd.deep_dive_app
    print(" -> Backward-compatibility shim matches deskdriver 100%")


def test_core_mouse():
    print("Testing core mouse...")
    pos = dd.get_mouse_position()
    assert isinstance(pos, tuple) and len(pos) == 2
    assert pos[0] >= 0 and pos[1] >= 0
    print(f" -> Cursor position: {pos}")


def test_window_enumeration():
    print("Testing window enumeration...")
    wins = dd.list_windows()
    assert isinstance(wins, list)
    print(f" -> Found {len(wins)} active windows")


def test_element_inspection():
    print("Testing element inspection...")
    el = dd.get_element_under_cursor()
    assert isinstance(el, dict)
    print(f" -> Under cursor: {el.get('name')!r} ({el.get('control_type')})")


def test_roadmap_lookup():
    print("Testing roadmap cache...")
    stats = dd.roadmap.map
    assert isinstance(stats, dict)
    print(f" -> Cached apps in roadmap: {len(stats)}")


def test_keyboard_support():
    print("Testing keyboard hotkey definitions...")
    from deskdriver.core.keyboard import _get_vk_code, COMMON_HOTKEYS
    assert _get_vk_code("ctrl") == 0x11
    assert _get_vk_code("enter") == 0x0D
    assert "save" in COMMON_HOTKEYS
    assert COMMON_HOTKEYS["save"] == "ctrl+s"
    print(f" -> Universal hotkeys registered: {len(COMMON_HOTKEYS)}")


def test_hotkeys_extraction():
    print("Testing hotkey extraction...")
    from deskdriver.navigation.hotkeys import extract_shortcut_from_name, get_app_hotkeys
    name, sc = extract_shortcut_from_name("Bold (Ctrl+B)")
    assert name == "Bold" and sc == "Ctrl+B"
    name, sc = extract_shortcut_from_name("Save File (Ctrl+Shift+S)")
    assert name == "Save File" and sc == "Ctrl+Shift+S"
    notepad_keys = get_app_hotkeys("Notepad")
    assert len(notepad_keys) > 10
    print(f" -> Notepad hotkeys recognized: {len(notepad_keys)}")


def test_mouse_features():
    print("Testing scroll and drag functions...")
    assert callable(dd.mouse_scroll)
    assert callable(dd.drag_and_drop)
    # Perform a subtle zero-distance or safe scroll
    dd.mouse_scroll(0)
    print(" -> Mouse scroll & drag callable verified")


def test_dpi_awareness():
    print("Testing DPI awareness...")
    from deskdriver.core.desktop import enable_dpi_awareness
    enable_dpi_awareness()
    print(" -> DPI awareness enabled")


def test_responsive_anchors_and_fill():
    print("Testing responsive anchors and fill_input...")
    assert callable(dd.fill_input)

    # Test anchor calculation in memory
    rect1 = {"left": 100, "top": 100, "right": 1100, "bottom": 800}
    test_elements = [
        {"name": "CloseBtn", "control_type": "Button", "center_x": 1050, "center_y": 120, "rect": {"width": 30, "height": 30}},
        {"name": "SaveBtn", "control_type": "Button", "center_x": 150, "center_y": 120, "rect": {"width": 30, "height": 30}},
    ]
    dd.roadmap.learn_window("TestAppAnchor", test_elements, rect1)

    # Now simulate resized window: width expanded from 1000 to 1400
    rect2 = {"left": 100, "top": 100, "right": 1500, "bottom": 800}
    cached_close = dd.roadmap.find_cached_element("TestAppAnchor", "CloseBtn", rect2)
    assert cached_close is not None
    # CloseBtn was 50px from right in rect1 (1100 - 1050). In rect2 (right=1500), it should be 1500 - 50 = 1450!
    assert cached_close["center_x"] == 1450
    print(f" -> Responsive right-anchor dynamically recalculated: {cached_close['center_x']}")


def test_sync_and_sanitizer():
    print("Testing cloud sync sanitizer skeleton...")
    from deskdriver.sync import sanitize_app_profile, CloudSyncClient

    sample_app_data = {
        "elements": {
            "save": {"name": "Save File", "control_type": "ButtonControl", "shortcut": "Ctrl+S"},
            "private_path": {"name": "C:\\Users\\Robert\\Secrets.txt", "control_type": "EditControl"},
            "email_button": {"name": "Send to john@example.com", "control_type": "ButtonControl"},
            "print": {"name": "Print", "control_type": "ButtonControl", "shortcut": "Ctrl+P"},
        }
    }
    sanitized = sanitize_app_profile("PersonalDoc - Notepad", sample_app_data)
    assert sanitized["app"] == "notepad"
    assert "save" in sanitized["elements"]
    assert "print" in sanitized["elements"]
    assert "private_path" not in sanitized["elements"]
    assert "email_button" not in sanitized["elements"]

    client = CloudSyncClient()
    res = client.upload_to_community("notepad", sample_app_data, public_consent=False)
    assert "error" in res  # Without consent, blocked
    res_ok = client.upload_to_community("notepad", sample_app_data, public_consent=True)
    assert res_ok["status"] == "skeleton_queued"
    print(" -> Sanitizer & Sync skeleton verified")


def test_clipboard():
    print("Testing native Win32 clipboard...")
    test_str = "DeskDriver_Clipboard_Test_§$%&_123"
    ok = dd.set_clipboard_text(test_str)
    assert ok is True
    read_back = dd.get_clipboard_text()
    assert read_back == test_str
    assert callable(dd.clipboard_paste)
    print(" -> Clipboard read/write roundtrip verified")


def test_window_snapping():
    print("Testing window snapping & sizing API...")
    assert callable(dd.snap_window)
    assert callable(dd.maximize_window)
    assert callable(dd.minimize_window)
    assert callable(dd.move_window)
    # Check find_window_hwnd on nonexistent window
    from deskdriver.automation.windows import find_window_hwnd
    assert find_window_hwnd("NonExistentWindow_12345XYZ") is None
    print(" -> Window management callables verified")


def test_record_on_hover():
    print("Testing record on hover...")
    res = dd.record_element_at_cursor(custom_name="SelfCheckTestButton")
    assert res["status"] == "element_recorded"
    assert "app" in res
    assert res["element"] == "SelfCheckTestButton"
    # Verify it exists in memory roadmap
    app_key = res["app"]
    assert "selfchecktestbutton" in dd.roadmap.map[app_key]["elements"]
    print(f" -> Hover recorded into roadmap for app: {app_key}")


def test_multimonitor_and_waiting():
    print("Testing multi-monitor work area detection...")
    wins = dd.list_windows()
    assert len(wins) > 0
    from deskdriver.automation.windows import get_window_monitor_work_area
    work = get_window_monitor_work_area(wins[0]["hwnd"])
    assert "width" in work and work["width"] > 200
    assert "height" in work and work["height"] > 200
    print(f" -> Monitor work area for active window: {work['width']}x{work['height']} (offset {work['left']},{work['top']})")

    print("Testing smart waiting primitives...")
    # Timeout check
    t0 = dd.wait_for_window("NonExistentWindow_99999", timeout=0.08)
    assert t0 is None

    # Found check
    target_title = wins[0]["title"][:15]
    found = dd.wait_for_window(target_title, timeout=1.0)
    assert found is not None
    assert "hwnd" in found
    print(f" -> Smart wait resolved window {target_title!r} instantly")

    # Element wait check on cached element
    cached_el = dd.wait_for_element("SelfCheckTestButton", timeout=0.5)
    assert cached_el is not None
    print(" -> Smart wait resolved cached element")


def test_auto_record():
    print("Testing auto_record_window...")
    wins = dd.list_windows()
    if wins:
        res = dd.auto_record_window(window_search=wins[0]["title"], move_cursor=False, max_elements=2)
        assert res["status"] == "auto_recorded"
        assert "app" in res
        print(f" -> Auto-recorded {res.get('count', 0)} controls for {res['app']}")


def test_deep_dive():
    print("Testing deep_dive_app engine...")
    wins = dd.list_windows()
    if wins:
        res = dd.deep_dive_app(window_search=wins[0]["title"], max_depth=4, max_elements=5)
        assert res["status"] == "deep_dive_complete"
        assert "total_elements" in res
        assert "categories" in res
        print(f" -> Deep dive indexed {res['total_elements']} elements for {res['app']}")


def test_dashboard_scan_logging():
    print("Testing dashboard API, request guards & scan history...")
    import json as _json
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    import dashboard

    entry = dashboard.record_scan_log(
        action="Deep Dive",
        app="testapp",
        summary="Test deep dive scan",
        count=12,
        new_count=4,
        new_items=["Settings", "New File", "Close", "Save"],
        shortcuts_count=3,
        items=["File", "Edit", "Save"],
        duration=0.15,
    )
    assert entry["action"] == "Deep Dive" and entry["new_count"] == 4

    server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard.DashboardHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def call(path, body=None, headers=None):
        data = _json.dumps(body).encode() if isinstance(body, (dict, list)) else body
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    try:
        status, raw = call("/api/logs")
        logs = _json.loads(raw)["logs"]
        assert status == 200 and logs[0]["app"] == "testapp"
        assert call("/")[0] == 200
        assert call("/api/stats")[0] == 200
        # Guards: cross-site origin and DNS-rebinding host are refused
        assert call("/api/run_action", {"action": "wait:0"}, {"Origin": "https://evil.example"})[0] == 403
        assert call("/api/stats", headers={"Host": "evil.example"})[0] == 403
        # Bad input gives JSON errors instead of a dropped connection
        assert call("/api/run_action", b"{oops", {"Content-Type": "application/json"})[0] == 400
        assert call("/api/run_action", {})[0] == 400
        assert call("/api/nope")[0] == 404
        status, raw = call("/api/run_action", {"action": "wait:0.01"})
        assert status == 200 and _json.loads(raw)["status"] == "completed"
    finally:
        server.shutdown()
        server.server_close()
    print(" -> Dashboard API, guards and scan logging verified")


def test_action_pipeline():
    print("Testing action pipeline engine...")
    test_str = "open:notepad | wait:0.02 | hotkey:ctrl+n | type:test | snap:left"
    steps = dd.parse_action_string(test_str)
    assert len(steps) == 5
    assert steps[0]["verb"] == "open"
    assert steps[0]["arg"] == "notepad"
    assert steps[1]["verb"] == "wait"
    assert steps[2]["verb"] == "hotkey"
    assert steps[3]["verb"] == "type"
    assert steps[4]["verb"] == "snap"

    # Test saving & loading actions
    save_res = dd.save_action("unit_test_action", "wait:0.01 | wait:0.02")
    assert save_res["status"] == "saved"
    actions = dd.load_saved_actions()
    assert "unit_test_action" in actions
    assert actions["unit_test_action"] == "wait:0.01 | wait:0.02"

    # Test execution of safe string
    exec_res = dd.execute_action("wait:0.01 | wait:0.01", interval=0.0)
    assert exec_res["status"] == "completed"
    assert exec_res["steps_count"] == 2
    assert exec_res["steps_executed"] == 2

    # Clean up
    assert dd.delete_action("unit_test_action") is True
    print(f" -> Action pipeline verified: parsing, storage, and execution OK ({exec_res['steps_count']} steps in {exec_res['duration_seconds']}s)")


def test_application_tree():
    print("Testing dynamic application hierarchy & tree mapping...")
    # 1. OS Settings Tree
    settings_tree = dd.build_application_tree("settings")
    assert settings_tree["is_settings"] is True
    assert settings_tree["total_categories"] >= 5
    assert len(settings_tree["tree"]) >= 5
    assert "System" in [b["name"] for b in settings_tree["tree"]]
    # Verify pre-computed action chain
    first_cat = settings_tree["tree"][0]
    assert len(first_cat["children"]) > 0
    assert "action_chain" in first_cat["children"][0]
    assert first_cat["children"][0]["action_chain"].startswith("open:")

    # 2. Notepad Tree
    np_tree = dd.build_application_tree("notepad")
    assert np_tree["app"] == "notepad.exe"
    assert np_tree["total_branches"] > 0
    assert len(np_tree["tree"]) > 0
    # Check that Menu Bar exists
    menu_branch = next((b for b in np_tree["tree"] if "Menu" in b["name"]), None)
    assert menu_branch is not None
    assert len(menu_branch.get("sub_branches", [])) > 0
    file_sub = menu_branch["sub_branches"][0]
    assert "children" in file_sub and len(file_sub["children"]) > 0
    assert "action_chain" in file_sub["children"][0]
    print(f" -> Dynamic tree hierarchy verified: Settings ({settings_tree['total_items']} options) & Notepad ({np_tree['total_controls']} controls mapped)")


def test_session_recorder():
    print("Testing SessionRecorder live monitoring...")
    status_init = dd.get_recording_status()
    assert isinstance(status_init, dict)
    assert status_init.get("recording") is False

    res_start = dd.start_recording()
    assert res_start.get("status") == "recording_started"
    status_active = dd.get_recording_status()
    assert status_active.get("recording") is True

    # Stop recording
    res_stop = dd.stop_recording()
    assert res_stop.get("status") == "recording_stopped"
    assert "pipeline" in res_stop
    assert "actions_count" in res_stop
    assert "visited_apps" in res_stop

    status_after = dd.get_recording_status()
    assert status_after.get("recording") is False
    print(f" -> Live SessionRecorder lifecycle verified (pipeline: '{res_stop.get('pipeline')}')")


def test_review_regressions():
    """Pure-logic checks for fixes from the code review (no desktop interaction, no disk writes)."""
    import sys as _sys
    import tempfile
    print("Testing review regressions (canvas detection, matching, parsing, storage)...")
    from deskdriver.navigation.deepdive import detect_canvas_game_surface
    rm = _sys.modules["deskdriver.navigation.roadmap"]

    # Canvas heuristic: UIA frameworks and capped / already-known scans are never canvases
    assert not detect_canvas_game_surface("ApplicationFrameWindow", 2, 1200, 800)["is_canvas_game"]
    assert not detect_canvas_game_surface("Chrome_WidgetWin_1", 3, 1200, 800, known_count=2000)["is_canvas_game"]
    assert not detect_canvas_game_surface("MyEngineWnd", 5, 1200, 800, truncated=True)["is_canvas_game"]
    assert detect_canvas_game_surface("UnityWndClass", 50, 1200, 800)["is_canvas_game"]
    assert detect_canvas_game_surface("MyEngineWnd", 1, 1200, 800)["is_canvas_game"]

    # App identity is the executable; shared hosts are qualified by window class
    from deskdriver.automation import appid
    assert appid.key_for("Notepad.exe", "Notepad") == "notepad.exe"
    assert appid.key_for("explorer.exe", "CabinetWClass") == "explorer.exe"
    assert appid.key_for("explorer.exe", "Shell_TrayWnd") == "explorer.exe#shell_traywnd"
    assert appid.key_for("", "TaskManagerWindow") == "#taskmanagerwindow"
    assert appid.display_name_for("mspaint.exe") == "Paint"
    assert appid.surface_name("Page setup") == "page setup"
    # Every open window resolves to an identity, and an app can be found by name
    for w in dd.list_windows()[:5]:
        ident = appid.identify_window(w["hwnd"])
        assert ident.key and ident.display_name
        assert appid.find_app_window(ident.key, [w]) is w

    # Schema 1 (title keys) -> schema 2 (executable keys)
    from deskdriver.navigation.roadmap_migrate import migrate_entries
    old = {
        "notepad": {"elements": {"save": {"name": "Save"}}, "last_updated": 1},
        "*notes - Notepad": {"elements": {"open": {"name": "Open"}}, "last_updated": 2,
                             "process_info": {"exe_name": "Notepad.exe", "class_name": "Notepad"}},
        "Page setup": {"elements": {"ok": {"name": "OK"}}, "last_updated": 3,
                       "process_info": {"exe_name": "Notepad.exe", "class_name": "#32770"}},
        "Untitled - Paint": {"elements": {}, "last_updated": 1},
        "Bank_Statement.pdf - Viewer": {"elements": {"x": {}}, "last_updated": 1},
    }
    migrated, unmigrated = migrate_entries(old)
    assert set(migrated) == {"notepad.exe", "notepad.exe/page setup", "mspaint.exe"}
    assert set(migrated["notepad.exe"]["elements"]) == {"save", "open"}
    assert migrated["notepad.exe"]["display_name"] == "Notepad"
    assert migrated["notepad.exe/page setup"]["surface"] == "page setup"
    assert list(unmigrated) == ["Bank_Statement.pdf - Viewer"]
    assert "*notes - Notepad" not in str(migrated)  # window titles are not carried over

    # Element matching: no reverse-substring hits ("ok" must not match "bookmark")
    els = {"ok": 1, "bookmark this tab": 1, "save": 1, "save as": 1}
    assert rm.match_element_key(els, "bookmark") == "bookmark this tab"
    assert rm.match_element_key(els, "save") == "save"
    assert rm.match_element_key({"ok": 1}, "bookmark") is None

    # Drag coordinates with a bare "->" stay one step
    steps = dd.parse_action_string("drag:10,10->200,200 | key:enter")
    assert [st["raw"] for st in steps] == ["drag:10,10->200,200", "key:enter"]

    # Per-app storage round-trip, change-only writes and deletion
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        d = Path(tmp) / "ui_roadmap"
        r = rm.UIRoadmap(directory=d, legacy_file=None)
        r.map["Admin: Prompt"] = {"elements": {"x": {"name": "X"}}, "schema": 2}
        r.map["taskbar"] = {"elements": {}, "schema": 2}
        r.map["Taskbar"] = {"elements": {}, "schema": 2}
        r.save()
        names = sorted(f.name for f in d.glob("*.json"))
        assert "admin-prompt.json" in names and "taskbar.json" in names and len(names) == 3
        r2 = rm.UIRoadmap(directory=d, legacy_file=None)
        assert r2.map == r.map
        del r2.map["Admin: Prompt"]
        r2.save()
        assert not (d / "admin-prompt.json").exists()

        # Two instances = two processes sharing the directory
        rect = {"left": 0, "top": 0, "right": 100, "bottom": 100}
        el = lambda n: {"name": n, "center_x": 5, "center_y": 5, "rect": {"width": 4, "height": 4}}  # noqa: E731
        a = rm.UIRoadmap(directory=d, legacy_file=None)
        b = rm.UIRoadmap(directory=d, legacy_file=None)
        a.learn_window("Weird App", [el("from a")], rect)
        b.learn_window("Weird App", [el("from b")], rect)  # b never saw a's write; must merge, not clobber
        a.refresh_app("Weird App")
        assert {"from a", "from b"} <= set(a.map["Weird App"]["elements"])
        assert a.remove_element("Weird App", "from a")
        b.learn_window("Weird App", [el("from b 2")], rect)  # stale b still holds "from a"
        final = rm.UIRoadmap(directory=d, legacy_file=None).map["Weird App"]["elements"]
        assert "from a" not in final and {"from b", "from b 2"} <= set(final)

        # Document / browser tabs, web content and secrets are never cached
        from deskdriver.navigation.element_filter import is_transient, redact_secrets
        tab = {"name": "notes.txt. Modified.", "control_type": "TabItemControl"}
        assert is_transient(tab, "notepad.exe")
        assert is_transient({"name": "Gmail - Memory usage - 280 MB", "control_type": "DataItemControl"}, "brave.exe")
        assert is_transient({"name": "reddit", "control_type": "HyperlinkControl"}, "brave.exe")
        assert is_transient({"name": "Go", "control_type": "ButtonControl",
                             "container_path": "pane > Chrome Legacy Window > id:wikiArticle"}, "antigravity.exe")
        assert is_transient({"name": "~ ai-mouse", "control_type": "TabItemControl",
                             "container_path": "pane > id:TabView"}, "windowsterminal.exe")
        assert is_transient({"name": "sk-ant-api03-abcDEF123. Modified", "control_type": "ButtonControl"})
        assert not is_transient({"name": "Reload", "control_type": "ButtonControl"}, "brave.exe")
        assert not is_transient({"name": "View", "control_type": "TabItemControl",
                                 "container_path": "id:12320"}, "explorer.exe")
        assert redact_secrets("key sk-ant-api03-abc_DEF-1 here") == "key [REDACTED] here"

        a.learn_window("notepad.exe", [el("Save"), {**el("todo.txt. Modified."), "control_type": "TabItemControl"}], rect)
        assert "save" in a.map["notepad.exe"]["elements"]
        assert not any("todo" in k for k in a.map["notepad.exe"]["elements"])
        a.map["notepad.exe"]["elements"]["old tab. unmodified."] = {"name": "old tab. Unmodified."}
        assert a.prune_transient() == {"notepad.exe": 1}
        assert "old tab. unmodified." not in rm.UIRoadmap(directory=d, legacy_file=None).map["notepad.exe"]["elements"]

        # "explorer" means File Explorer, not the taskbar that shares its exe
        a.map["explorer.exe#shell_traywnd"] = {"elements": {}, "schema": 2, "exe": "explorer.exe", "display_name": "Tray Test"}
        a.map["explorer.exe"] = {"elements": {}, "schema": 2, "exe": "explorer.exe", "display_name": "File Explorer"}
        assert a.resolve_app_key("explorer") == "explorer.exe"
        assert a.resolve_app_key("tray test") == "explorer.exe#shell_traywnd"
        from deskdriver.automation.appid import AppIdentity, app_matches
        tray = AppIdentity("explorer.exe#shell_traywnd", "explorer.exe", "Taskbar", "shell_traywnd", "")
        files = AppIdentity("explorer.exe", "explorer.exe", "File Explorer", "cabinetwclass", "")
        assert not app_matches(tray, "explorer") and app_matches(tray, "taskbar")
        assert app_matches(files, "explorer") and app_matches(files, "explorer.exe")
    print(" -> Review regressions verified")


def test_module_layering():
    """Each module may only import deskdriver modules from its own layer or below."""
    import ast
    print("Testing module layering (paths/core -> automation -> navigation -> workflows)...")
    ranks = {"paths": 0, "core": 1, "sync": 1, "automation": 2, "navigation": 3, "workflows": 4, "server": 5}
    pkg = src_path / "deskdriver"

    def layer_of(dotted: str):
        parts = dotted.split(".")
        return ranks.get(parts[1]) if len(parts) > 1 and parts[0] == "deskdriver" else None

    violations = []
    for f in pkg.rglob("*.py"):
        rel = f.relative_to(src_path).with_suffix("")
        mod = ".".join(rel.parts)
        if mod == "deskdriver.__init__":
            continue  # the package facade re-exports every layer
        own = layer_of(mod)
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            for name in names:
                dep = layer_of(name)
                if own is not None and dep is not None and dep > own:
                    violations.append(f"{mod} -> {name}")
    assert not violations, "Layering violations: " + ", ".join(violations)
    print(" -> No upward imports")


def test_real_data_untouched():
    print("Testing that the real roadmap / history / actions were not modified...")
    assert _real_data_fingerprint() == REAL_DATA_BEFORE, "tests wrote to the real data files"
    print(f" -> Real data untouched (tests used {TEST_DATA_DIR})")


def run_all():
    test_shim_parity()
    test_core_mouse()
    test_window_enumeration()
    test_element_inspection()
    test_roadmap_lookup()
    test_keyboard_support()
    test_hotkeys_extraction()
    test_mouse_features()
    test_dpi_awareness()
    test_responsive_anchors_and_fill()
    test_sync_and_sanitizer()
    test_clipboard()
    test_window_snapping()
    test_record_on_hover()
    test_multimonitor_and_waiting()
    test_auto_record()
    test_deep_dive()
    test_dashboard_scan_logging()
    test_action_pipeline()
    test_application_tree()
    test_session_recorder()
    test_review_regressions()
    test_module_layering()
    test_real_data_untouched()
    print("\nALL DESKDRIVER TESTS PASSED!")


if __name__ == "__main__":
    run_all()

