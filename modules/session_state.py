import streamlit as st
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def initialize_session_state() -> None:
    """
    Initialize all required Streamlit session state variables with default values.
    
    This ensures the app has all necessary keys in `st.session_state` before
    any user interaction begins.
    
    Defaults include:
        - Interview state: started, job_title, question_type, difficulty
        - Questions, answers, feedback tracking
        - Sidebar and welcome screen clarification flags
    """
    defaults: Dict[str, Any] = {
        # Core interview state
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

        # Advanced OpenAI defaults
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens_eval": 250,
        "max_tokens_question_and_summary": 800,


        # --- Token usage / cost tracking ---
        "input_tokens_total": 0,
        "output_tokens_total": 0,
        "cost_so_far": 0.0,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    
    logger.info("Session state initialized with default values.")


def get_openai_settings() -> dict:
    """Return OpenAI parameters from session_state (with defaults)."""
    return {
        "model": st.session_state.get("model", "gpt-4o-mini"),
        "temperature": st.session_state.get("temperature", 0.2),
        "max_tokens_eval": st.session_state.get("max_tokens_eval", 250),
    }