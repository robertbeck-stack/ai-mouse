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


def run_all():
    test_core_mouse()
    test_window_enumeration()
    test_element_inspection()
    test_roadmap_lookup()
    test_keyboard_support()
    test_hotkeys_extraction()
    print("\nALL MODULAR TESTS PASSED!")


if __name__ == "__main__":
    run_all()
