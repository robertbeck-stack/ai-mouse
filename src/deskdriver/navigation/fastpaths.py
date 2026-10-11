"""
Windows direct URI and deep-link fastpaths for zero-click navigation.
"""

import os

FASTPATHS = {
    "system": "ms-settings:system",
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "notifications": "ms-settings:notifications",
    "power": "ms-settings:powersleep",
    "battery": "ms-settings:batterysaver",
    "storage": "ms-settings:storagesense",
    "bluetooth": "ms-settings:bluetooth",
    "network": "ms-settings:network",
    "wifi": "ms-settings:network-wifi",
    "vpn": "ms-settings:network-vpn",
    "personalization": "ms-settings:personalization",
    "background": "ms-settings:personalization-background",
    "colors": "ms-settings:personalization-colors",
    "themes": "ms-settings:themes",
    "lockscreen": "ms-settings:lockscreen",
    "apps": "ms-settings:appsfeatures",
    "defaultapps": "ms-settings:defaultapps",
    "startup": "ms-settings:startupapps",
    "accounts": "ms-settings:yourinfo",
    "time": "ms-settings:dateandtime",
    "region": "ms-settings:regionformatting",
    "language": "ms-settings:keyboard",
    "gaming": "ms-settings:gaming-gamebar",
    "accessibility": "ms-settings:easeofaccess-display",
    "mouse": "ms-settings:mousetouchpad",
    "update": "ms-settings:windowsupdate",
    "security": "windowsdefender:",
    "about": "ms-settings:about",
    "calculator": "calc:",
    "explorer": "explorer.exe",
    "taskmgr": "taskmgr.exe",
    "notepad": "notepad.exe",
    "paint": "mspaint.exe",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "polytopia": r"C:\Users\rober\Downloads\The.Battle.of.Polytopia.v2.3.5.9320\Polytopia.exe",
}


def execute_fastpath(target: str) -> bool:
    """Execute direct OS URI shortcut if recognized."""
    key = target.strip().lower()
    uri = FASTPATHS.get(key)
    if uri:
        os.system(f"start {uri}")
        return True
    return False
