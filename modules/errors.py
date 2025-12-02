"""
errors.py

Defines a hierarchy of custom exceptions used throughout the Interview Practice App.
These exceptions carry both developer-facing information (exception text)
and user-facing messages that can be displayed safely in the UI.
"""


class AppError(Exception):
    """
    Base class for all application-specific errors.

    Attributes:
        user_message (str): A safe, user-friendly error message that can be shown in the UI.
    """
    user_message: str = "An unexpected application error occurred."


class ValidationError(AppError):
    """
    Raised when user inputs are missing, malformed, or fail validation logic.
    """
    user_message = "Some input seems invalid. Please correct it and try again."


class SessionStateError(AppError):
    """
    Raised when Streamlit session_state is missing required fields or is inconsistent.
    """
    user_message = (
        "Your session became invalid. The interview will restart to recover."
    )


class LLMError(AppError):
    """
    Raised when communication with the LLM fails or a response cannot be parsed.
    """
    user_message = (
        "I ran into a problem generating a response. Please try again."
    )


class TemplateError(AppError):
    """
    Raised when a Jinja template cannot render or is missing variables.
    """
    user_message = (
        "There was an issue preparing the interview prompt. Please restart the interview."
    )


class ParsingError(AppError):
    """
    Raised when JSON or structured content returned by the LLM cannot be parsed.
    """
    user_message = (
        "I could not understand the model's response. Please answer again or restart."
    )
