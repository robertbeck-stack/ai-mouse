"""
Locations of DeskDriver's persistent data files.

Everything lives in the project root by default. Set DESKDRIVER_DATA_DIR to keep
the roadmap, scan history and saved actions somewhere else (the test suite uses
this to run against a throwaway copy instead of the real data).
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DESKDRIVER_DATA_DIR") or PROJECT_ROOT)

ROADMAP_DIR = DATA_DIR / "ui_roadmap"
LEGACY_ROADMAP_FILE = DATA_DIR / "ui_roadmap.json"
SCAN_HISTORY_FILE = DATA_DIR / "scan_history.json"
SAVED_ACTIONS_FILE = DATA_DIR / "saved_actions.json"
