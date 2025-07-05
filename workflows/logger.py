import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FILE = "workflow_execution.log"

def setup_logger(name='workflow_logger', log_file=LOG_FILE, level=logging.INFO):
    """
    Sets up a standardized logger.

    Args:
        name (str): The name of the logger.
        log_file (str): The file to save logs to.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)

    if logger.hasHandlers():
        return logger

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Default logger instance for easy import
workflow_logger = setup_logger()
