import logging


class ThreadLogger(logging.Handler):
    """Custom logger that emits all logging messages as QT signals"""

    def __init__(self, signal):
        super().__init__()

        self.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.signal = signal

    def emit(self, msg):
        self.signal.emit(self.format(msg))


def set_logger_handler(name, signal, level=logging.INFO):
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger_handler = ThreadLogger(signal)
    logger.addHandler(logger_handler)
    logger.setLevel(level)

    return logger
