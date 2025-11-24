import streamlit as st
from typing import Tuple, Optional
from .utils import get_prompt, openai_call
from modules.config import USE_MOCK_API

# --- MOCK API MODE ---
MOCK_CLARIFICATION_JOB_TITLES = ["Wizard of Light", "Dragon Tamer"]  # Example titles that need clarification
MOCK_MESSAGE = "Mock Clarification: This job title seems unusual. Please confirm."


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
    
    Args:
        job_title (str): The job title entered by the user.
    
    Returns:
        Tuple[bool, Optional[str]]:
            - True, None if the title is valid.
            - False, message if clarification is needed.
    """
    # mock API for testing
    if USE_MOCK_API:
        # Return False with a mock message if the title is in mock list
        if job_title.strip() in MOCK_CLARIFICATION_JOB_TITLES:
            return False, MOCK_MESSAGE
        # Otherwise, return True (title accepted)
        return True, None

    # Load instructions and the validation prompt
    instructions = get_prompt(
        "validation_prompts.j2",
        macro_name="validation_instructions"
    )
    
    prompt = get_prompt(
        "validation_prompts.j2",
        macro_name="validate_job_title",
        job_title=job_title
    )
    
    # Call the LLM
    result = openai_call(
        instructions=instructions,
        user_input=prompt,
        temperature=0.7
    )
    
    # Determine if clarification is needed
    if result and "clarification" in result.lower():
        # Return False and the message if the LLM asks for clarification
        return False, result.strip()
    
    # Otherwise, return True and no message
    return True, None
    