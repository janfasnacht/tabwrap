# tex_compiler/utils/logging.py
import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path | None = None, module_name: str = "tex_compiler") -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        module_name: Name of the module for the logger

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Create formatters
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    simple_formatter = logging.Formatter("%(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger
