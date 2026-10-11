"""Shortcut strings become the right key events."""

import importlib

keyboard = importlib.import_module("deskdriver.core.keyboard")


class FakeUser32:
    def __init__(self):
        self.events = []  # (vk, is_up)

    def SendInput(self, n, inputs, size):
        ki = inputs._obj[0].ki if hasattr(inputs, "_obj") else inputs[0].ki
        self.events.append((ki.wVk, bool(ki.dwFlags & keyboard.KEYEVENTF_KEYUP)))
        return 1


def pressed(monkeypatch, hotkey):
    fake = FakeUser32()
    monkeypatch.setattr(keyboard, "user32", fake)
    monkeypatch.setattr(keyboard, "ensure_desktop", lambda: None)
    monkeypatch.setattr(keyboard.time, "sleep", lambda s: None)
    keyboard.press_hotkey(hotkey)
    return fake.events


def test_chord_presses_together(monkeypatch):
    assert pressed(monkeypatch, "ctrl+s") == [(0x11, False), (0x53, False), (0x53, True), (0x11, True)]


def test_access_key_sequence_taps_each_key(monkeypatch):
    # "Alt, F" = tap Alt, then tap F (not Alt+F, and never F alone)
    assert pressed(monkeypatch, "Alt, F") == [(0x12, False), (0x12, True), (0x46, False), (0x46, True)]


def test_unknown_key_sends_nothing(monkeypatch):
    assert pressed(monkeypatch, "ctrl+ä") == []
