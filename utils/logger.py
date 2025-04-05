import logging

def create_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    formatter = logging.Formatter(f"%(asctime)s :: %(levelname)s :: {name} :: %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
