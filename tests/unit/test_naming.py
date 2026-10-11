"""App keys, dialog surfaces, element names and shortcuts."""

import pytest

from deskdriver.automation.appid import AppIdentity, app_matches, display_name_for, key_for, surface_name
from deskdriver.core.shortcuts import extract_shortcut_from_name
from deskdriver.navigation.element_filter import normalize_name, prefer_shortcut


@pytest.mark.parametrize("exe, cls, key", [
    ("Notepad.exe", "Notepad", "notepad.exe"),
    ("explorer.exe", "CabinetWClass", "explorer.exe"),
    ("explorer.exe", "Shell_TrayWnd", "explorer.exe#shell_traywnd"),
    ("", "SomeClass", "#someclass"),
    ("", "", "unknown"),
])
def test_key_for(exe, cls, key):
    assert key_for(exe, cls) == key


def test_display_names():
    assert display_name_for("mspaint.exe") == "Paint"
    assert display_name_for("explorer.exe#shell_traywnd") == "Taskbar"
    assert display_name_for("notepad.exe/page setup") == "Notepad"


@pytest.mark.parametrize("title, surface", [
    ("Page setup", "page setup"),
    ("notes.txt Properties", "properties"),
    ("backup.2024.zip Properties", "properties"),
    ('Delete "report"', "delete"),
    ("Copying 3 items", "copying items"),
    ("", "dialog"),
])
def test_surface_name(title, surface):
    assert surface_name(title) == surface


def test_bare_exe_name_means_the_main_window():
    tray = AppIdentity("explorer.exe#shell_traywnd", "explorer.exe", "Taskbar", "shell_traywnd")
    files = AppIdentity("explorer.exe", "explorer.exe", "File Explorer", "cabinetwclass")
    dialog = AppIdentity("notepad.exe/page setup", "notepad.exe", "Notepad", "#32770", "page setup")
    assert not app_matches(tray, "explorer") and app_matches(tray, "taskbar")
    assert app_matches(files, "explorer") and app_matches(files, "File Explorer")
    assert app_matches(dialog, "notepad")


@pytest.mark.parametrize("name, expected", [
    ("Bold (Ctrl+B)", ("Bold", "Ctrl+B")),
    ("Collapse tabs (Ctrl+Shift+L)", ("Collapse tabs", "Ctrl+Shift+L")),
    ("Refresh (F5)", ("Refresh", "F5")),
    ("Media Alt+M", ("Media", "Alt+M")),
    ("Playback Alt+l", ("Playback", "Alt+L")),
    ("Save", ("Save", "")),
])
def test_extract_shortcut(name, expected):
    assert extract_shortcut_from_name(name) == expected


def test_normalize_name_uses_window_relative_position_for_unnamed_controls():
    assert normalize_name("unnamed_buttoncontrol_477_1204", 62, 985) == ("button @ 62,985", "")
    assert normalize_name("unnamed_splitbuttoncontrol_902_732", 487, 513) == ("splitbutton @ 487,513", "")
    assert normalize_name("Media Alt+M", 0, 0) == ("Media", "Alt+M")


def test_canvas_detection():
    from deskdriver.navigation.deepdive import detect_canvas_game_surface as detect
    assert detect("UnityWndClass", 50, 1200, 800)["is_canvas_game"]          # known engine
    assert detect("MyEngineWnd", 1, 1200, 800)["is_canvas_game"]             # unknown class, no UIA tree
    assert not detect("MyEngineWnd", 1, 1200, 800, xaml_host=True)["is_canvas_game"]  # WinUI island not loaded
    assert not detect("MSPaintApp", 1, 1200, 800)["is_canvas_game"]
    assert not detect("ApplicationFrameWindow", 2, 1200, 800)["is_canvas_game"]
    assert not detect("MyEngineWnd", 5, 1200, 800, truncated=True)["is_canvas_game"]


def test_prefer_shortcut():
    assert prefer_shortcut("Ctrl+B", "Alt, B") == "Ctrl+B"   # access key loses to accelerator
    assert prefer_shortcut("Ctrl+B", "") == "Ctrl+B"
    assert prefer_shortcut("", "Ctrl+S") == "Ctrl+S"
    assert prefer_shortcut("Ctrl+B", "Ctrl+Shift+B") == "Ctrl+Shift+B"  # UIA's real accelerator wins
