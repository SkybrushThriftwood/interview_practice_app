import streamlit as st

def initialize_session_state():
    """Initialize all required session state variables with defaults."""

    defaults = {
        "started": False,
        "job_title": "",
        "question_type": "Behavioral",
        "difficulty": "Easy",
        "questions": [],
        "answers": [],
        "current_question_index": 0,
        "job_error": "",
        "feedbacks": [],

        # Welcome screen clarification
        "needs_clarification": False,
        "pending_job_title": "",
        "pending_question_type": "",
        "pending_difficulty": "",

        # Sidebar clarification (for restart)
        "sidebar_needs_clarification": False,
        "sidebar_clarification_message": "",
        "pending_sidebar_job_title": "",
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)