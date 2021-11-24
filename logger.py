import logging
import inspect


def logger(filename: str, name: str) -> logging.Logger:
    """configure task logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(filename)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s: %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def ctx_message(message: str) -> str:
    """create an info message using the context function name
    """
    name = inspect.stack()[1][3]
    return f"fn: {name}, msg: '{message}'"
