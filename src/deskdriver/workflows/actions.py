"""
DeskDriver Action Pipeline Engine.
Records, serializes, parses, and executes multi-step desktop workflows
as compact, zero-token single action strings (e.g. "open:notepad | type:Hello | hotkey:ctrl+s").
"""

import os
import re
import json
import time

from deskdriver.core.mouse import move_and_click, drag_and_drop
from deskdriver.core.keyboard import press_hotkey, type_text
from deskdriver.automation.windows import focus_window, foreground_root, snap_window
from deskdriver.automation.appid import wait_for_app_window
from deskdriver.navigation.fastpaths import execute_fastpath
from deskdriver.navigation.interact import fast_click_element, fill_input, wait_for_element
from deskdriver.navigation.deepdive import deep_dive_app

from deskdriver.paths import SAVED_ACTIONS_FILE as ACTIONS_FILE

DEFAULT_ACTIONS = {
    "quick_note": "open:notepad | wait:0.4 | hotkey:ctrl+n | type:DeskDriver Action Pipeline | key:enter",
    "open_display_settings": "open:display | wait:0.5",
    "system_info": "open:about | wait:0.5",
    "open_calc": "open:calc | wait:0.5 | type:500*1.24 | key:enter",
}


# Steps that send clicks or keystrokes to whatever window is in front
INPUT_VERBS = {
    "click", "tap", "doubleclick", "dblclick", "rightclick", "rclick",
    "type", "write", "fill", "input", "hotkey", "key", "press", "drag", "draw",
}


def load_saved_actions() -> dict[str, str]:
    """Load saved named action strings from disk."""
    if ACTIONS_FILE.exists():
        try:
            with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    # Initialize with default recipes
    save_all_actions(DEFAULT_ACTIONS)
    return dict(DEFAULT_ACTIONS)


