import logging

def get_logger(name, level="INFO"):
    level = logging.getLevelName(level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    file_handler = logging.FileHandler('server_debug.log')
    file_handler.setLevel(level)

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)  # Set level to DEBUG for console output

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)  # Use the same formatter for the stream handler

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)  # Add the stream handler to the logger

    return logger

logger = get_logger(__name__, "DEBUG")