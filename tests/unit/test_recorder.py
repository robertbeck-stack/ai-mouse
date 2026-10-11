"""Turning raw clicks into pipeline steps."""

import importlib

recorder = importlib.import_module("deskdriver.workflows.recorder")
actions = importlib.import_module("deskdriver.workflows.actions")


def click(button="left", x=10, y=10, t=0.0, name="OK"):
    c = {"button": button, "x": x, "y": y, "time": t}
    return {**c, "type": "mouse_click", "action": recorder.click_action(button, name, x, y)}


def test_click_actions():
    assert recorder.click_action("left", "Save", 1, 2) == "click:Save"
    assert recorder.click_action("right", "", 5, 6) == "rightclick:5,6"
    assert recorder.click_action("left", "(no text)", 5, 6) == "click:5,6"


def test_quick_second_click_becomes_double_click():
    acts = [click(t=1.0, name="report.txt")]
    assert recorder.merge_double_click(acts, {"button": "left", "x": 11, "y": 9, "time": 1.2}, 0.5)
    assert acts[0]["action"] == "doubleclick:report.txt"


def test_slow_far_or_right_clicks_stay_separate():
    acts = [click(t=1.0)]
    assert not recorder.merge_double_click(acts, {"button": "left", "x": 10, "y": 10, "time": 2.0}, 0.5)
    assert not recorder.merge_double_click(acts, {"button": "left", "x": 40, "y": 10, "time": 1.1}, 0.5)
    assert not recorder.merge_double_click(acts, {"button": "right", "x": 10, "y": 10, "time": 1.1}, 0.5)


def test_repeated_clicks_are_kept_but_repeated_focus_collapses():
    acts = [{"action": "focus:calc.exe"}, {"action": "focus:calc.exe"},
            {"action": "click:+"}, {"action": "click:+"}]
    assert recorder.pipeline_steps(acts) == ["focus:calc.exe", "click:+", "click:+"]


def test_dashboard_is_not_recorded():
    assert recorder.is_ignored_title("DeskDriver Wiki - The Free Desktop Automation Encyclopedia")
    assert not recorder.is_ignored_title("Antigravity")


def test_click_after_right_click_uses_the_open_menu(monkeypatch):
    clicked, named = [], []
    monkeypatch.setattr(actions, "move_and_click", lambda x, y, **kw: clicked.append((x, y, kw.get("button", "left"))))
    monkeypatch.setattr(actions, "find_open_menu_item", lambda name: (300, 400) if name == "Copy" else None)
    monkeypatch.setattr(actions, "fast_click_element", lambda name: named.append(name) or {"status": "ok"})
    monkeypatch.setattr(actions.time, "sleep", lambda s: None)

    res = actions.execute_action("rightclick:100,200 | click:Copy | click:Paste", interval=0)
    assert res["status"] == "completed"
    assert clicked == [(100, 200, "right"), (300, 400, "left")]
    assert named == ["Paste"]  # the menu closed after "Copy"; later clicks resolve normally
