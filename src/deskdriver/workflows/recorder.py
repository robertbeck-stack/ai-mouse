"""
DeskDriver Live Session Recorder & Observer Engine.
Monitors user desktop interactions in real time: tracks foreground window transitions,
mouse clicks on UI controls, and automatically indexes all visited applications in the background.
Produces serialized Action Pipeline strings ready for immediate zero-token replay.
"""

import ctypes
from ctypes import wintypes
import queue
import threading
import time
from typing import Any

from deskdriver.core.desktop import ensure_desktop
from deskdriver.automation.windows import user32, window_at
from deskdriver.automation.uia import get_element_at
from deskdriver.navigation.roadmap import roadmap
from deskdriver.automation.appid import identify_window
from deskdriver.navigation.history import record_scan_log
from deskdriver.navigation.deepdive import deep_dive_app

SCAN_MAX_ELEMENTS = 250

VK_LBUTTON, VK_RBUTTON = 0x01, 0x02
CLICK_VERBS = {"left": "click", "right": "rightclick"}
DOUBLE_CLICK_DISTANCE = 4  # px, like SM_CXDOUBLECLK
# Windows the recorder must not record: the dashboard that controls it
IGNORED_TITLES = ("deskdriver wiki",)


def is_ignored_title(title: str) -> bool:
    low = (title or "").lower()
    return any(t in low for t in IGNORED_TITLES)


def click_action(button: str, name: str, x: int, y: int) -> str:
    """Pipeline step for a click: by element name when known, else by screen position."""
    target = name if name and name != "(no text)" else f"{x},{y}"
    return f"{CLICK_VERBS[button]}:{target}"


def merge_double_click(actions: list[dict], click: dict, double_click_time: float) -> bool:
    """
    Turn the previous left click into a double click if `click` repeats it within the
    system double-click time and distance. Returns True when merged.
    """
    if click["button"] != "left" or not actions:
        return False
    prev = actions[-1]
    if (prev.get("type") == "mouse_click" and prev.get("button") == "left"
            and click["time"] - prev["time"] <= double_click_time
            and abs(click["x"] - prev["x"]) <= DOUBLE_CLICK_DISTANCE
            and abs(click["y"] - prev["y"]) <= DOUBLE_CLICK_DISTANCE):
        prev["type"] = "mouse_double_click"
        prev["action"] = prev["action"].replace("click:", "doubleclick:", 1)
        return True
    return False


def pipeline_steps(actions: list[dict]) -> list[str]:
    """
    Recorded actions as pipeline steps. Only repeated focus steps collapse
    (re-focusing the same window adds nothing); repeated clicks are real input
    (pressing "+" twice) and stay.
    """
    steps = []
    for item in actions:
        act = item.get("action", "").strip()
        if not act:
            continue
        if steps and act == steps[-1] and act.startswith("focus:"):
            continue
        steps.append(act)
    return steps


