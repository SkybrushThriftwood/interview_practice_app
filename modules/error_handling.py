"""
error_handling.py

Provides decorators and utility functions for centralized error handling.
Ensures that errors are logged and displayed in a consistent, user-friendly way.
"""


import logging
import streamlit as st
from functools import wraps

from modules.errors import AppError


logger = logging.getLogger(__name__)


def handle_app_errors(func):
    """
    Decorator for UI-layer functions.

    Wraps a function so that:
    - Known AppError exceptions show a friendly message to the user.
    - Unknown exceptions log a full stack trace and show a generic error.
    - The Streamlit app does not crash.

    Recommended usage:
        @handle_app_errors
        def render_interview_ui():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except AppError as exc:
            # Expected & controlled errors
            logger.exception(f"Handled application error: {exc}")
            st.error(exc.user_message)

        except Exception as exc:
            # Unexpected, uncontrolled errors
            logger.exception(f"Unhandled exception in UI: {exc}")
            st.error("An unexpected error occurred. Please restart the interview.")

    return wrapper


def safe_execute(operation, fallback=None, reraise=False):
    """
    Helper for executing risky operations in logic-layer code
    (API calls, template rendering, parsing, etc.)

    Args:
        operation (callable): The function to execute.
        fallback: Value to return if an exception occurs.
        reraise (bool): If True, re-raises the caught exception as AppError.

    Returns:
        Any: Result of operation or fallback value.

    Example:
        result = safe_execute(lambda: model.generate(prompt), fallback=None, reraise=True)
    """

    try:
        return operation()

    except AppError as exc:
        logger.exception(f"Handled error in logic layer: {exc}")
        if reraise:
            raise
        return fallback

    except Exception as exc:
        logger.exception("Unhandled error in logic layer")
        if reraise:
            raise AppError("Unexpected internal error.") from exc
        return fallback
