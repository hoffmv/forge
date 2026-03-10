import logging
import os
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

LOGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
LOG_FILE = os.path.join(LOGS_PATH, "build.log")

os.makedirs(LOGS_PATH, exist_ok=True)

_logger = logging.getLogger("forge")
_logger.setLevel(logging.DEBUG)

_file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)

_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
_file_handler.setFormatter(_formatter)
_logger.addHandler(_file_handler)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
_logger.addHandler(_console_handler)


def log(message: str, level: str = "info", data: dict | None = None):
    """Structured log entry to logs/build.log with optional JSON data."""
    entry = message
    if data:
        entry = f"{message} | {json.dumps(data, default=str)}"

    getattr(_logger, level.lower(), _logger.info)(entry)


def log_action(action: str, detail: str = "", data: dict | None = None):
    """Log an action with timestamp — convenience wrapper."""
    msg = f"[ACTION] {action}"
    if detail:
        msg += f" — {detail}"
    log(msg, "info", data)


def log_error(action: str, error: str, data: dict | None = None):
    """Log an error with timestamp."""
    msg = f"[ERROR] {action} — {error}"
    log(msg, "error", data)


def log_sprint(sprint: int, task: str, status: str = "start"):
    """Log sprint progress."""
    log(f"[SPRINT {sprint}] {task} — {status.upper()}")
