from __future__ import annotations

import logging
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_FILE = LOG_DIR / "nexus.log"


# ============================================================
# FORMAT
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = (
    "%Y-%m-%d %H:%M:%S"
)


# ============================================================
# LOGGER SETUP
# ============================================================

def get_logger(
    name: str = "nexus",
) -> logging.Logger:

    logger = logging.getLogger(
        name
    )

    logger.setLevel(
        logging.INFO
    )

    logger.propagate = False

    # Avoid duplicate handlers when
    # Streamlit reloads the application.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # --------------------------------------------------------
    # File handler
    # --------------------------------------------------------

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setLevel(
        logging.INFO
    )

    file_handler.setFormatter(
        formatter
    )

    # --------------------------------------------------------
    # Console handler
    # --------------------------------------------------------

    console_handler = logging.StreamHandler(
        sys.stdout
    )

    console_handler.setLevel(
        logging.INFO
    )

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    logger.addHandler(
        console_handler
    )

    return logger


# ============================================================
# APPLICATION LOGGER
# ============================================================

logger = get_logger(
    "nexus"
)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def log_info(
    message: str,
) -> None:

    logger.info(
        message
    )


def log_warning(
    message: str,
) -> None:

    logger.warning(
        message
    )


def log_error(
    message: str,
) -> None:

    logger.error(
        message
    )


def log_exception(
    message: str,
) -> None:

    logger.exception(
        message
    )