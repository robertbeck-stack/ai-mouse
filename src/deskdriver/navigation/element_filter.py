"""
Which scanned elements are worth caching in the roadmap, and under what name.

The roadmap stores controls at fixed window-relative positions, so it should only
hold an app's own UI. Two kinds of elements don't fit:

  * transient content: open document / browser tabs ("notes.txt. Modified.",
    "Inbox - Gmail - Memory usage - 280 MB") and anything inside a web page.
    Their names and positions change every time, so a cached hit would click the
    wrong thing, and they'd fill the store with page titles.
  * secrets: names that look like API keys or tokens (a document tab named after
    its first line can be one).

Pure functions, so the rules can be tested without UI Automation.
"""

import re

from deskdriver.core.shortcuts import extract_shortcut_from_name

BROWSER_EXES = frozenset({
    "brave.exe", "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe",
    "vivaldi.exe", "arc.exe", "chromium.exe",
})

# In a browser only the toolbar / menus are app UI; lists, links, tabs and text
# come from tabs or web pages.
BROWSER_CONTENT_TYPES = frozenset({
    "DataItemControl", "ListItemControl", "HyperlinkControl", "TabItemControl",
    "TextControl", "DocumentControl", "ImageControl", "TreeItemControl",
})

# Container segments of embedded web content (Chromium / Electron / WebView2)
WEB_CONTENT_MARKERS = ("Chrome Legacy Window", "Chrome_RenderWidgetHostHWND")

# Tab strips whose items are open documents (Notepad: "Tabs", Terminal: "TabView")
DOCUMENT_TAB_CONTAINERS = re.compile(r"id:(Tabs|TabView)$")

TRANSIENT_NAME_PATTERNS = [
    re.compile(r"memory usage\s*-\s*[\d.,]+\s*[kmg]b", re.I),   # Chromium tab tooltips
    re.compile(r"\.\s*(un)?modified\.$", re.I),                 # Notepad tab names
]

SECRET_PATTERN = re.compile(
    r"\b(sk-ant-[\w-]+|sk-(proj-)?[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|xox[abpr]-[\w-]{10,}|AIza[\w-]{30,})"
)


def looks_secret(text: str) -> bool:
    return bool(SECRET_PATTERN.search(text or ""))


def redact_secrets(text: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", text or "")


def is_transient(element: dict, exe: str = "") -> bool:
    """True if the element shouldn't be cached for the app running `exe`."""
    name = element.get("name") or ""
    ct = element.get("control_type") or ""
    container = element.get("container_path") or ""

    if looks_secret(name):
        return True
    if any(p.search(name) for p in TRANSIENT_NAME_PATTERNS):
        return True
    if any(m in container for m in WEB_CONTENT_MARKERS):
        return True
    if ct == "TabItemControl" and DOCUMENT_TAB_CONTAINERS.search(container):
        return True
    if (exe or "").lower() in BROWSER_EXES and ct in BROWSER_CONTENT_TYPES:
        return True
    return False


# Names uia.get_element_name() invents for controls without a name / id / help text.
# They embed *screen* coordinates, so they change whenever the window moves.
UNNAMED = re.compile(r"^unnamed_([a-z]+?)(?:control)?_-?\d+_-?\d+$")


def normalize_name(name: str, rel_x: int, rel_y: int) -> tuple[str, str]:
    """
    (display name, shortcut) to cache an element under:
      "Media Alt+M", "Bold (Ctrl+B)"        -> ("Media", "Alt+M"), ("Bold", "Ctrl+B")
      "unnamed_buttoncontrol_477_1204"      -> ("button @ 62,985", "")   window-relative
    """
    name = (name or "").strip()
    m = UNNAMED.match(name)
    if m:
        return f"{m.group(1)} @ {rel_x},{rel_y}", ""
    return extract_shortcut_from_name(name)



def prefer_shortcut(from_name: str, reported: str) -> str:
    """
    The shortcut to store: UIA's reported one, unless it's only an access key
    ("Alt, B": a menu mnemonic) and the name carries a real accelerator ("Ctrl+B").
    """
    if from_name and (not reported or reported.lower().startswith("alt,")):
        return from_name
    return reported or from_name


# Controls whose value is user content (typed text, the URL in an address bar,
# a search box), not a label of the app's UI
INPUT_TYPES = ("Edit", "ComboBox", "Document", "Spinner")


def storable_value(control_type: str, value) -> str:
    """The element value to cache: empty for input fields, secrets redacted otherwise."""
    if any(t in (control_type or "") for t in INPUT_TYPES):
        return ""
    return redact_secrets(str(value or ""))
