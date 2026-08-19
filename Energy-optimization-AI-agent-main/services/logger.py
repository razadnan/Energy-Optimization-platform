"""
Logging Configuration
Energy Optimization Agent
"""

import logging
from pathlib import Path

from backend.config import config


def setup_logger(name: str = "EnergyOptimization") -> logging.Logger:
    """
    Create and configure a logger.
    """

    # Create logs directory if it doesn't exist
    Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File Handler
    file_handler = logging.FileHandler(
        config.LOG_DIR / "energy_agent.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger