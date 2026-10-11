"""
DeskDriver Scan & Activity History Logger.
Persists unified audit logs of deep dives, auto-tours, prelearn scans,
and action pipeline executions into scan_history.json.
"""

import json
import os
import threading
from datetime import datetime

from deskdriver.paths import SCAN_HISTORY_FILE as LOG_FILE
MAX_LOGS = 200

# Dashboard requests run on several threads; serialize read-modify-write of the log file.
_log_lock = threading.Lock()


def load_scan_logs() -> list[dict]:
    """Load all historical scan and activity logs from disk."""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_scan_logs(logs: list[dict]) -> bool:
    """Save logs to disk atomically, keeping the most recent MAX_LOGS entries."""
    tmp = LOG_FILE.with_name(LOG_FILE.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(logs[:MAX_LOGS], f, indent=2, ensure_ascii=False)
        os.replace(tmp, LOG_FILE)
        return True
    except Exception:
        return False


def record_scan_log(
    action: str,
    app: str,
    summary: str,
    count: int = 0,
    new_count: int = 0,
    new_items: list | None = None,
    shortcuts_count: int = 0,
    items: list | None = None,
    duration: float = 0.0,
    status: str = "success",
) -> dict:
    """Append a new scan or action log entry and persist to scan_history.json."""
    with _log_lock:
        logs = load_scan_logs()
        # len(logs) + 1 repeats once the log is trimmed to MAX_LOGS; continue from the highest id.
        next_id = max((e.get("id", 0) for e in logs if isinstance(e, dict)), default=0) + 1
        entry = _make_entry(next_id, action, app, summary, count, new_count, new_items,
                            shortcuts_count, items, duration, status)
        logs.insert(0, entry)
        save_scan_logs(logs)
    return entry


def _make_entry(entry_id, action, app, summary, count, new_count, new_items,
                shortcuts_count, items, duration, status) -> dict:
    return {
        "id": entry_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_str": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "app": app,
        "summary": summary,
        "count": count,
        "new_count": new_count,
        "new_items": new_items or [],
        "shortcuts_count": shortcuts_count,
        "items": items or [],
        "duration": f"{duration:.2f}s" if duration else "",
        "status": status,
    }
