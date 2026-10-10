"""
Interactive Demo for AI Mouse & Desktop Control.
Run: .\\.venv\\Scripts\\python demo.py
"""

import sys
import time
from pathlib import Path

# Add src to python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import ai_mouse as am


def print_banner():
    print("=" * 60)
    print("       AI MOUSE & UI AUTOMATION CONTROLLER (DEMO)")
    print("=" * 60)


def test_inspect_cursor():
    x, y = am.get_mouse_position()
    print(f"\n[+] Músarhnit: ({x}, {y})")
    print("[+] Skoða hvað er undir músinni...")
    info = am.get_element_under_cursor()
    print(f"    Heiti:         {info.get('name')!r}")
    print(f"    Tegund (Type): {info.get('control_type')}")
    print(f"    Gluggi:        {info.get('window_title')!r}")
    rect = info.get("bounding_rect", {})
    print(f"    Stærð:         {rect.get('width')}x{rect.get('height')} px")


def test_list_windows():
    print("\n[+] Sæki alla sýnilega glugga á skjánum:")
    wins = am.list_windows()
    for i, w in enumerate(wins, 1):
        print(f"  {i}. [{w['hwnd']}] {w['title']}")


def test_list_buttons():
    print("\n[+] Sæki smellanlega hnappa í virka glugganum:")
    buttons = am.list_clickable_elements(max_elements=15)
    if not buttons:
        print("  Engir hnappar fundust í núverandi forritsglugga.")
    for b in buttons:
        print(f"  - [{b['control_type']}] {b['name']!r} -> Miðja: ({b['center_x']}, {b['center_y']})")


def test_smooth_movement():
    start_x, start_y = am.get_mouse_position()
    print(f"\n[+] Núverandi staðsetning: ({start_x}, {start_y})")
    target_x, target_y = start_x + 60, start_y + 60
    print(f"[+] Hreyfi músina mjúklega á ({target_x}, {target_y}) með Bézier-kúrfu...")
    am.move_mouse(target_x, target_y, smooth=True, duration=0.25)
    time.sleep(0.15)
    print(f"[+] Færi hana aftur á ({start_x}, {start_y})...")
    am.move_mouse(start_x, start_y, smooth=True, duration=0.2)
    print("[+] Hreyfingu lokið!")


def main():
    print_banner()
    test_inspect_cursor()
    test_list_windows()
    test_list_buttons()
    test_smooth_movement()
    print("\n" + "=" * 60)
    print("Allar prófanir tókust! Modular ai-mouse er tilbúið.")
    print("=" * 60)


if __name__ == "__main__":
    main()
