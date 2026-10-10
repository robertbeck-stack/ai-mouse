"""
Self-check test suite for modular ai_mouse.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import ai_mouse as am


def test_core_mouse():
    print("Testing core mouse...")
    pos = am.get_mouse_position()
    assert isinstance(pos, tuple) and len(pos) == 2
    assert pos[0] >= 0 and pos[1] >= 0
    print(f" -> Cursor position: {pos}")


def test_window_enumeration():
    print("Testing window enumeration...")
    wins = am.list_windows()
    assert isinstance(wins, list)
    print(f" -> Found {len(wins)} active windows")


def test_element_inspection():
    print("Testing element inspection...")
    el = am.get_element_under_cursor()
    assert isinstance(el, dict)
    print(f" -> Under cursor: {el.get('name')!r} ({el.get('control_type')})")


def test_roadmap_lookup():
    print("Testing roadmap cache...")
    stats = am.roadmap.map
    assert isinstance(stats, dict)
    print(f" -> Cached apps in roadmap: {len(stats)}")


def test_keyboard_support():
    print("Testing keyboard hotkey definitions...")
    from ai_mouse.core.keyboard import _get_vk_code, COMMON_HOTKEYS
    assert _get_vk_code("ctrl") == 0x11
    assert _get_vk_code("enter") == 0x0D
    assert "save" in COMMON_HOTKEYS
    assert COMMON_HOTKEYS["save"] == "ctrl+s"
    print(f" -> Universal hotkeys registered: {len(COMMON_HOTKEYS)}")


def test_hotkeys_extraction():
    print("Testing hotkey extraction...")
    from ai_mouse.navigation.hotkeys import extract_shortcut_from_name, get_app_hotkeys
    name, sc = extract_shortcut_from_name("Feitletrað (Ctrl+B)")
    assert name == "Feitletrað" and sc == "Ctrl+B"
    name, sc = extract_shortcut_from_name("Save File (Ctrl+Shift+S)")
    assert name == "Save File" and sc == "Ctrl+Shift+S"
    notepad_keys = get_app_hotkeys("Notepad")
    assert len(notepad_keys) > 10
    print(f" -> Notepad hotkeys recognized: {len(notepad_keys)}")


def test_mouse_features():
    print("Testing scroll and drag functions...")
    assert callable(am.mouse_scroll)
    assert callable(am.drag_and_drop)
    # Perform a subtle zero-distance or safe scroll
    am.mouse_scroll(0)
    print(" -> Mouse scroll & drag callable verified")


def test_dpi_awareness():
    print("Testing DPI awareness...")
    from ai_mouse.core.desktop import enable_dpi_awareness
    enable_dpi_awareness()
    print(" -> DPI awareness enabled")


def test_responsive_anchors_and_fill():
    print("Testing responsive anchors and fill_input...")
    assert callable(am.fill_input)

    # Test anchor calculation in memory
    rect1 = {"left": 100, "top": 100, "right": 1100, "bottom": 800}
    test_elements = [
        {"name": "CloseBtn", "control_type": "Button", "center_x": 1050, "center_y": 120, "rect": {"width": 30, "height": 30}},
        {"name": "SaveBtn", "control_type": "Button", "center_x": 150, "center_y": 120, "rect": {"width": 30, "height": 30}},
    ]
    am.roadmap.learn_window("TestAppAnchor", test_elements, rect1)

    # Now simulate resized window: width expanded from 1000 to 1400
    rect2 = {"left": 100, "top": 100, "right": 1500, "bottom": 800}
    cached_close = am.roadmap.find_cached_element("TestAppAnchor", "CloseBtn", rect2)
    assert cached_close is not None
    # CloseBtn was 50px from right in rect1 (1100 - 1050). In rect2 (right=1500), it should be 1500 - 50 = 1450!
    assert cached_close["center_x"] == 1450
    print(f" -> Responsive right-anchor dynamically recalculated: {cached_close['center_x']}")


def run_all():
    test_core_mouse()
    test_window_enumeration()
    test_element_inspection()
    test_roadmap_lookup()
    test_keyboard_support()
    test_hotkeys_extraction()
    test_mouse_features()
    test_dpi_awareness()
    test_responsive_anchors_and_fill()
    print("\nALL MODULAR TESTS PASSED!")


if __name__ == "__main__":
    run_all()
