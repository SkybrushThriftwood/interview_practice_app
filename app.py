"""
app.py

Main entry point for the Interview Practice App.
Controls app initialization, session state, and routing
between the welcome screen and the interview interface.
"""

import logging
import streamlit as st
from modules.session_state import initialize_session_state
from modules.ui.ui_start_screen import render_main_screen
from modules.ui.ui_interview import render_interview_ui
from modules.logging_config import setup_logging


def main() -> None:
    """
    Main application loop.

    Initializes logging and session state, then routes
    the user to either the welcome screen or interview mode
    based on session state.
    """
    # Initialize logging (only once)
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Interview Practice App")

    # Initialize Streamlit session state with defaults
    initialize_session_state()
    logger.debug("Session state initialized with default values")

    # ------------------- Main Screen (Welcome) -------------------
    if not st.session_state.started:
        logger.info("Rendering welcome screen")
        render_main_screen()
        return

    # ------------------- Interview Mode -------------------
    else:
        logger.info(
            f"Entering interview mode for job_title={st.session_state.get('job_title')}, "
            f"question_type={st.session_state.get('question_type')}, "
            f"difficulty={st.session_state.get('difficulty')}"
        )
        render_interview_ui()


if __name__ == "__main__":
    main()