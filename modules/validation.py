import streamlit as st
from modules.config import USE_MOCK_API, ACTIVE_VALIDATION_TECHNIQUE, SYSTEM_PROMPTS, BASE_PROMPTS
from typing import Tuple, Optional
from modules.utils import load_prompt, openai_call, build_prompt
import logging

logger = logging.getLogger(__name__)

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



def validate_job_title_with_clarification(job_title: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a job title using the LLM with a fail-safe prompt.
    """
    # --- MOCK API for testing ---
    if USE_MOCK_API:
        if job_title.strip() in MOCK_CLARIFICATION_JOB_TITLES:
            return False, MOCK_MESSAGE
        return True, None

    # --- Load system instructions ---
    sys_instructions = load_prompt(SYSTEM_PROMPTS["job_title_validator"])

    # --- Build full prompt using base + technique ---
    prompt_body = build_prompt(
        category="validation",
        base_instructions=BASE_PROMPTS["validation"],
        technique=ACTIVE_VALIDATION_TECHNIQUE,
        job_title=job_title
    )

    final_prompt = f"MODE: validate_job_title\n\n{prompt_body}".strip()

    # --- Call OpenAI API ---
    result = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=final_prompt,
    )

    if not result:
        return False, "Validation failed. Please try again."

    # --- Determine if clarification is needed ---
    if "clarification needed" in result.lower():
        return False, result.strip()

    return True, None
    