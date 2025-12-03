import json
import logging
from typing import Tuple, Optional, List

import streamlit as st
from modules.utils import openai_call, load_prompt, build_prompt
from modules.config import (
    USE_MOCK_API,
    ACTIVE_QUESTION_TECHNIQUE,
    ACTIVE_SUMMARY_TECHNIQUE,
    SYSTEM_PROMPTS,
    BASE_PROMPTS,
    PERSONA_MAP
)

logger = logging.getLogger(__name__)

# --- MOCK API DATA FOR LOCAL TESTING ---
mock_questions = [
    "Mock Q1: Tell me about yourself.",
    "Mock Q2: Why do you want this job?",
    "Mock Q3: Describe a challenge you faced at work.",
    "Mock Q4: How do you handle stress?"
]

mock_feedback = [
    "Mock Feedback: Good answer! Try to be more concise.",
    "Mock Feedback: Solid response. Could give more examples.",
    "Mock Feedback: Excellent! Well-structured answer.",
    "Mock Feedback: Nice! Consider elaborating on impact."
]


# =====================================================================
# CORE SESSION MANAGEMENT
# =====================================================================

def restart_interview() -> None:
    """
    Reset all interview-related state while keeping the user
    in interview mode.

    Notes:
        - Job title, difficulty, and question type remain unchanged.
        - Sidebar clarification state is reset as well.
    """
    logger.info("Restarting interview: clearing questions, answers, and feedbacks.")

    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.current_question_index = 0
    st.session_state.input_tokens_total = 0
    st.session_state.output_tokens_total = 0
    st.session_state.cost_so_far = 0.0

    st.session_state.sidebar_needs_clarification = False
    st.session_state.sidebar_clarification_message = ""
    st.session_state.pending_sidebar_job_title = ""

    logger.debug("Session after restart: %s", {
        "questions": st.session_state.questions,
        "answers": st.session_state.answers,
        "feedbacks": st.session_state.feedbacks
    })


def initialize_interview_session(job_title: str, question_type: str, difficulty: str) -> None:
    """
    Initialize a fresh interview session in Streamlit's session state.

    Args:
        job_title: Position being interviewed for.
        question_type: Behavioral, Technical, or Role-specific.
        difficulty: Selected difficulty level.
    """
    logger.info(
        "Initializing interview session | job_title=%s | type=%s | difficulty=%s",
        job_title, question_type, difficulty
    )

    st.session_state.started = True
    st.session_state.job_title = job_title
    st.session_state.question_type = question_type
    st.session_state.difficulty = difficulty

    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.current_question_index = 0


# =====================================================================
# EVALUATION LOGIC
# =====================================================================

def evaluate_answer_and_generate_next(user_answer: str) -> Tuple[str, Optional[str]]:
    """
    Evaluate the user's answer using the selected persona and optionally
    generate the next question.

    Args:
        user_answer: The user's free-form text answer.

    Returns:
        (feedback, next_question)
        - feedback: The evaluation of the answer.
        - next_question: Generated follow-up question or None.
    """
    logger.info("Evaluating user answer for question index %s", st.session_state.current_question_index)

    # --- MOCK MODE ---
    if USE_MOCK_API:
        logger.debug("Using mock feedback and question.")
        return "Mock feedback: good answer.", "Mock next question."

    index = st.session_state.current_question_index
    sys_instructions = load_prompt(SYSTEM_PROMPTS["answer_evaluator"])

    selected_persona = st.session_state.evaluation_style
    persona_template = PERSONA_MAP.get(selected_persona, "Hiring Manager")

    prompt_text = build_prompt(
        category="evaluation",
        base_instructions=BASE_PROMPTS["evaluation"],
        technique=persona_template,
        job_title=st.session_state.job_title,
        question=st.session_state.questions[index],
        answer=user_answer,
        previous_answers=st.session_state.answers[: index + 1],
        previous_questions=st.session_state.questions,
        difficulty=st.session_state.difficulty,
        question_type=st.session_state.question_type,
    )

    logger.debug("Built evaluation prompt.")
    logger.debug("Evaluation prompt content: %s", prompt_text)

    response_format = {
        "format": {
            "type": "json_schema",
            "name": "evaluation_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "feedback": {"type": "string"},
                    "next_question": {"type": ["string", "null"]},
                },
                "required": ["feedback", "next_question"],
                "additionalProperties": False,
            },
        }
    }

    raw_response = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
        structured_output=response_format,
    )

    logger.debug("Raw evaluation response: %s", raw_response)

    try:
        data = json.loads(raw_response)
        feedback = data.get("feedback", "No feedback returned.")
        next_question = data.get("next_question") or None
    except Exception as e:
        logger.error("Failed to parse evaluation JSON: %s", e, exc_info=True)
        feedback = "Error parsing model response."
        next_question = None

    # Fallback to ensure continuity
    if not next_question:
        logger.info("Model did not provide next question — generating manually.")
        next_question = generate_next_question()

    return feedback, next_question


