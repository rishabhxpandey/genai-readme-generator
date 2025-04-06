import logging
import sys

def setup_logging(log_level=logging.INFO, log_file="app.log"):
    """Configures logging for the application.

    Args:
        log_level: The minimum logging level to capture (e.g., logging.INFO, logging.DEBUG).
        log_file: The path to the log file.
    """
    # Create logger
    # Using __name__ for the logger is good practice if used within modules,
    # but for a central config, a fixed name might be better.
    # Let's use a root logger approach for simplicity here.
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Prevent multiple handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                datefmt='%Y-%m-%d %H:%M:%S')

    # Console Handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info(f"Logging configured. Level: {logging.getLevelName(log_level)}, File: {log_file}")

