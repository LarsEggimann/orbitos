"""
This module contains a custom log formatter class that adds color
and custom formatting to log messages.
"""

import logging
from rich.logging import RichHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)-120s [%(processName)s:%(process)s %(threadName)s:%(thread)s]",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                level=logging.INFO,
                rich_tracebacks=True
                )
            ]
    )

    # ensure other loggers DO NOT propagate messages if handled by root
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()  # remove their handlers
        logger.propagate = True  # let root handle them
