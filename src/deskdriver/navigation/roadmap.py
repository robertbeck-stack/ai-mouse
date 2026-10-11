"""
Persistent UI Roadmap store: spatial UI element caching and fast O(1) retrieval.

Storage only - this module has no knowledge of mouse, keyboard or windows. The
actions built on top of it (fast_click_element, fill_input, ...) live in
deskdriver.navigation.interact.
"""

import hashlib
import json
import msvcrt
import os
import re
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from deskdriver.navigation.hotkeys import APP_PROFILES
from deskdriver.paths import ROADMAP_DIR, LEGACY_ROADMAP_FILE


# Whole-word title patterns, so e.g. "System Restore" is not "Microsoft Store"
# and "painting.docx - Word" is not Paint.
APP_KEY_PATTERNS = [
    (r"\bmicrosoft store\b|^store$", "Microsoft Store"),
    (r"\bpaint\b", "paint"),
    (r"\bpolytopia\b", "Polytopia"),
    (r"\bbrave\b", "brave"),
    (r"\bchrome\b", "chrome"),
    (r"^settings\b|\bsettings$", "settings"),
    (r"\bnotepad\b", "notepad"),
    (r"\bfile explorer\b|\bconfigs\b", "explorer"),
]

LOCK_FILE_NAME = ".lock"


def match_element_key(elements: dict, query: str) -> str | None:
    """Exact key, else the shortest cached key that contains the query as a whole word."""
    q = query.strip().lower()
    if not q:
        return None
    if q in elements:
        return q
    word = re.compile(r"(?<!\w)" + re.escape(q) + r"(?!\w)")
    hits = [k for k in elements if word.search(k)]
    return min(hits, key=len) if hits else None


def app_file_slug(app_key: str) -> str:
    """Filesystem-safe file stem for an app key ("Administrator: Command Prompt" -> "administrator-command-prompt")."""
    slug = re.sub(r"[^a-z0-9._]+", "-", app_key.lower()).strip("-._")[:60]
    return slug or "app"


def _serialize(app_key: str, app_data: dict) -> str:
    return json.dumps({"app_key": app_key, **app_data}, indent=2, ensure_ascii=False)


