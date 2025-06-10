import logging
import os
from logging.handlers import TimedRotatingFileHandler

def init_logging(
    log_level=logging.INFO,
    log_dir="logs",
    log_file_name="automation.log",
    when="midnight",
    backup_count=14,
    console_log_level=None
):
    """
    Initialize logging for the Gmail automation system.

    Args:
        log_level (int): The minimum log level for file logging (default: logging.INFO).
        log_dir (str): Directory where log files are stored (default: 'logs').
        log_file_name (str): Name of the log file (default: 'automation.log').
        when (str): Rotation interval for TimedRotatingFileHandler (default: 'midnight').
        backup_count (int): Number of days to retain log files (default: 14).
        console_log_level (int or None): Log level for console output (default: same as log_level).
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_format = (
        "%(asctime)s [%(levelname)s] %(module)s: %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Allow all levels, handlers will filter

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, log_file_name),
        when=when,
        backupCount=backup_count,
        encoding="utf-8",
        utc=True
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(file_handler)

    # Console handler
    ch_level = console_log_level if console_log_level is not None else log_level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(ch_level)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(console_handler)

def get_logger(name=None):
    """
    Get a logger for a given module or script.

    Args:
        name (str or None): The logger name (usually __name__). If None, returns the root logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)