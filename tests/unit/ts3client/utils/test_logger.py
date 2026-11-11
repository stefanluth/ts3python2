import logging

from ts3client.utils.logger import create_logger


def test_create_logger_reuses_the_existing_file_handler(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "test-logger-reuses-handler"
    logger = logging.getLogger(name)
    logger.handlers.clear()

    try:
        first = create_logger(name, "logs/main.log")
        second = create_logger(name, "logs/main.log")

        assert first is second
        assert len(second.handlers) == 1
        assert isinstance(second.handlers[0], logging.FileHandler)
    finally:
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
