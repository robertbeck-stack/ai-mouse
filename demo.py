"""
Interactive Demo for DeskDriver Desktop Automation.
Run: .\\.venv\\Scripts\\python demo.py
"""

import sys
import time
from pathlib import Path

# Add src to python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import deskdriver as dd


def print_banner():
    print("=" * 60)
    print("       DESKDRIVER - NATIVE DESKTOP AUTOMATION (DEMO)")
    print("=" * 60)


def test_inspect_cursor():
    x, y = dd.get_mouse_position()
    print(f"\n[+] Cursor coordinates: ({x}, {y})")
    print("[+] Inspecting element under cursor...")
    info = dd.get_element_under_cursor()
    print(f"    Name:         {info.get('name')!r}")
    print(f"    Type:         {info.get('control_type')}")
    print(f"    Window:       {info.get('window_title')!r}")
    rect = info.get("bounding_rect", {})
    print(f"    Dimensions:   {rect.get('width')}x{rect.get('height')} px")


def test_list_windows():
    print("\n[+] Enumerating all visible desktop windows:")
    wins = dd.list_windows()
    for i, w in enumerate(wins[:10], 1):
        print(f"  {i}. [{w['hwnd']}] {w['title']}")


def test_list_buttons():
    print("\n[+] Inspecting interactive controls in active window:")
    buttons = dd.list_clickable_elements(max_elements=15)
    if not buttons:
        print("  No clickable controls detected in active foreground window.")
    for b in buttons:
        print(f"  - [{b['control_type']}] {b['name']!r} -> Center: ({b['center_x']}, {b['center_y']})")


def test_smooth_movement():
    start_x, start_y = dd.get_mouse_position()
    print(f"\n[+] Current cursor position: ({start_x}, {start_y})")
    target_x, target_y = start_x + 50, start_y + 50
    print(f"[+] Moving cursor with human Bézier curve to ({target_x}, {target_y})...")
    dd.move_mouse(target_x, target_y, smooth=True, duration=0.25)
    time.sleep(0.15)
    print(f"[+] Restoring back to ({start_x}, {start_y})...")
    dd.move_mouse(start_x, start_y, smooth=True, duration=0.2)
    print("[+] Cursor motion complete!")


def main():
    print_banner()
    test_inspect_cursor()
    test_list_windows()
    test_list_buttons()
    test_smooth_movement()
    print("\n" + "=" * 60)
    print("All demonstrations succeeded! DeskDriver is operational.")
    print("=" * 60)


if __name__ == "__main__":
    main()
