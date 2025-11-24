import streamlit as st
from modules.utils import openai_call, get_prompt, handle_errors
from modules.config import USE_MOCK_API
from typing import Tuple
import logging
logger = logging.getLogger(__name__)

# --- MOCK API MODE ---
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

def start_interview():
    """Starts the interview by setting session state to 'started'."""
    st.session_state.started = True
    st.session_state.job_error = ""  # Reset error

def restart_interview():
    """
    Restarts the interview by resetting question/answer state.
    Keeps the user in interview mode (started=True).
    Does NOT reset job_title, question_type, or difficulty.
    """
    # Reset interview progress only
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.current_question_index = 0
    
    # Reset sidebar clarification state
    st.session_state.sidebar_needs_clarification = False
    st.session_state.sidebar_clarification_message = ""
    st.session_state.pending_sidebar_job_title = ""


def initialize_interview_session(job_title: str, question_type: str, difficulty: str) -> None:
    """
    Initializes the interview session in Streamlit's session state.
    
    Args:
        job_title (str): The job title for which the interview is conducted.
        question_type (str): Type of questions (Behavioral, Role-specific, Technical).
        difficulty (str): Difficulty level (Easy, Medium, Hard).
    """
    st.session_state.started = True
    st.session_state.job_title = job_title
    st.session_state.question_type = question_type
    st.session_state.difficulty = difficulty
    st.session_state.questions = []            # List of asked questions
    st.session_state.answers = []              # User answers
    st.session_state.current_question_index = 0  # Tracks which question is being displayed

@handle_errors(default=None)
def generate_next_question() -> str:
    """
    Generates the next interview question dynamically using the OpenAI API.

    Returns:
        str: The generated question text.
    """
    # mock API for testing
    if USE_MOCK_API:
        # Return next mock question based on how many questions we already have
        index = len(st.session_state.questions)
        return mock_questions[index % len(mock_questions)]
    
    # Render the prompt using Jinja2 template and macro
    prompt_text = get_prompt(
        "question_prompts.j2",
        macro_name="generate_question",
        job_title=st.session_state.job_title,
        question_type=st.session_state.question_type,
        difficulty=st.session_state.difficulty,
        previous_answers=st.session_state.answers
    )
    if not prompt_text:
        logger.error("Failed to render question prompt template")
        return "Could not generate question. Please try again."
    
    instructions = get_prompt("question_prompts.j2", macro_name="generate_question_instructions")
    
    question_text = openai_call(
        instructions=instructions,
        user_input=prompt_text
    )

    return question_text

def evaluate_answer_and_generate_next(user_answer: str) -> Tuple[str, str]:
    """
    Evaluates the user's answer and generates the next question using the OpenAI API.

    Args:
        user_answer (str): The answer provided by the user to the current question.

    Returns:
        Tuple[str, str]: A tuple containing:
            - feedback (str): Feedback for the user's answer.
            - next_question (str): The next interview question.
    """
    # mock API for testing
    if USE_MOCK_API:
        index = len(st.session_state.answers) - 1
        feedback = mock_feedback[index % len(mock_feedback)]
        next_question = generate_next_question()
        return feedback, next_question


    # Append the user answer to session state
    st.session_state.answers.append(user_answer)

    # Render instructions and prompt using Jinja2
    instructions = get_prompt(
        "question_prompts.j2",
        macro_name="evaluate_answer_instructions"
    )
    prompt_text = get_prompt(
        "question_prompts.j2",
        macro_name="evaluate_answer",
        job_title=st.session_state.job_title,
        question=st.session_state.questions[-1],
        answer=user_answer,
        previous_answers=st.session_state.answers
    )

    # Call OpenAI API
    result = openai_call(
        instructions=instructions,
        user_input=prompt_text,
    )

    # Parse the feedback and next question
    feedback, next_question = parse_feedback_and_next(result)

    return feedback, next_question


def parse_feedback_and_next(result_text: str) -> Tuple[str, str]:
    """
    Parses the OpenAI response into feedback and the next question.
    Assumes the LLM response uses a structured format: "FEEDBACK: ... NEXT_QUESTION: ..."

    Args:
        result_text (str): The raw response text from the LLM.

    Returns:
        Tuple[str, str]: A tuple containing:
            - feedback (str): Feedback for the user's previous answer.
            - next_question (str): The next question to ask.
    """
    try:
        feedback_marker = "FEEDBACK:"
        question_marker = "NEXT_QUESTION:"
        feedback = result_text.split(feedback_marker)[1].split(question_marker)[0].strip()
        next_question = result_text.split(question_marker)[1].strip()
        return feedback, next_question
    except Exception:
        # Fallback if parsing fails
        return "Feedback could not be parsed.", result_text