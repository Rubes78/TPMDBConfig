import logging
import os
import sys

def setup_logger(module_name="App"):
    logger = logging.getLogger(module_name)

    if getattr(logger, "_custom_setup_done", False):
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(name)s | %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AppLog.log")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger._custom_setup_done = True
    return logger

# Default logger instance using the name of the main running script
logger = setup_logger(os.path.splitext(os.path.basename(sys.argv[0]))[0])

def log(message, level="info"):
    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
    else:
        logger.info(message)