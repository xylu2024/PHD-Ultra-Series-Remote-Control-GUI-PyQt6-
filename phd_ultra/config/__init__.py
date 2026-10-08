# -*- coding: utf-8 -*-
"""Configuration module."""

from .logging import (
    setup_logging,
    logger_debug_console,
    logger_info_console_file,
    logger_info_file,
    LOGS_DIR,
)

__all__ = [
    "setup_logging",
    "logger_debug_console",
    "logger_info_console_file",
    "logger_info_file",
    "LOGS_DIR",
]
