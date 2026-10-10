"""
Self-check test suite for DeskDriver (and backward compatibility shim ai_mouse).
"""

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
src_path = Path(__file__).parent.parent / "src"
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
    print("\nALL DESKDRIVER TESTS PASSED!")


if __name__ == "__main__":
    run_all()