class SessionRecorder:
    def __init__(self):
        self._is_recording = False
        self._thread: threading.Thread | None = None
        self._scan_thread: threading.Thread | None = None
        # Newly visited windows to index. Scans take seconds, so they run on their own
        # thread; scanning inline in the monitor loop missed every click meanwhile.
        self._scan_queue: queue.Queue = queue.Queue()
        self._start_time = 0.0
        self._stop_time = 0.0
        self._actions: list[dict[str, Any]] = []
        self._visited_apps: list[str] = []
        self._new_controls_count = 0
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    def start(self) -> dict[str, Any]:
        """Start monitoring user actions in the background."""
        with self._lock:
            if self._is_recording:
                return {
                    "status": "already_recording",
                    "elapsed": round(time.time() - self._start_time, 1),
                    "actions_count": len(self._actions),
                }

            self._is_recording = True
            self._start_time = time.time()
            self._stop_time = 0.0
            self._actions = []
            self._visited_apps = []
            self._new_controls_count = 0

            self._scan_queue = queue.Queue()
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="DeskDriverSessionRecorder")
            self._scan_thread = threading.Thread(
                target=self._scan_loop, args=(self._scan_queue,), daemon=True, name="DeskDriverRecorderScanner"
            )
            self._thread.start()
            self._scan_thread.start()

            return {
                "status": "recording_started",
                "timestamp": self._start_time,
                "message": "Live session recording started. DeskDriver is monitoring windows and clicks in background.",
            }

    def get_status(self) -> dict[str, Any]:
        """Check live recorder status and current action count."""
        with self._lock:
            if not self._is_recording:
                return {"recording": False, "elapsed": 0.0, "actions_count": 0, "apps": []}

            elapsed = round(time.time() - self._start_time, 1)
            return {
                "recording": True,
                "elapsed": elapsed,
                "actions_count": len(self._actions),
                "apps": list(self._visited_apps),
                "latest_action": self._actions[-1]["action"] if self._actions else None,
            }

    def stop(self) -> dict[str, Any]:
        """Stop monitoring, compile recorded action pipeline, and return session audit."""
        with self._lock:
            if not self._is_recording:
                return {"status": "not_recording", "actions": [], "pipeline": ""}

            self._is_recording = False
            self._stop_time = time.time()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        # Queued scans run before the stop sentinel; wait a bounded time so their new controls are counted.
        self._scan_queue.put(None)
        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=5.0)

        elapsed = round(self._stop_time - self._start_time, 2)

        clean_steps = pipeline_steps(self._actions)

        pipeline_str = " | ".join(clean_steps)

        # Persist updated roadmap
        try:
            roadmap.save()
        except Exception:
            pass

        # Unified log entry
        apps_summary = ", ".join(self._visited_apps[:3]) if self._visited_apps else "Desktop"
        if len(self._visited_apps) > 3:
            apps_summary += f" (+{len(self._visited_apps) - 3} more)"

        record_scan_log(
            action="Session Record",
            app=apps_summary,
            summary=f"Recorded {len(clean_steps)} actions across {len(self._visited_apps)} apps ({self._new_controls_count} new controls indexed)",
            count=len(clean_steps),
            new_count=self._new_controls_count,
            items=clean_steps[:30],
            duration=elapsed,
            status="success",
        )

        return {
            "status": "recording_stopped",
            "duration_seconds": elapsed,
            "actions_count": len(clean_steps),
            "apps_visited": self._visited_apps,
            "visited_apps": self._visited_apps,
            "pipeline": pipeline_str,
            "actions": self._actions,
            "new_controls_count": self._new_controls_count,
            "discovered_controls": self._new_controls_count,
        }

    def _monitor_loop(self):
        """Worker thread polling foreground window changes and mouse clicks."""
        ensure_desktop()
        last_hwnd = 0
        pressed = {"left": False, "right": False}
        double_click_time = user32.GetDoubleClickTime() / 1000.0
        # GetAsyncKeyState reports physical buttons; with swapped buttons (left-handed
        # setting) the primary "left" click is the physical right button
        swapped = bool(user32.GetSystemMetrics(23))  # SM_SWAPBUTTON
        buttons = (("left", VK_RBUTTON), ("right", VK_LBUTTON)) if swapped else (("left", VK_LBUTTON), ("right", VK_RBUTTON))

        buf = ctypes.create_unicode_buffer(512)

        while True:
            with self._lock:
                if not self._is_recording:
                    break

            try:
                # 1. Detect Window / Focus Changes
                curr_hwnd = user32.GetForegroundWindow()
                if curr_hwnd and curr_hwnd != last_hwnd:
                    user32.GetWindowTextW(curr_hwnd, buf, 512)
                    title = buf.value.strip()

                    # Don't record the dashboard that is running the recorder
                    if title and not is_ignored_title(title):
                        identity = identify_window(int(curr_hwnd))
                        app_key = identity.key
                        with self._lock:
                            first_visit = app_key not in self._visited_apps
                            if first_visit:
                                self._visited_apps.append(app_key)
                        if first_visit:
                            self._scan_queue.put(int(curr_hwnd))

                        elapsed = round(time.time() - self._start_time, 2)
                        with self._lock:
                            self._actions.append({
                                "action": f"focus:{app_key}",
                                "type": "window_focus",
                                "app": app_key,
                                "display_name": identity.display_name,
                                "time": elapsed,
                            })

                        last_hwnd = curr_hwnd

                # 2. Detect left / right clicks (on press, so a held drag counts once)
                for button, vk in buttons:
                    down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                    if down and not pressed[button]:
                        self._record_click(button, double_click_time)
                    pressed[button] = down

            except Exception:
                pass

            time.sleep(0.04)


    def _record_click(self, button: str, double_click_time: float):
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        win = window_at(pt.x, pt.y)
        if win and is_ignored_title(win["title"]):
            return
        now = time.time()
        click = {"button": button, "x": pt.x, "y": pt.y, "time": round(now - self._start_time, 2)}
        with self._lock:
            if merge_double_click(self._actions, click, double_click_time):
                return
        el = get_element_at(pt.x, pt.y)
        name = (el.get("name") or "").strip()
        with self._lock:
            self._actions.append({
                **click,
                "action": click_action(button, name, pt.x, pt.y),
                "type": "mouse_click",
                "name": name,
                "control_type": el.get("control_type", ""),
            })

    def _scan_loop(self, scan_queue: queue.Queue):
        """Worker thread: index each newly visited window without touching focus or the cursor."""
        ensure_desktop()
        while True:
            hwnd = scan_queue.get()
            if hwnd is None:
                break
            try:
                scan_res = deep_dive_app(hwnd=hwnd, max_elements=SCAN_MAX_ELEMENTS, background=True)
                if isinstance(scan_res, dict):
                    with self._lock:
                        self._new_controls_count += scan_res.get("new_count", 0)
            except Exception:
                pass


recorder = SessionRecorder()


def start_recording() -> dict[str, Any]:
    return recorder.start()


def stop_recording() -> dict[str, Any]:
    return recorder.stop()


def get_recording_status() -> dict[str, Any]:
    return recorder.get_status()
