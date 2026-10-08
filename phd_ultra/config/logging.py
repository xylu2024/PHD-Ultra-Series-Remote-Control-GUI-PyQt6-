# -*- coding: utf-8 -*-
"""
Logging configuration for Harvard Apparatus PHD Ultra Remote Control application.
Ensures log directories exist before configuring handlers.
"""

import logging
import logging.config
import os

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Automatically create the logs directory
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE_PATH_INFO = os.path.join(LOGS_DIR, "user_info.log")
LOG_FILE_PATH_DEBUG = os.path.join(LOGS_DIR, "user_debug.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(threadName)s:%(thread)d [%(name)s] %(levelname)s [%(pathname)s:%(lineno)d] %(message)s",
            "datefmt": "[%d-%m-%Y] [%H:%M:%S]"
        },
        "simple": {
            "format": "%(asctime)s [%(name)s] %(levelname)s %(message)s",
            "datefmt": "[%d-%m-%Y] [%H:%M:%S]"
        },
        "test": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "[%d-%m-%Y] [%H:%M:%S]"
        }
    },
    "filters": {},
    "handlers": {
        "console_debug_handler": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple"
        },
        "file_info_handler": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE_PATH_INFO,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "standard"
        },
        "file_debug_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOG_FILE_PATH_DEBUG,
            "encoding": "utf-8",
            "formatter": "test"
        }
    },
    "loggers": {
        "logger1": {
            "handlers": ["console_debug_handler"],
            "level": "DEBUG",
            "propagate": False
        },
        "logger2": {
            "handlers": ["console_debug_handler", "file_debug_handler"],
            "level": "INFO",
            "propagate": False
        },
        "logger3": {
            "handlers": ["file_info_handler"],
            "level": "INFO",
            "propagate": False
        },
    }
}


def setup_logging():
    """Apply logging configuration dictionary."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


# Apply configuration on module load
setup_logging()

logger_debug_console = logging.getLogger("logger1")
logger_info_console_file = logging.getLogger("logger2")
logger_info_file = logging.getLogger("logger3")
