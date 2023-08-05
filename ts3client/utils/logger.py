import logging

from config import LOGGING_LEVEL


def create_logger(name: str, file: str, level: int = LOGGING_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str):
    return logging.getLogger(name)
