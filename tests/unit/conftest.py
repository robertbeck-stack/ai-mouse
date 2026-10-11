"""
Unit tests for DeskDriver's pure logic (no live desktop needed), run by `pytest`
and in CI. tests/test_deskdriver.py is the separate end-to-end suite that drives
real windows.
"""

import os
import sys
import tempfile
from pathlib import Path

# Point the data directory at a throwaway location before deskdriver is imported:
# importing the roadmap module loads the store from DESKDRIVER_DATA_DIR.
os.environ["DESKDRIVER_DATA_DIR"] = tempfile.mkdtemp(prefix="deskdriver-unit-")

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
