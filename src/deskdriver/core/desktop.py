"""
Windows desktop station, thread input synchronization, and COM initialization.
"""

import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
ole32 = ctypes.windll.ole32


def enable_dpi_awareness():
    """Ensure process is Per-Monitor DPI aware for accurate screen coordinates."""
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def attach_thread_desktop():
    """Ensure the calling thread is attached to the interactive 'default' desktop."""
    enable_dpi_awareness()
    try:
        hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def init_com():
    """Initialize COM on the calling thread."""
    try:
        ole32.CoInitialize(None)
    except Exception:
        pass


def ensure_desktop():
    """Ensure both desktop attachment and COM initialization for the thread."""
    attach_thread_desktop()
    init_com()


# Ensure the importing thread is attached immediately before UI libraries load
attach_thread_desktop()