def save_all_actions(actions: dict[str, str]) -> bool:
    """Save actions map to disk."""
    try:
        with open(ACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(actions, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def save_action(name: str, action_str: str) -> dict:
    """Save or update a named action string."""
    clean_name = name.strip()
    clean_action = action_str.strip()
    if not clean_name or not clean_action:
        return {"error": "Name and action string must not be empty"}
    actions = load_saved_actions()
    actions[clean_name] = clean_action
    save_all_actions(actions)
    return {"status": "saved", "name": clean_name, "action": clean_action}


def delete_action(name: str) -> bool:
    """Delete a saved action."""
    actions = load_saved_actions()
    if name in actions:
        del actions[name]
        save_all_actions(actions)
        return True
    return False


def parse_action_string(action_str: str) -> list[dict]:
    """
    Parse an action string into executable step dictionaries.
    Supports separators: '|', ' -> ' (with spaces), ';', and newlines.
    """
    steps = []
    # Split on pipeline delimiters; a bare "->" belongs to drag coordinates (x1,y1->x2,y2)
    raw_parts = [p.strip() for p in re.split(r"\s*(?:\||\s->\s|;|\n)\s*", action_str) if p.strip()]

    for raw in raw_parts:
        if ":" not in raw:
            # Bare command like 'enter' or 'click'
            verb = raw.lower()
            arg = ""
        else:
            verb, arg = raw.split(":", 1)
            verb = verb.strip().lower()
            arg = arg.strip()

        steps.append({"verb": verb, "arg": arg, "raw": raw})

    return steps


def _step_status(res: dict) -> str:
    """Map a fast_click_element / fill_input result to a step status."""
    return "error" if "error" in res else res.get("status", "ok")


def _resolve_element_point(name: str) -> tuple[int, int] | None:
    """Screen coordinates of a named element (roadmap cache first, then a live UIA scan)."""
    el = wait_for_element(name, timeout=1.0)
    if el and "center_x" in el and "center_y" in el:
        return el["center_x"], el["center_y"]
    return None


def _launch(target: str) -> None:
    """Start an executable or App Paths alias without going through a shell."""
    exe = target if target.lower().endswith(".exe") else f"{target}.exe"
    os.startfile(exe)


def execute_action(action_str: str, interval: float = 0.05) -> dict:
    """
    Execute a multi-step action string on the desktop.
    Returns status, number of steps executed, and any errors.
    """
    t0 = time.perf_counter()
    steps = parse_action_string(action_str)
    if not steps:
        return {"error": "No valid action steps found in string"}

    results = []
    # Window the pipeline last opened / focused. Input steps only run while it is
    # still in front, so a user clicking elsewhere stops the pipeline instead of
    # having clicks and keystrokes land in the wrong window.
    target_hwnd = None
    interrupted = ""

    for idx, step in enumerate(steps):
        verb = step["verb"]
        arg = step["arg"]

        if verb in INPUT_VERBS and target_hwnd and foreground_root() != target_hwnd:
            interrupted = f"step {idx + 1} ({step['raw']}): another window came to the front"
            results.append({"step": idx + 1, "action": f"stopped before '{step['raw']}'", "status": "interrupted"})
            break

        try:
            if verb in ("open", "launch"):
                # 1. Direct fastpath
                if execute_fastpath(arg):
                    results.append({"step": idx + 1, "action": f"open fastpath '{arg}'", "status": "ok"})
                    time.sleep(0.3)
                    continue

                # 2. Window already exists?
                win = wait_for_app_window(arg, timeout=0.3)
                if win:
                    focus_window(win["hwnd"])
                    target_hwnd = win["hwnd"]
                    results.append({"step": idx + 1, "action": f"focused existing '{arg}'", "status": "ok"})
                else:
                    # Launch executable
                    try:
                        _launch(arg)
                        time.sleep(0.5)
                        w = wait_for_app_window(arg, timeout=2.5)
                        if w:
                            focus_window(w["hwnd"])
                            target_hwnd = w["hwnd"]
                        results.append({"step": idx + 1, "action": f"launched '{arg}'", "status": "ok"})
                    except Exception as err:
                        results.append({"step": idx + 1, "action": f"launch '{arg}' failed: {err}", "status": "error"})

            elif verb in ("focus", "window", "app"):
                w = wait_for_app_window(arg, timeout=2.0)
                if w:
                    focus_window(w["hwnd"])
                    target_hwnd = w["hwnd"]
                    results.append({"step": idx + 1, "action": f"focused '{arg}'", "status": "ok"})
                else:
                    results.append({"step": idx + 1, "action": f"window '{arg}' not found", "status": "warning"})

            elif verb in ("click", "tap"):
                # Coordinates or element name
                coord_match = re.match(r"^(\d+)\s*,\s*(\d+)$", arg)
                if coord_match:
                    cx, cy = int(coord_match.group(1)), int(coord_match.group(2))
                    move_and_click(cx, cy, smooth=True, duration=0.1)
                    results.append({"step": idx + 1, "action": f"clicked coordinates ({cx}, {cy})", "status": "ok"})
                else:
                    res = fast_click_element(arg)
                    results.append({"step": idx + 1, "action": f"click '{arg}'", "status": _step_status(res)})

            elif verb in ("doubleclick", "dblclick", "rightclick", "rclick"):
                is_right = verb in ("rightclick", "rclick")
                label = "right-click" if is_right else "double-click"
                coord_match = re.match(r"^(\d+)\s*,\s*(\d+)$", arg)
                point = (int(coord_match.group(1)), int(coord_match.group(2))) if coord_match else _resolve_element_point(arg)
                if point:
                    move_and_click(
                        point[0], point[1],
                        button="right" if is_right else "left",
                        clicks=1 if is_right else 2,
                        smooth=True, duration=0.1,
                    )
                    results.append({"step": idx + 1, "action": f"{label} '{arg}' at {point}", "status": "ok"})
                else:
                    results.append({"step": idx + 1, "action": f"{label} '{arg}': element not found", "status": "error"})

            elif verb in ("type", "write"):
                type_text(arg)
                results.append({"step": idx + 1, "action": f"typed '{arg}'", "status": "ok"})

            elif verb in ("fill", "input"):
                # Form: field, text or field: text
                if "," in arg:
                    field, text = arg.split(",", 1)
                elif ":" in arg:
                    field, text = arg.split(":", 1)
                else:
                    field, text = arg, ""
                res = fill_input(field.strip(), text.strip())
                results.append({"step": idx + 1, "action": f"filled '{field.strip()}' with '{text.strip()}'", "status": _step_status(res)})

            elif verb in ("hotkey", "key", "press"):
                press_hotkey(arg)
                results.append({"step": idx + 1, "action": f"pressed hotkey '{arg}'", "status": "ok"})

            elif verb in ("drag", "draw"):
                # Coordinates form: x1,y1->x2,y2 or x1,y1,x2,y2
                drag_match = re.match(r"(\d+)\s*,\s*(\d+)(?:\s*->\s*|\s*,\s*)(\d+)\s*,\s*(\d+)", arg)
                if drag_match:
                    x1, y1, x2, y2 = [int(g) for g in drag_match.groups()]
                    drag_and_drop(x1, y1, x2, y2, smooth=True, duration=0.15)
                    results.append({"step": idx + 1, "action": f"dragged ({x1},{y1}) -> ({x2},{y2})", "status": "ok"})
                else:
                    results.append({"step": idx + 1, "action": f"invalid drag format '{arg}'", "status": "error"})

            elif verb in ("wait", "sleep"):
                try:
                    sec = float(arg)
                    time.sleep(sec)
                    results.append({"step": idx + 1, "action": f"waited {sec}s", "status": "ok"})
                except ValueError:
                    time.sleep(0.3)
                    results.append({"step": idx + 1, "action": f"invalid wait '{arg}', waited 0.3s", "status": "warning"})

            elif verb in ("snap",):
                ok = snap_window("", side=arg or "left")  # "" = foreground window
                results.append({"step": idx + 1, "action": f"snapped window to {arg}", "status": "ok" if ok else "error"})

            elif verb in ("scan", "learn", "deepdive"):
                scan_res = deep_dive_app(window_search=arg)
                if "error" in scan_res:
                    results.append({"step": idx + 1, "action": f"scan '{arg}' failed: {scan_res['error']}", "status": "error"})
                else:
                    cnt = scan_res.get("total_elements", 0)
                    app_n = scan_res.get("app", arg or "app")
                    results.append({"step": idx + 1, "action": f"scanned {app_n} ({cnt} controls indexed into roadmap)", "status": "ok"})

            else:
                results.append({"step": idx + 1, "action": f"unknown verb '{verb}'", "status": "skipped"})

            if interval > 0:
                time.sleep(interval)

        except Exception as step_err:
            results.append({"step": idx + 1, "action": f"failed '{step['raw']}': {step_err}", "status": "error"})

    duration = round(time.perf_counter() - t0, 2)
    result = {
        "status": "interrupted" if interrupted else "completed",
        "action_string": action_str,
        "steps_count": len(steps),
        "steps_executed": len(results),
        "duration_seconds": duration,
        "steps": results,
    }
    if interrupted:
        result["reason"] = f"Stopped at {interrupted}. The user may have taken over; ask before continuing."
    return result
