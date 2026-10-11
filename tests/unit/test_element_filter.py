"""What the roadmap refuses to store: transient content, secrets, user input."""

import pytest

from deskdriver.navigation.element_filter import is_transient, redact_secrets, storable_value


@pytest.mark.parametrize("element, exe", [
    ({"name": "notes.txt. Modified.", "control_type": "TabItemControl"}, "notepad.exe"),
    ({"name": "Gmail - Memory usage - 280 MB", "control_type": "DataItemControl"}, "brave.exe"),
    ({"name": "reddit", "control_type": "HyperlinkControl"}, "brave.exe"),
    ({"name": "Go", "control_type": "ButtonControl", "container_path": "pane > Chrome Legacy Window > id:x"}, "code.exe"),
    ({"name": "~ ai-mouse", "control_type": "TabItemControl", "container_path": "pane > id:TabView"}, "windowsterminal.exe"),
    ({"name": "sk-ant-api03-abcDEF123. Modified", "control_type": "ButtonControl"}, ""),
    ({"name": "token ghp_abcdefghijklmnopqrstuvwxyz0123", "control_type": "ButtonControl"}, ""),
])
def test_transient(element, exe):
    assert is_transient(element, exe)


@pytest.mark.parametrize("element, exe", [
    ({"name": "Reload", "control_type": "ButtonControl"}, "brave.exe"),
    ({"name": "View", "control_type": "TabItemControl", "container_path": "id:12320"}, "explorer.exe"),
    ({"name": "Home", "control_type": "TreeItemControl"}, "explorer.exe"),
    ({"name": "Desk-top layout", "control_type": "ButtonControl"}, ""),
])
def test_kept(element, exe):
    assert not is_transient(element, exe)


def test_redact_secrets():
    assert redact_secrets("key sk-ant-api03-abc_DEF-1 here") == "key [REDACTED] here"
    assert redact_secrets("nothing to see") == "nothing to see"


def test_input_values_are_not_stored():
    assert storable_value("EditControl", "https://example.com/private") == ""
    assert storable_value("ComboBoxControl", "search terms") == ""
    assert storable_value("TreeItemControl", "Home") == "Home"
    assert storable_value("TextControl", "sk-ant-api03-zzz") == "[REDACTED]"
