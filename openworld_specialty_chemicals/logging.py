from __future__ import annotations
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from .config import settings

_configured = False

def _setup_file_handler(log_file: Path) -> logging.Handler:
    """Setup rotating file handler for production logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    return handler

def _setup_console_handler(use_rich: bool = True) -> logging.Handler:
    """Setup console handler with optional Rich formatting."""
    if use_rich:
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
    enable_file_logging: bool = True
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
    console_handler = _setup_console_handler(use_rich)
    console_handler.setLevel(numeric_level)
    handlers.append(console_handler)
    
    # File handler for production
    if enable_file_logging:
        if log_file is None:
            log_file = Path("logs/openworld-chem.log")
        else:
            log_file = Path(log_file)
            
        file_handler = _setup_file_handler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything, handlers filter
        handlers=handlers,
        format="%(message)s" if use_rich else None
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING) 
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

def setup_production_logging() -> None:
    """Setup production-ready logging configuration."""
    configure_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/openworld-chem.log"), 
        use_rich=False,  # Disable rich formatting in production
        enable_file_logging=True
    )

def setup_development_logging() -> None:
    """Setup development logging configuration with Rich formatting."""
    configure_logging(
        level="DEBUG",
        use_rich=True,
        enable_file_logging=False  # Console only for development
    )


