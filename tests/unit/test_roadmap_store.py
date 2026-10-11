"""Per-app roadmap storage: learning rules, aging, cross-process merges, migration."""

import importlib

import pytest

# The module, not the `roadmap` instance that deskdriver.navigation re-exports
rm = importlib.import_module("deskdriver.navigation.roadmap")
migrate_entries = importlib.import_module("deskdriver.navigation.roadmap_migrate").migrate_entries

RECT = {"left": 100, "top": 50, "right": 900, "bottom": 650}


def el(name, x=150, y=80, **extra):
    return {"name": name, "center_x": x, "center_y": y, "rect": {"width": 10, "height": 10}, **extra}


@pytest.fixture
def store(tmp_path):
    return rm.UIRoadmap(directory=tmp_path / "ui_roadmap", legacy_file=None)


def reopen(store):
    return rm.UIRoadmap(directory=store.directory, legacy_file=None)


def test_positions_are_window_relative(store):
    store.learn_window("App", [el("Save", 150, 80)], RECT)
    saved = reopen(store).map["App"]["elements"]["save"]
    assert (saved["rel_x"], saved["rel_y"]) == (50, 30)


@pytest.mark.parametrize("rect", [
    {"left": 0, "top": 0, "right": 0, "bottom": 0},                          # zero-size (Qt via UIA)
    {"left": -32000, "top": -32000, "right": -31840, "bottom": -31972},      # minimized
])
def test_invalid_window_rects_learn_nothing(store, rect):
    store.learn_window("App", [el("Save")], rect)
    assert "App" not in store.map


def test_names_are_normalized_and_input_values_dropped(store):
    store.learn_window("App", [
        el("Media Alt+M"),
        el("unnamed_buttoncontrol_900_900", 160, 90),
        el("Address", control_type="EditControl", value="https://private.example"),
        el("notes.txt. Modified.", control_type="TabItemControl"),
    ], RECT)
    elements = store.map["App"]["elements"]
    assert elements["media"]["shortcut"] == "Alt+M"
    assert elements["media"]["ai_action"] == "hotkey:alt+m"
    assert "button @ 60,40" in elements
    assert elements["address"]["value"] == ""
    assert not any("notes.txt" in k for k in elements)


def test_complete_scans_drop_elements_missing_three_times(store):
    store.learn_window("App", [el("Old", container_path="toolbar"), el("Kept", container_path="toolbar")], RECT, complete=True)
    for i in range(rm.STALE_AFTER_MISSES - 1):
        store.learn_window("App", [el("Kept", container_path="toolbar")], RECT, complete=True)
        assert "old" in store.map["App"]["elements"]
    store.learn_window("App", [el("Kept", container_path="toolbar")], RECT, complete=True)
    assert "old" not in reopen(store).map["App"]["elements"]


def test_controls_of_a_part_not_on_screen_are_not_aged(store):
    # Settings: deep dives of the System page must not erase what was learned on Bluetooth
    store.learn_window("App", [el("Pair device", container_path="page:bluetooth")], RECT, complete=True)
    for _ in range(rm.STALE_AFTER_MISSES + 2):
        store.learn_window("App", [el("Display", container_path="page:system")], RECT, complete=True)
    assert store.map["App"]["elements"]["pair device"]["misses"] == 0


def test_partial_scans_never_drop_elements(store):
    store.learn_window("App", [el("Old")], RECT, complete=True)
    for _ in range(5):
        store.learn_window("App", [el("Other")], RECT)
    assert "old" in store.map["App"]["elements"]


def test_seeing_an_element_again_resets_its_misses(store):
    store.learn_window("App", [el("Flaky", container_path="bar")], RECT, complete=True)
    store.learn_window("App", [el("X", container_path="bar")], RECT, complete=True)
    assert store.map["App"]["elements"]["flaky"]["misses"] == 1
    store.learn_window("App", [el("Flaky", container_path="bar"), el("X", container_path="bar")], RECT, complete=True)
    assert store.map["App"]["elements"]["flaky"]["misses"] == 0


def test_normalize_names_rekeys_existing_entries(store):
    store.map["App"] = {"schema": 2, "elements": {
        "view alt+i": {"name": "View Alt+i", "rel_x": 1, "rel_y": 1, "ai_action": "click:View Alt+i"},
    }}
    assert store.normalize_names() == {"App": 1}
    assert store.map["App"]["elements"]["view"]["ai_action"] == "hotkey:alt+i"


def test_prune_transient_and_scrub_values(store):
    store.map["App"] = {"schema": 2, "exe": "notepad.exe", "elements": {
        "old tab. unmodified.": {"name": "old tab. Unmodified.", "control_type": "TabItemControl"},
        "search": {"name": "Search", "control_type": "EditControl", "value": "secret query"},
    }}
    assert store.prune_transient() == {"App": 1}
    saved = reopen(store).map["App"]["elements"]
    assert "old tab. unmodified." not in saved and saved["search"]["value"] == ""


def test_two_processes_merge_instead_of_clobbering(store):
    a, b = store, reopen(store)
    a.learn_window("App", [el("From A")], RECT)
    b.learn_window("App", [el("From B")], RECT)
    a.refresh_app("App")
    assert {"from a", "from b"} <= set(a.map["App"]["elements"])
    assert a.remove_element("App", "from a")
    b.learn_window("App", [el("From B 2")], RECT)  # stale b still holds "from a"
    final = reopen(store).map["App"]["elements"]
    assert "from a" not in final and {"from b", "from b 2"} <= set(final)


def test_resolve_app_key_prefers_main_window(store):
    store.map["explorer.exe#shell_traywnd"] = {"elements": {}, "exe": "explorer.exe", "display_name": "Taskbar"}
    store.map["explorer.exe"] = {"elements": {}, "exe": "explorer.exe", "display_name": "File Explorer"}
    assert store.resolve_app_key("explorer") == "explorer.exe"
    assert store.resolve_app_key("Taskbar") == "explorer.exe#shell_traywnd"


def test_schema1_migration():
    old = {
        "notepad": {"elements": {"save": {"name": "Save"}}, "last_updated": 1},
        "*notes - Notepad": {"elements": {"open": {"name": "Open"}}, "last_updated": 2,
                             "process_info": {"exe_name": "Notepad.exe", "class_name": "Notepad"}},
        "Page setup": {"elements": {"ok": {"name": "OK"}}, "last_updated": 3,
                       "process_info": {"exe_name": "Notepad.exe", "class_name": "#32770"}},
        "Bank_Statement.pdf - Viewer": {"elements": {"x": {}}, "last_updated": 1},
    }
    migrated, unmigrated = migrate_entries(old)
    assert set(migrated) == {"notepad.exe", "notepad.exe/page setup"}
    assert set(migrated["notepad.exe"]["elements"]) == {"save", "open"}
    assert list(unmigrated) == ["Bank_Statement.pdf - Viewer"]
    assert "*notes - Notepad" not in str(migrated)


def test_match_element_key_has_no_reverse_substring_hits():
    els = {"ok": 1, "bookmark this tab": 1, "save": 1, "save as": 1}
    assert rm.match_element_key(els, "bookmark") == "bookmark this tab"
    assert rm.match_element_key(els, "save") == "save"
    assert rm.match_element_key({"ok": 1}, "bookmark") is None


def test_dropdown_items_remember_their_menu(store):
    store.learn_window("App", [el("Save as", menu_parent="File", shortcut="")], RECT)
    hit = store.find_cached_element("App", "Save as", RECT)
    assert hit["menu_parent"] == "File"