# =====================================================================
# QUESTION GENERATION
# =====================================================================

def generate_next_question() -> str:
    """
    Generate the next interview question using the configured prompt technique.

    Returns:
        The generated question as a string.
    """
    try:
        # --- MOCK MODE ---
        if USE_MOCK_API:
            index = len(st.session_state.questions)
            return mock_questions[index % len(mock_questions)]

        # --- Load system instructions ---
        sys_instructions = load_prompt(SYSTEM_PROMPTS["question_generator"])

        # --- Build full prompt ---
        prompt_content = build_prompt(
            category="questions",
            base_instructions=BASE_PROMPTS["question"],
            technique=ACTIVE_QUESTION_TECHNIQUE,
            job_title=st.session_state.job_title,
            question_type=st.session_state.question_type,
            difficulty=st.session_state.difficulty,
            previous_answers=st.session_state.answers,
            previous_questions=st.session_state.questions,
        )
        prompt_text = f"MODE: generate_question\n{prompt_content}"

        if not prompt_text:
            logger.error("Failed to build question prompt")
            return "Could not generate question. Please try again."

        # --- Structured output for consistent parsing ---
        structured_output = {
            "format": {
                "type": "json_schema",
                "name": "question_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"question": {"type": "string", "minLength": 1}},
                    "required": ["question"],
                    "additionalProperties": False,
                },
            }
        }

        # --- Call the model ---
        response = openai_call(
            sys_instructions=sys_instructions,
            prompt_text=prompt_text,
            structured_output=structured_output,
        )

        # --- Parse JSON safely ---
        if response:
            try:
                data = json.loads(response)
                return data.get("question", "Could not generate question. Please try again.")
            except Exception as e:
                logger.error(f"Failed to parse question JSON: {e}")
                return response

        return "Could not generate question. Please try again."

    except Exception as e:
        logger.error(f"Error in generate_next_question: {e}")
        return "Could not generate question. Please try again."


# =====================================================================
# SUMMARY GENERATION
# =====================================================================

def generate_interview_summary() -> str:
    """
    Generate a summary of the user's interview performance based on all
    questions and answers.

    Returns:
        A plain-text or JSON-formatted summary depending on prompt design.
    """
    logger.info("Generating interview summary.")

    if USE_MOCK_API:
        return "Mock summary: User performed well overall, needs improvement in problem-solving."

    sys_instructions = load_prompt(SYSTEM_PROMPTS["summary_generator"])

    questions_and_answers = list(zip(st.session_state.questions, st.session_state.answers))

    prompt_text = build_prompt(
        category="summary",
        base_instructions=BASE_PROMPTS["summary"],
        technique=ACTIVE_SUMMARY_TECHNIQUE,
        questions_and_answers=questions_and_answers,
    )

    logger.debug("Summary prompt: %s", prompt_text)

    result = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
    )

    return result.strip()


def parse_summary(summary_text: str) -> Tuple[str, List[str]]:
    """
    Parse the JSON-formatted interview summary returned by the LLM.

    Args:
        summary_text: Raw model output.

    Returns:
        (summary, recommendations)
        - summary: plain text summary
        - recommendations: list of improvements
    """
    logger.info("Parsing interview summary.")

    try:
        data = json.loads(summary_text)
        summary = data.get("summary", "No summary provided.")
        recommendations = data.get("recommendations", [])

        if not isinstance(recommendations, list):
            recommendations = [str(recommendations)]

        return summary.strip(), [str(r).strip() for r in recommendations]

    except json.JSONDecodeError:
        logger.warning("Summary JSON decode failed — returning raw text.")
        return summary_text.strip(), []

    except Exception as e:
        logger.error("Unexpected error parsing summary: %s", e, exc_info=True)
        return "Summary could not be parsed.", []
