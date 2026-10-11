"""
Schema migration for the roadmap store.

Schema 1 keyed apps by (normalized) window titles: "notepad", "Untitled - Paint",
"◐ ai-mouse", "Page setup". Schema 2 keys them by executable (see
deskdriver.automation.appid). This module maps old entries to new keys; it is pure
so it can be tested without touching disk.
"""

from deskdriver.automation.appid import (
    PRIMARY_HOST_CLASS,
    display_name_for,
    key_for,
    surface_name,
)

SCHEMA_VERSION = 2

# Title-derived keys whose process info is missing or points at a host process.
LEGACY_KEY_MAP = {
    "settings": "systemsettings.exe",
    "microsoft store": "winstore.app.exe",
    "paint": "mspaint.exe",
    "untitled - paint": "mspaint.exe",
    "notepad": "notepad.exe",
    "brave": "brave.exe",
    "chrome": "chrome.exe",
    "explorer": "explorer.exe",
    "taskbar": "explorer.exe#shell_traywnd",
    "polytopia": "polytopia.exe",
    "snipping tool": "snippingtool.exe",
}

DIALOG_CLASS = "#32770"


def legacy_target_key(old_key: str, data: dict) -> str | None:
    """Schema-2 key for a schema-1 entry, or None if it can't be attributed to a program."""
    mapped = LEGACY_KEY_MAP.get(old_key.strip().lower())
    if mapped:
        return mapped

    info = data.get("process_info") or {}
    exe = (info.get("exe_name") or "").lower()
    cls = info.get("class_name") or ""
    if not exe or exe == "applicationframehost.exe":
        return None
    if cls == DIALOG_CLASS:
        owner = key_for(exe, PRIMARY_HOST_CLASS.get(exe, ""))
        return f"{owner}/{surface_name(old_key)}"
    return key_for(exe, cls)


def describe(key: str) -> dict:
    """Metadata fields stored with every schema-2 entry."""
    app_key, _, surface = key.partition("/")
    exe = app_key.split("#", 1)[0] if not app_key.startswith("#") else ""
    return {
        "schema": SCHEMA_VERSION,
        "display_name": display_name_for(app_key),
        "exe": exe,
        "surface": surface,
    }


def migrate_entries(old: dict[str, dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Map schema-1 entries to schema-2 keys.
    Returns (migrated, unmigrated). Entries landing on the same key are merged in
    last_updated order, so newer element data wins. Old keys (window titles) are not
    kept in the migrated data.
    """
    migrated: dict[str, dict] = {}
    unmigrated: dict[str, dict] = {}

    for old_key, data in sorted(old.items(), key=lambda kv: kv[1].get("last_updated", 0)):
        if data.get("schema") == SCHEMA_VERSION:
            target = old_key
        else:
            target = legacy_target_key(old_key, data)
        if not target:
            unmigrated[old_key] = data
            continue

        entry = migrated.setdefault(target, {"elements": {}, "last_updated": 0})
        entry["elements"].update(data.get("elements", {}))
        for field in ("process_info", "categories"):
            if data.get(field):
                entry[field] = data[field]
        entry["last_updated"] = max(entry["last_updated"], data.get("last_updated", 0))

    for key, entry in migrated.items():
        for field, value in describe(key).items():
            entry.setdefault(field, value)
        entry["schema"] = SCHEMA_VERSION
    return migrated, unmigrated
