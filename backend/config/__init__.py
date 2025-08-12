# ------------------------------ CONFIG MODULE INITIALIZATION ------------------------------
"""
Configuration module for Turolytics backend.

This module contains browser settings, validation functions, and configuration constants
used throughout the application.
"""

from .browser_settings import (
    launch_browser,
    USER_AGENT,
    DEFAULT_VIEWPORT,
    BROWSER_LAUNCH_ARGS,
    DEFAULT_TIMEOUT,
    DEFAULT_HEADLESS,
    validate_viewport,
    validate_user_agent,
)

__all__ = [
    "launch_browser",
    "USER_AGENT",
    "DEFAULT_VIEWPORT",
    "BROWSER_LAUNCH_ARGS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_HEADLESS",
    "validate_viewport",
    "validate_user_agent",
]
