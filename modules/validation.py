import streamlit as st
from modules.config import USE_MOCK_API, ACTIVE_VALIDATION_TECHNIQUE, SYSTEM_PROMPTS, BASE_PROMPTS
from typing import Tuple, Optional
from modules.utils import load_prompt, build_prompt, openai_call
from modules.error_handling import safe_execute
import logging

logger = logging.getLogger(__name__)

# --- MOCK API MODE ---
MOCK_CLARIFICATION_JOB_TITLES = ["Wizard of Light", "Dragon Tamer"]  # Example titles that need clarification
MOCK_MESSAGE = "Mock Clarification: This job title seems unusual. Please confirm."


def validate_job_title_exists(job_title: Optional[str]) -> bool:
    """
    Validates that the job title field is not empty.
    Sets `job_error` in session state if invalid.

    Args:
        job_title: The job title to validate (can be None)

    Returns:
        bool: True if valid, False if empty/None
    """
    if not job_title or not job_title.strip():
        st.session_state.job_error = "Job title is required. Please enter a valid job title."
        logger.info("Job title validation failed: empty or None")
        return False

    # Clear any previous error
    st.session_state.job_error = ""
    logger.debug(f"Job title '{job_title}' is valid")
    return True


def validate_job_title_with_clarification(job_title: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a job title using the LLM with a fail-safe prompt.
    Returns whether the job title is valid and optionally a clarification message.

    Args:
        job_title: Job title string to validate

    Returns:
        Tuple[bool, Optional[str]]:
            - bool: True if valid, False if clarification is needed
            - Optional[str]: Clarification message if needed, otherwise None
    """
    logger.info(f"Validating job title: '{job_title}'")

    # --- MOCK API for testing ---
    if USE_MOCK_API:
        if job_title.strip() in MOCK_CLARIFICATION_JOB_TITLES:
            logger.info(f"Mock clarification needed for job title: '{job_title}'")
            return False, MOCK_MESSAGE
        return True, None

    try:
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
        logger.debug(f"Final validation prompt length: {len(final_prompt)}")

        # --- Call OpenAI API using centralized error handler ---
        result = safe_execute(lambda: openai_call(sys_instructions, final_prompt), fallback="Validation failed. Please try again.")
        if not result:
            logger.warning(f"Validation API returned empty result for '{job_title}'")
            return False, "Validation failed. Please try again."

        # --- Determine if clarification is needed ---
        if "clarification needed" in result.lower():
            logger.info(f"Clarification required for job title '{job_title}': {result.strip()}")
            return False, result.strip()

        logger.debug(f"Job title '{job_title}' validated successfully")
        return True, None

    except Exception as e:
        logger.error(f"Unexpected error during job title validation: {e}", exc_info=True)
        return False, "Validation failed due to an internal error."
