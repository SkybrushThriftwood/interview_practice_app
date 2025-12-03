"""
ui_sidebar.py

Streamlit sidebar for interview settings:
- Job title input, question type, difficulty
- Handles restart flows and job title clarifications
"""

import streamlit as st
from typing import Tuple
from modules.interview_logic import initialize_interview_session, generate_next_question, restart_interview
from modules.validation import validate_job_title_exists, validate_job_title_with_clarification
from modules.ui.ui_helpers import advanced_settings_ui
import logging

logger = logging.getLogger(__name__)


def display_sidebar() -> Tuple[str, str, str, bool]:
    """
    Displays the sidebar with interview settings.
    Handles job title clarification within the sidebar for restart flow.

    Returns:
        Tuple[str, str, str, bool]: (pending_job_title, pending_question_type, pending_difficulty, should_restart)
    """
    st.sidebar.header("Interview Settings")

    # --- Clarification mode (after failed restart) ---
    if st.session_state.get('sidebar_needs_clarification', False):
        st.sidebar.warning("Please clarify the job title:")
        st.sidebar.markdown(
            st.session_state.get('sidebar_clarification_message', ''),
            help="The job title wasn't clear. Please provide a more specific title."
        )

        clarify_input = st.sidebar.text_input(
            "Clarify Job Title",
            value=st.session_state.get('pending_sidebar_job_title', ''),
            key="sidebar_clarification_input"
        )
        new_job_title = clarify_input or ""

        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("Restart", key="sidebar_clarify_restart"):
                if new_job_title.strip():
                    st.session_state.sidebar_needs_clarification = False
                    st.session_state.sidebar_clarification_message = ""
                    # Update live session state
                    st.session_state.job_title = new_job_title.strip()
                    st.session_state.questions = []
                    st.session_state.answers = []
                    st.session_state.feedbacks = []
                    st.session_state.current_question_index = 0
                    st.session_state.question_type = st.session_state.pending_question_type
                    st.session_state.difficulty = st.session_state.pending_difficulty

                    initialize_interview_session(
                        st.session_state.job_title,
                        st.session_state.question_type,
                        st.session_state.difficulty
                    )
                    st.session_state.questions.append(generate_next_question())
                    st.rerun()
                else:
                    st.sidebar.error("Please enter a job title.")

        with col2:
            if st.button("Cancel", key="sidebar_cancel_clarify"):
                st.session_state.sidebar_needs_clarification = False
                st.session_state.sidebar_clarification_message = ""
                st.rerun()

        return (
            st.session_state.get('pending_sidebar_job_title', st.session_state.get('job_title', '')),
            st.session_state.get('pending_question_type', st.session_state.get('question_type', 'Behavioral')),
            st.session_state.get('pending_difficulty', st.session_state.get('difficulty', 'Easy')),
            False
        )

    # --- Normal sidebar display ---
    job_title_input = st.sidebar.text_input(
        "Job Title",
        value=st.session_state.get('pending_job_title', st.session_state.get('job_title', '')),
        key="sidebar_job_title_input", placeholder="e.g. Software Engineer"
    )
    st.session_state.pending_job_title = job_title_input or ""

    question_types = ["Behavioral", "Role-specific", "Technical"]
    current_question_type = st.session_state.get('pending_question_type', st.session_state.get('question_type', 'Behavioral'))
    if current_question_type not in question_types:
        current_question_type = "Behavioral"

    selected_type = st.sidebar.selectbox(
        "Question Type",
        question_types,
        index=question_types.index(current_question_type),
        key="sidebar_question_type_input"
    )
    st.session_state.pending_question_type = selected_type

    difficulties = ["Easy", "Medium", "Hard"]
    current_difficulty = st.session_state.get('pending_difficulty', st.session_state.get('difficulty', 'Easy'))
    if current_difficulty not in difficulties:
        current_difficulty = "Easy"

    selected_difficulty = st.sidebar.selectbox(
        "Difficulty Level",
        difficulties,
        index=difficulties.index(current_difficulty),
        key="sidebar_difficulty_input"
    )
    st.session_state.pending_difficulty = selected_difficulty
    
    advanced_settings_ui(use_sidebar=True)


    st.sidebar.markdown("---")

    should_restart = st.sidebar.button("Restart Interview", key="restart_button")

    return (
        st.session_state.pending_job_title,
        st.session_state.pending_question_type,
        st.session_state.pending_difficulty,
        should_restart
    )


def handle_sidebar_restart() -> None:
    """
    Updates live session state and starts a new interview
    based on pending sidebar values. Called when Restart button is pressed.
    """
    job_title = st.session_state.pending_job_title

    if not validate_job_title_exists(job_title):
        st.sidebar.error(st.session_state.job_error)
        return

    logger.info(f"User requesting restart with job_title={job_title}")
    valid, message = validate_job_title_with_clarification(job_title)

    if valid:
        st.session_state.job_title = job_title
        st.session_state.question_type = st.session_state.pending_question_type
        st.session_state.difficulty = st.session_state.pending_difficulty

        restart_interview()
        initialize_interview_session(
            st.session_state.job_title,
            st.session_state.question_type,
            st.session_state.difficulty
        )
        st.rerun()
    else:
        st.session_state.sidebar_needs_clarification = True
        st.session_state.sidebar_clarification_message = message
        st.session_state.pending_sidebar_job_title = job_title
        logger.info(f"Job title needs clarification: {message}")
        st.rerun()
