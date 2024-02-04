import logging

def get_logger(name, level="INFO"):
    level = logging.getLevelName(level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler('app.log')
    handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

logger = get_logger(__name__, "DEBUG")