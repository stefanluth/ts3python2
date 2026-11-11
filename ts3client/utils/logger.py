import logging
import os

from config import LOGGING_LEVEL, TS3_LOG_DIR


def log_path(filename: str) -> str:
    return os.path.join(TS3_LOG_DIR, filename)


def create_logger(name: str, file: str, level: int = LOGGING_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    target = os.path.abspath(file)
    has_handler = any(
        isinstance(handler, logging.FileHandler) and os.path.abspath(handler.baseFilename) == target
        for handler in logger.handlers
    )

    if not has_handler:
        directory = os.path.dirname(target)
        if directory:
            os.makedirs(directory, exist_ok=True)
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str):
    return logging.getLogger(name)
