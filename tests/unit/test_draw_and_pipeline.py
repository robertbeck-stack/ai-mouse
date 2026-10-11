"""Drawing input validation and the stop-when-the-user-takes-over rules."""

import importlib

import pytest

draw = importlib.import_module("deskdriver.automation.draw")
actions = importlib.import_module("deskdriver.workflows.actions")


def test_interpolation_reaches_the_end_point_in_small_steps():
    pts = list(draw._interpolate((0, 0), (30, 0)))
    assert pts[-1] == (30, 0)
    assert all(b[0] - a[0] <= draw.STEP_PX for a, b in zip([(0, 0)] + pts, pts))


def test_normalize_accepts_polylines_and_rejects_bad_points():
    assert draw._normalize([[[1.4, 2.6], [3, 4]], []]) == [[(1, 3), (3, 4)]]
    with pytest.raises(ValueError):
        draw._normalize([[[1, 2, 3]]])


def test_draw_refuses_bad_input_without_touching_the_mouse():
    assert "error" in draw.draw_strokes("mspaint", [[[1, 2, 3]]])
    assert "not found" in draw.draw_strokes("no-such-app-xyz", [[[1, 1], [2, 2]]])["error"]


def test_pipeline_stops_when_another_window_comes_to_front(monkeypatch):
    sent = []
    monkeypatch.setattr(actions, "wait_for_app_window", lambda name, timeout=0: {"hwnd": 111, "title": name})
    monkeypatch.setattr(actions, "focus_window", lambda hwnd: True)
    monkeypatch.setattr(actions, "execute_fastpath", lambda target: False)
    monkeypatch.setattr(actions, "type_text", lambda text: sent.append(text))
    monkeypatch.setattr(actions, "foreground_root", lambda: 222)  # the user clicked another window

    res = actions.execute_action("focus:notepad | type:hello | type:world", interval=0)
    assert res["status"] == "interrupted"
    assert sent == []
    assert res["steps"][-1]["status"] == "interrupted"


def test_pipeline_runs_while_target_stays_in_front(monkeypatch):
    sent = []
    monkeypatch.setattr(actions, "wait_for_app_window", lambda name, timeout=0: {"hwnd": 111, "title": name})
    monkeypatch.setattr(actions, "focus_window", lambda hwnd: True)
    monkeypatch.setattr(actions, "type_text", lambda text: sent.append(text))
    monkeypatch.setattr(actions, "foreground_root", lambda: 111)

    res = actions.execute_action("focus:notepad | type:hello | type:world", interval=0)
    assert res["status"] == "completed" and sent == ["hello", "world"]