class UIRoadmap:
    """
    In-memory roadmap ({app_key: app_data}) persisted as one JSON file per app
    under ui_roadmap/. Each file carries its own "app_key" so the original
    (possibly non-filesystem-safe) key round-trips exactly.

    Several processes (dashboard, MCP server) and threads (session recorder) share
    the files, so:
    - writes are serialized by a thread lock plus a lock file in the directory;
    - before writing an app, a version another process saved in the meantime is
      merged in (its elements are kept unless this process also has them);
    - lookups pick up files other processes changed (see refresh_app).
    """

    def __init__(self, directory: Path = ROADMAP_DIR, legacy_file: Path | None = LEGACY_ROADMAP_FILE):
        self.directory = Path(directory)
        self.legacy_file = legacy_file
        self.map: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._files: dict[str, str] = {}             # app_key -> file name
        self._written: dict[str, str] = {}           # app_key -> content last read from / written to disk
        self._stamps: dict[str, tuple] = {}          # app_key -> (mtime_ns, size) of that content
        self._removed: dict[str, set[str]] = {}      # app_key -> element keys deleted since last save
        self._load()

    @property
    def filepath(self) -> Path:
        return self.directory

    # ------------------------------------------------------------------ disk I/O

    @contextmanager
    def _disk_lock(self):
        """Exclusive lock across threads and processes for read-merge-write cycles."""
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            with open(self.directory / LOCK_FILE_NAME, "a+b") as fh:
                deadline = time.monotonic() + 5.0
                while True:
                    try:
                        fh.seek(0)
                        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        if time.monotonic() > deadline:
                            raise
                        time.sleep(0.01)
                try:
                    yield
                finally:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)

    @staticmethod
    def _stamp(path: Path) -> tuple | None:
        try:
            st = path.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return None

    def _read_file(self, path: Path) -> tuple[str, dict, str] | None:
        """(app_key, app_data, raw text) of one app file, or None if unreadable."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            app_data = json.loads(raw)
            return app_data.pop("app_key", path.stem), app_data, raw
        except Exception:
            return None

    def _adopt(self, app_key: str, app_data: dict, path: Path, raw: str):
        """Make a disk version the in-memory one, updating the dict in place so held references stay live."""
        current = self.map.get(app_key)
        if current is None:
            self.map[app_key] = app_data
        else:
            current.clear()
            current.update(app_data)
        self._files[app_key] = path.name
        self._written[app_key] = raw
        self._stamps[app_key] = self._stamp(path)

    def _load(self):
        with self._lock:
            if not self.directory.exists():
                self._migrate_legacy()
                return

            seen = set()
            for path in sorted(self.directory.glob("*.json")):
                parsed = self._read_file(path)
                if not parsed:
                    continue
                app_key, app_data, raw = parsed
                seen.add(app_key)
                if self._written.get(app_key) != raw:
                    self._adopt(app_key, app_data, path, raw)
            # Apps whose files were deleted on disk (by this or another process)
            for app_key in [k for k in self._files if k not in seen]:
                self.map.pop(app_key, None)
                self._forget(app_key)

    def _migrate_legacy(self):
        """One-time split of the old monolithic ui_roadmap.json into per-app files."""
        if not self.legacy_file or not self.legacy_file.exists():
            return
        try:
            with open(self.legacy_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        self.map.update(data)
        self.save()
        try:
            self.legacy_file.replace(self.legacy_file.with_name(self.legacy_file.name + ".migrated"))
        except Exception:
            pass

    def _forget(self, app_key: str):
        for d in (self._files, self._written, self._stamps, self._removed):
            d.pop(app_key, None)

    def reload(self) -> dict:
        """Pick up changes other processes wrote. The map is updated in place and returned."""
        self._load()
        return self.map

    def refresh_app(self, app_key: str):
        """Re-read one app's file if another process changed it since we last saw it."""
        name = self._files.get(app_key)
        if not name:
            if not self.directory.exists():
                return
            name = f"{app_file_slug(app_key)}.json"
        path = self.directory / name
        stamp = self._stamp(path)
        if stamp is None or stamp == self._stamps.get(app_key):
            return
        with self._lock:
            parsed = self._read_file(path)
            if parsed and parsed[0] == app_key and parsed[2] != self._written.get(app_key):
                self._adopt(app_key, parsed[1], path, parsed[2])
            else:
                self._stamps[app_key] = stamp

    def app_file(self, app_key: str) -> Path:
        """Path of the storage file for an app, assigning a unique name on first use."""
        name = self._files.get(app_key)
        if not name:
            stem = app_file_slug(app_key)
            name = f"{stem}.json"
            existing = self.directory / name
            if name in self._files.values() or (
                existing.exists() and (self._read_file(existing) or (None,))[0] != app_key
            ):
                digest = hashlib.sha1(app_key.encode("utf-8")).hexdigest()[:8]
                name = f"{stem}-{digest}.json"
            self._files[app_key] = name
        return self.directory / name

    def _merge_from_disk(self, app_key: str, path: Path):
        """Fold in a version another process saved after we last read/wrote this app."""
        parsed = self._read_file(path)
        if not parsed or parsed[0] != app_key or parsed[2] == self._written.get(app_key):
            return
        disk = parsed[1]
        mine = self.map[app_key]
        disk_elements = disk.get("elements", {})
        # Three-way merge against the version we last saw: an element that is gone from
        # disk and that we have not changed since was deleted elsewhere - don't revive it.
        try:
            base_elements = json.loads(self._written[app_key]).get("elements", {}) if app_key in self._written else {}
        except Exception:
            base_elements = {}
        my_elements = {
            k: v for k, v in mine.get("elements", {}).items()
            if k in disk_elements or k not in base_elements or base_elements[k] != v
        }
        removed = self._removed.get(app_key, set())
        elements = {k: v for k, v in disk_elements.items() if k not in removed}
        elements.update(my_elements)
        merged = {**disk, **mine, "elements": elements}
        merged["last_updated"] = max(disk.get("last_updated", 0), mine.get("last_updated", 0))
        mine.clear()
        mine.update(merged)

    def _write_app(self, app_key: str):
        path = self.app_file(app_key)
        self._merge_from_disk(app_key, path)
        content = _serialize(app_key, self.map[app_key])
        if self._written.get(app_key) == content and path.exists():
            return
        tmp = path.with_name(path.name + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            os.replace(tmp, path)
            self._written[app_key] = content
            self._stamps[app_key] = self._stamp(path)
            self._removed.pop(app_key, None)
        except Exception:
            pass

    def save(self, app_key: str | None = None):
        """Write changed app files (or only app_key's) and remove files of apps deleted from the map."""
        try:
            with self._disk_lock():
                keys = [app_key] if app_key is not None else list(self.map.keys())
                for key in keys:
                    if key in self.map:
                        self._write_app(key)

                if app_key is None:
                    for key in [k for k in self._files if k not in self.map]:
                        try:
                            (self.directory / self._files[key]).unlink(missing_ok=True)
                        except Exception:
                            pass
                        self._forget(key)
        except Exception:
            pass

    # ------------------------------------------------------------------ data API

    def remove_element(self, app_key: str, element_key: str) -> bool:
        """Delete one cached element and persist that (the deletion survives cross-process merges)."""
        with self._lock:
            elements = self.map.get(app_key, {}).get("elements", {})
            if element_key not in elements:
                return False
            del elements[element_key]
            self._removed.setdefault(app_key, set()).add(element_key)
            self.save(app_key)
            return True

    def get_app_key(self, window_title: str) -> str:
        """Normalize window title to identify application family."""
        t = window_title.lower()
        for pattern, key in APP_KEY_PATTERNS:
            if re.search(pattern, t):
                return key
        return window_title[:30].strip()

    def learn_window(
        self,
        window_title: str,
        elements: list[dict],
        window_rect: dict,
        process_info: dict | None = None,
        categories: dict | None = None,
    ):
        """Cache elements using coordinates relative to the window top-left."""
        with self._lock:
            app_key = self.get_app_key(window_title)
            if app_key not in self.map:
                self.map[app_key] = {"elements": {}, "last_updated": time.time()}

            if process_info:
                self.map[app_key]["process_info"] = process_info
            if categories:
                self.map[app_key]["categories"] = categories

            win_left = window_rect["left"]
            win_top = window_rect["top"]
            win_w = max(1, window_rect.get("right", win_left + 800) - win_left)
            win_h = max(1, window_rect.get("bottom", win_top + 600) - win_top)

            for el in elements:
                name = (el.get("name") or "").strip().lower()
                if not name or name.startswith("("):
                    continue

                rel_x = el["center_x"] - win_left
                rel_y = el["center_y"] - win_top
                anchor_right = rel_x > (win_w * 0.65)
                anchor_bottom = rel_y > (win_h * 0.65)

                existing_el = self.map[app_key]["elements"].get(name, {})
                final_sc = el.get("shortcut", "") or existing_el.get("shortcut", "")

                ct = el.get("control_type", "ButtonControl")
                if final_sc:
                    ai_action = f"hotkey:{final_sc.lower()}"
                elif any(k in ct for k in ("Edit", "ComboBox", "Spinner", "Document")):
                    ai_action = f"fill:{el.get('name', name)}, <text>"
                else:
                    ai_action = f"click:{el.get('name', name)}"

                self.map[app_key]["elements"][name] = {
                    "name": el.get("name", name),
                    "control_type": ct,
                    "shortcut": final_sc,
                    "rel_x": rel_x,
                    "rel_y": rel_y,
                    "anchor_right": anchor_right,
                    "anchor_bottom": anchor_bottom,
                    "dist_from_right": win_w - rel_x,
                    "dist_from_bottom": win_h - rel_y,
                    "width": el.get("rect", {}).get("width", 0),
                    "height": el.get("rect", {}).get("height", 0),
                    "automation_id": el.get("automation_id", existing_el.get("automation_id", "")),
                    "class_name": el.get("class_name", existing_el.get("class_name", "")),
                    "help_text": el.get("help_text", existing_el.get("help_text", "")),
                    "value": el.get("value", existing_el.get("value", "")),
                    "toggle_state": el.get("toggle_state", existing_el.get("toggle_state", None)),
                    "container_path": el.get("container_path", existing_el.get("container_path", "")),
                    "ai_action": el.get("ai_action", ai_action),
                    "is_enabled": el.get("is_enabled", existing_el.get("is_enabled", True)),
                }

            # Merge standard application hotkey profiles if known
            app_profile = APP_PROFILES.get(app_key, {})
            for action_name, hk in app_profile.items():
                matched_key = None
                for k in self.map[app_key]["elements"]:
                    if action_name in k or k in action_name:
                        matched_key = k
                        break
                if matched_key:
                    if not self.map[app_key]["elements"][matched_key].get("shortcut"):
                        self.map[app_key]["elements"][matched_key]["shortcut"] = hk
                else:
                    self.map[app_key]["elements"][action_name] = {
                        "name": action_name.title(),
                        "control_type": "HotkeyAction",
                        "shortcut": hk,
                        "rel_x": 0,
                        "rel_y": 0,
                        "width": 0,
                        "height": 0,
                    }

            self.map[app_key]["last_updated"] = time.time()
            self.save(app_key)

    def find_cached_element(self, window_title: str, element_name: str, window_rect: dict) -> dict | None:
        """O(1) instant lookup from roadmap memory."""
        app_key = self.get_app_key(window_title)
        self.refresh_app(app_key)
        app_data = self.map.get(app_key)
        if not app_data:
            return None

        elements = app_data.get("elements", {})
        key = match_element_key(elements, element_name)
        matched = elements.get(key) if key else None

        # Win32 menu items and profile hotkeys are stored without geometry; without a
        # shortcut there is nothing to press and no real point to click.
        if matched and not matched.get("shortcut") and not (matched.get("width") and matched.get("height")):
            matched = None

        if matched:
            curr_w = window_rect.get("right", 0) - window_rect.get("left", 0)
            curr_h = window_rect.get("bottom", 0) - window_rect.get("top", 0)

            # Responsive right-anchor adjustment
            if matched.get("anchor_right") and curr_w > 0 and matched.get("dist_from_right", 0) > 0:
                abs_x = window_rect["right"] - matched["dist_from_right"]
            else:
                abs_x = window_rect["left"] + matched["rel_x"]

            # Responsive bottom-anchor adjustment
            if matched.get("anchor_bottom") and curr_h > 0 and matched.get("dist_from_bottom", 0) > 0:
                abs_y = window_rect["bottom"] - matched["dist_from_bottom"]
            else:
                abs_y = window_rect["top"] + matched["rel_y"]

            return {
                "name": matched["name"],
                "control_type": matched["control_type"],
                "shortcut": matched.get("shortcut", ""),
                "center_x": abs_x,
                "center_y": abs_y,
                "source": "roadmap_cache",
            }
        return None


roadmap = UIRoadmap()


def __getattr__(name):
    """Backward compatibility: the roadmap actions moved to deskdriver.navigation.interact."""
    if name in _MOVED_TO_INTERACT:
        from deskdriver.navigation import interact
        return getattr(interact, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_MOVED_TO_INTERACT = {
    "fast_click_element",
    "fill_input",
    "record_element_at_cursor",
    "wait_for_element",
    "wait_and_click",
    "auto_record_window",
}
