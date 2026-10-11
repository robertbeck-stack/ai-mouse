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
from deskdriver.automation.windows import user32
from deskdriver.automation.uia import get_element_at
from deskdriver.navigation.roadmap import roadmap
from deskdriver.navigation.history import record_scan_log
from deskdriver.navigation.deepdive import deep_dive_app

SCAN_MAX_ELEMENTS = 250


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

        # Assemble clean pipeline string without redundant repeated clicks
        clean_steps = []
        prev_act = ""
        for item in self._actions:
            act = item.get("action", "").strip()
            if act and act != prev_act:
                clean_steps.append(act)
                prev_act = act

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
        last_lbutton = False
        last_click_time = 0.0

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

                    # Avoid recording the dashboard itself or developer tools
                    lt = title.lower()
                    if title and "dashboard" not in lt and "antigravity" not in lt:
                        app_key = roadmap.get_app_key(title)
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
                                "window_title": title,
                                "time": elapsed,
                            })

                        last_hwnd = curr_hwnd

                # 2. Detect User Left Clicks
                is_lbutton_pressed = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
                if is_lbutton_pressed and not last_lbutton:
                    now = time.time()
                    if now - last_click_time > 0.15:
                        last_click_time = now
                        pt = wintypes.POINT()
                        user32.GetCursorPos(ctypes.byref(pt))

                        # Inspect element under cursor
                        el = get_element_at(pt.x, pt.y)
                        el_name = (el.get("name") or "").strip()
                        ct = el.get("control_type", "")
                        elapsed = round(now - self._start_time, 2)

                        if el_name and el_name != "(no text)":
                            act_str = f"click:{el_name}"
                        else:
                            act_str = f"click:{pt.x},{pt.y}"

                        with self._lock:
                            self._actions.append({
                                "action": act_str,
                                "type": "mouse_click",
                                "name": el_name,
                                "control_type": ct,
                                "x": pt.x,
                                "y": pt.y,
                                "time": elapsed,
                            })

                last_lbutton = is_lbutton_pressed

            except Exception:
                pass

            time.sleep(0.04)


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
