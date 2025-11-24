import streamlit as st
from modules.validation import validate_job_title_with_clarification, validate_job_title_exists
from modules.interview_logic import initialize_interview_session, generate_next_question
import logging

logger = logging.getLogger(__name__)


def render_main_screen():
    """Render the welcome screen UI and handle the start logic."""
    st.markdown(
        "<h1 style='text-align:center;'>Welcome to the Interview Practice App</h1>",
        unsafe_allow_html=True,
    )
    st.write("Practice interviews for different roles, question types, and difficulties.")

    # ---- Clarification Workflow ----
    if st.session_state.needs_clarification:
        _render_clarification_ui()
        return

    # ---- Normal Start Workflow ----
    _render_normal_start_ui()

def _render_normal_start_ui():
    from modules.ui.ui_helpers import (
        display_job_title_input,
        display_question_type_dropdown,
        display_difficulty_dropdown,
    )

    job_title = display_job_title_input()
    question_type = display_question_type_dropdown()
    difficulty = display_difficulty_dropdown()

    if st.button("Start Interview", key="main_start_button"):
        if not validate_job_title_exists(job_title):
            st.rerun()

        valid, message = validate_job_title_with_clarification(job_title)

        if valid:
            st.session_state.job_title = job_title
            st.session_state.question_type = question_type
            st.session_state.difficulty = difficulty

            initialize_interview_session(job_title, question_type, difficulty)
            st.session_state.started = True
            st.session_state.questions.append(generate_next_question())
            logger.info(f"Interview started for job_title={job_title}")
            st.rerun()
        else:
            st.session_state.needs_clarification = True
            st.session_state.job_error = message
            st.session_state.pending_job_title = job_title
            st.session_state.pending_question_type = question_type
            st.session_state.pending_difficulty = difficulty
            st.rerun()

def _render_clarification_ui():
    st.warning(
        f"We just want to make sure this job title is correct.\n\n"
        f"{st.session_state.job_error}\n"
        "Questions might be off if a very unusual job title is chosen."
    )

    new_job_title_input = st.text_input(
        "Clarify Job Title",
        value=st.session_state.pending_job_title,
        key="clarification_input",
    )
    new_job_title = new_job_title_input or ""

    if st.button("Start Interview with this Title", key="clarify_start_button"):
        if not validate_job_title_exists(new_job_title):
            st.error(st.session_state.job_error)
        else:
            st.session_state.job_title = new_job_title.strip()
            st.session_state.question_type = st.session_state.pending_question_type
            st.session_state.difficulty = st.session_state.pending_difficulty
            st.session_state.needs_clarification = False

            initialize_interview_session(
                st.session_state.job_title,
                st.session_state.question_type,
                st.session_state.difficulty,
            )
            st.session_state.started = True
            st.session_state.questions.append(generate_next_question())
            logger.info(f"Interview started after clarification: {st.session_state.job_title}")
            st.rerun()