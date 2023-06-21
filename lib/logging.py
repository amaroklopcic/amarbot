import logging

from discord.utils import setup_logging


class ColoredLogsFormatter(logging.Formatter):
    # NOTE: these color escape sequences are for UNIX-type environments, running on
    # Windows will produce some ugly logs
    bold = "\033[1m"
    reset = "\x1b[0m"

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"

    log_format = (
        "[%(levelname)s] %(asctime)s [%(name)s] %(message)s"
    )

    formatters = {
        logging.NOTSET: logging.Formatter(grey + log_format + reset),
        logging.DEBUG: logging.Formatter(grey + log_format + reset),
        logging.INFO: logging.Formatter(blue + log_format + reset),
        logging.WARNING: logging.Formatter(yellow + log_format + reset),
        logging.ERROR: logging.Formatter(red + log_format + reset),
        logging.CRITICAL: logging.Formatter(bold + red + log_format + reset),
    }

    def format(self, record):
        log_formatter = self.formatters.get(record.levelno)
        return log_formatter.format(record)


def get_logger(name: str, log_level: int = logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(ColoredLogsFormatter())

    logger.addHandler(stream_handler)

    return logger


def setup_discord_logging():
    setup_logging(
        handler=logging.StreamHandler(),
        formatter=ColoredLogsFormatter(),
        level=logging.INFO,
        root=False,
    )
