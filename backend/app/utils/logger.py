import logging
import sys

# Configure the logging format
# Format: [Time] [Level] [Module]: Message
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a standardized logger instance.
    """
    logger = logging.getLogger(name)

    # Only add handler if not already added (prevents duplicate logs)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set default level (INFO for production, DEBUG for dev)
        logger.setLevel(logging.INFO)

    return logger
