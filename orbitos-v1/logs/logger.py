#!/usr/bin/env python3
"""
This module contains a custom log formatter class that adds color
and custom formatting to log messages.
"""

import logging
import logging.config
from pathlib import Path
import os


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    colored = "[%(levelname)s|%(module)s|L%(lineno)d]"
    log_format = " %(asctime)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + colored + reset + log_format + reset,
        logging.INFO: blue + colored + reset + log_format + reset,
        logging.WARNING: yellow + colored + reset + log_format + reset,
        logging.ERROR: red + colored + log_format + reset,
        logging.CRITICAL: bold_red + colored + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging():

    working_directory = Path(__file__).parent
    path = working_directory / "logs.log"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setFormatter(CustomFormatter())
    console.setLevel(logging.INFO)

    file_logger = logging.FileHandler(path, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        fmt="[%(levelname)s|%(module)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_logger.setFormatter(formatter)
    file_logger.setLevel(logging.INFO)

    logger.addHandler(console)
    logger.addHandler(file_logger)

    # empty the logs file if it exists
    if os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            logger.info("Logs file cleared")
