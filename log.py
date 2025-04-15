
import logging
import os
import sys

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AppLog.log")
_logger = None

def setup_logger(module_name):
    global _logger
    _logger = logging.getLogger(module_name)
    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False
    _logger.handlers.clear()

    formatter = logging.Formatter('[%(asctime)s] %(name)s | %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    _logger.addHandler(stream_handler)

def log(message):
    if _logger:
        _logger.info(message)
        for handler in _logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
