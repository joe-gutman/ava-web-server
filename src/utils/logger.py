import os
import logging

class PathnameFilter(logging.Filter):
    def filter(self, record):
        pathname = record.pathname
        record.folder = os.path.basename(os.path.dirname(pathname))
        return True

def get_logger(name, file_log_level="INFO", terminal_log_level="INFO"):
    file_log_level = logging.getLevelName(file_log_level.upper())
    terminal_log_level = logging.getLevelName(terminal_log_level.upper())

    if not isinstance(file_log_level, int):
        file_log_level = logging.INFO
    if not isinstance(terminal_log_level, int):
        terminal_log_level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(min(file_log_level, terminal_log_level))  # Set to the lower of the two log levels

    # Update the log file path to match your directory structure
    log_directory = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file_path = os.path.join(log_directory, 'server_debug.log')

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(file_log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(terminal_log_level)

    pathname_filter = PathnameFilter()
    file_handler.addFilter(pathname_filter)
    stream_handler.addFilter(pathname_filter)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(folder)s/%(filename)s:%(lineno)d - %(message)s')
    
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

logger = get_logger(__name__, "DEBUG", "INFO")
