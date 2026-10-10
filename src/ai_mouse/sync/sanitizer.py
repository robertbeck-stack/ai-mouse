"""
Privacy & Sanitization Filter for Community Profile Sharing.
Strips Personally Identifiable Information (PII), personal file paths,
and document titles before exporting or synchronizing UI profiles.
"""

import re
from typing import Any

# Disallowed patterns that could indicate PII, URLs, or local user paths
PII_REGEX = re.compile(
    r"(?:[A-Za-z]:\\[^\s]+|\/[^\s]+|https?:\/\/[^\s]+|[\w\.-]+@[\w\.-]+|\d{6,})",
    re.IGNORECASE,
)

# Safe durable control types suitable for global sharing
COMMUNITY_WHITELIST_TYPES = {
    "buttoncontrol",
    "menuitemcontrol",
    "tabitemcontrol",
    "checkboxcontrol",
    "radiobuttoncontrol",
    "splitbuttoncontrol",
    "toolbarcontrol",
    "hyperlinkcontrol",
    "hotkeyaction",
}


def sanitize_app_name(raw_name: str) -> str:
    """Normalize and clean application identifier."""
    # Strip trailing file indicators or document names
    clean = raw_name.split("-")[-1].strip().lower()
    clean = re.sub(r"[^a-z0-9_\-\s]", "", clean).strip()
    return clean or "unknown_app"


def is_safe_element(key_name: str, el_data: dict[str, Any]) -> bool:
    """Determine if a control is safe for public community indexing."""
    label = el_data.get("name") or key_name
    if not label or len(label) < 2:
        return False

    # Block any element containing paths, emails, URLs, or long numbers in either key or label
    if PII_REGEX.search(key_name) or PII_REGEX.search(label):
        return False

    ctrl_type = (el_data.get("control_type") or "").lower()
    if ctrl_type and ctrl_type not in COMMUNITY_WHITELIST_TYPES:
        # Exclude raw text documents, edits with user input, or custom containers
        return False

    return True


def sanitize_app_profile(app_key: str, app_data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize an application profile for public community sharing.
    Returns a clean, PII-free dictionary.
    """
    clean_app = sanitize_app_name(app_key)
    elements = app_data.get("elements", {})

    sanitized_elements = {}
    for name, data in elements.items():
        if is_safe_element(name, data):
            sanitized_elements[name] = {
                "name": data.get("name", name),
                "control_type": data.get("control_type", "ButtonControl"),
                "shortcut": data.get("shortcut", ""),
                "rel_x": data.get("rel_x", 0),
                "rel_y": data.get("rel_y", 0),
                "anchor_right": data.get("anchor_right", False),
                "anchor_bottom": data.get("anchor_bottom", False),
            }

    return {
        "app": clean_app,
        "version": "1.0",
        "elements_count": len(sanitized_elements),
        "elements": sanitized_elements,
        "is_sanitized": True,
    }
