"""
DeskDriver Scan & Activity History Logger.
Persists unified audit logs of deep dives, auto-tours, prelearn scans,
and action pipeline executions into scan_history.json.
"""

import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).resolve().parents[3] / "scan_history.json"


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
    """Save logs to disk, keeping the most recent 200 entries."""
    try:
        trimmed = logs[:200]
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)
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
    logs = load_scan_logs()
    entry = {
        "id": len(logs) + 1,
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
    logs.insert(0, entry)
    save_scan_logs(logs)
    return entry
