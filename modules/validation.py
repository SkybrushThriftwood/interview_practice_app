import streamlit as st
import logging
from typing import Tuple
from .utils import build_prompt, openai_call, load_prompt
from modules.config import USE_MOCK_API


# --- MOCK API MODE ---
MOCK_CLARIFICATION_JOB_TITLES = ["Wizard of Light", "Dragon Tamer"]  # Example titles that need clarification
MOCK_MESSAGE = "Mock Clarification: This job title seems unusual. Please confirm."

# --- setup logging ---
logger = logging.getLogger(__name__)

def validate_job_title_exists(job_title: str | None) -> bool:
    """
    Validates that the job title field is not empty.
    Sets job_error in session state if invalid.
    
    Args:
        job_title: The job title to validate (can be None)
        
    Returns:
        bool: True if valid, False if empty/None
    """
    if not job_title or not job_title.strip():
        st.session_state.job_error = "Job title is required. Please enter a valid job title."
        return False
    
    # Clear any previous error
    st.session_state.job_error = ""
    return True

def validate_job_title_with_clarification(job_title: str) -> Tuple[bool, str | None]:
    """
    Validates a job title using the LLM with a fail-safe prompt.
    
    Args:
        job_title (str): The job title entered by the user.
    
    Returns:
        Tuple[bool, Optional[str]]:
            - True, None if the title is valid.
            - False, message if clarification is needed.
    """
    # --- MOCK API for testing ---
    if USE_MOCK_API:
        if job_title.strip() in MOCK_CLARIFICATION_JOB_TITLES:
            return False, MOCK_MESSAGE
        return True, None

    # --- Load system instructions ---
    sys_instructions = load_prompt("system/job_title_validator.j2")

    # --- Build developer/user prompt dynamically ---
    prompt_text = build_prompt(
        category="validation",
        technique="default",  # Could be extended to different techniques later
        job_title=job_title
    )

    if not prompt_text:
        logger.error("Failed to build validation prompt")
        return False, "Could not generate validation prompt."

    # --- Call OpenAI API ---
    result = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
        temperature=0.7
    )

    # --- Determine if clarification is needed ---
    if result and "clarification" in result.lower():
        return False, result.strip()

    return True, None
    