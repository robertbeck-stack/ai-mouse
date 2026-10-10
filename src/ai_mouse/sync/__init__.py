"""
Sync & Cloud Module Skeleton for ai-mouse.
Provides profile sanitization, bundle exporting, and future community hub integration.
"""

from ai_mouse.sync.sanitizer import sanitize_app_profile
from ai_mouse.sync.client import CloudSyncClient

__all__ = ["sanitize_app_profile", "CloudSyncClient"]
