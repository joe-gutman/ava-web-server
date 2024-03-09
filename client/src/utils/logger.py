import os
import logging

class PathnameFilter(logging.Filter):
    def filter(self, record):
        pathname = record.pathname
        record.folder = os.path.basename(os.path.dirname(pathname))
        return True

def get_logger(name, level="INFO"):
    level = logging.getLevelName(level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_handler = logging.FileHandler('logs/client_debug.log')
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    pathname_filter = PathnameFilter()
    file_handler.addFilter(pathname_filter)
    stream_handler.addFilter(pathname_filter)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(folder)s/%(filename)s:%(lineno)d - %(message)s')
    
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

logger = get_logger(__name__, "DEBUG")