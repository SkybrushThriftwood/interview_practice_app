import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    """Initialize logging for the entire app, safe for Streamlit reruns."""

    # Prevent duplicate handlers on rerun
    if logging.getLogger().handlers:
        return

    # ---------- Format ----------
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(funcName)s:%(lineno)d): %(message)s"
    )

    # ---------- Handlers ----------
    debug_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app_debug.log"),
        maxBytes=1_000_000,
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    info_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app_info.log"),
        maxBytes=1_000_000,
        backupCount=3
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app_error.log"),
        maxBytes=1_000_000,
        backupCount=3
    )
    error_handler.setLevel(logging.WARNING)  # WARNING, ERROR, CRITICAL
    error_handler.setFormatter(formatter)

    # Console for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ---------- Root logger ----------
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # master switch

    root.addHandler(debug_handler)
    root.addHandler(info_handler)
    root.addHandler(error_handler)
    root.addHandler(console_handler)

    logging.info("Logging initialized.")