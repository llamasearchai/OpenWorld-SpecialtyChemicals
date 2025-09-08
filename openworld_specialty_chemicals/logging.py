from __future__ import annotations

import contextvars
import datetime as _dt
import json as _json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

_configured = False
_corr_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("corr_id", default="")


def set_correlation_id(corr_id: str) -> None:
    _corr_id_var.set(corr_id)


def get_correlation_id() -> str:
    return _corr_id_var.get()


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        try:
            record.corr_id = get_correlation_id()
        except Exception:
            record.corr_id = ""
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        ts = _dt.datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        payload = {
            "ts": ts,
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "corr_id": getattr(record, "corr_id", ""),
        }
        # Optional structured fields
        if hasattr(record, "event"):
            payload["event"] = getattr(record, "event")
        if hasattr(record, "fields"):
            try:
                payload["fields"] = getattr(record, "fields")
            except Exception:
                payload["fields"] = {}
        return _json.dumps(payload, ensure_ascii=False)

def _setup_file_handler(log_file: Path, json_format: bool = False) -> logging.Handler:
    """Setup rotating file handler for production logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )

    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    handler.setFormatter(formatter)
    return handler

def _setup_console_handler(use_rich: bool = True, json_format: bool = False) -> logging.Handler:
    """Setup console handler with optional Rich formatting."""
    if json_format:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
    elif use_rich:
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False,
            show_time=False
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
    return handler

def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_rich: bool = True,
    enable_file_logging: bool = True,
    json_format: bool = False,
) -> None:
    """
    Configure application-wide logging.
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to logs/openworld-chem.log)
        use_rich: Use Rich formatting for console output
        enable_file_logging: Enable file logging in addition to console
    """
    global _configured

    if _configured:
        return

    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Setup handlers
    handlers = []

    # Console handler
    console_handler = _setup_console_handler(use_rich, json_format)
    console_handler.setLevel(numeric_level)
    console_handler.addFilter(CorrelationFilter())
    handlers.append(console_handler)

    # File handler for production
    if enable_file_logging:
        if log_file is None:
            log_file = Path("logs/openworld-chem.log")
        else:
            log_file = Path(log_file)

        file_handler = _setup_file_handler(log_file, json_format)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.addFilter(CorrelationFilter())
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything, handlers filter
        handlers=handlers,
        format="%(message)s" if use_rich else None
    )

    # Suppress noisy third-party loggers (keep uvicorn.access visible in JSON mode)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    if not json_format:
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    _configured = True

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    Args:
        name: Logger name (typically __name__)
        level: Override default logging level for this logger
    Returns:
        Configured logger instance
    """
    global _configured
    if not _configured:
        # Auto-configure with defaults if not explicitly configured
        configure_logging()

    logger = logging.getLogger(name)

    if level:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

    return logger

def setup_production_logging(json_format: bool = False) -> None:
    """Setup production-ready logging configuration."""
    configure_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/openworld-chem.log"),
        use_rich=not json_format,  # rich only in text mode
        enable_file_logging=True,
        json_format=json_format or os.getenv("LOG_FORMAT", "text").lower() == "json",
    )

def setup_development_logging(json_format: bool = False) -> None:
    """Setup development logging configuration with Rich formatting."""
    configure_logging(
        level="DEBUG",
        use_rich=not json_format,
        enable_file_logging=False,  # Console only for development
        json_format=json_format or os.getenv("LOG_FORMAT", "text").lower() == "json",
    )


def uvicorn_log_config(json_format: bool = False) -> dict:
    """Return a logging dictConfig for uvicorn with optional JSON access logs."""
    if not json_format:
        return {}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": "openworld_specialty_chemicals.logging.JSONFormatter"}
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
        "root": {"handlers": ["default"], "level": "INFO"},
    }
