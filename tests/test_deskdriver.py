"""
Self-check test suite for DeskDriver (and backward compatibility shim ai_mouse).
"""

import sys
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

import deskdriver as dd
import ai_mouse as am


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
    print("Testing dashboard scan logging & history tracking...")
    import dashboard
    entry = dashboard.add_scan_log(
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
    assert entry["action"] == "Deep Dive"
    assert entry["app"] == "testapp"
    assert entry["new_count"] == 4
    assert len(entry["new_items"]) == 4
    assert len(dashboard.SCAN_LOGS) > 0
    assert dashboard.SCAN_LOGS[0]["app"] == "testapp"
    print(f" -> Dashboard scan logging active (latest: {dashboard.SCAN_LOGS[0]['summary']}, new: {dashboard.SCAN_LOGS[0]['new_count']})")


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
    assert np_tree["app"] == "notepad"
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
    print("\nALL DESKDRIVER TESTS PASSED!")


if __name__ == "__main__":
    run_all()
