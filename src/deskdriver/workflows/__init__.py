"""
Top layer: multi-step workflows built on core, automation and navigation.
"""

from deskdriver.workflows.actions import (
    execute_action,
    save_action,
    load_saved_actions,
    delete_action,
    parse_action_string,
)
from deskdriver.workflows.recorder import (
    SessionRecorder,
    recorder,
    start_recording,
    stop_recording,
    get_recording_status,
)

__all__ = [
    "execute_action",
    "save_action",
    "load_saved_actions",
    "delete_action",
    "parse_action_string",
    "SessionRecorder",
    "recorder",
    "start_recording",
    "stop_recording",
    "get_recording_status",
]
