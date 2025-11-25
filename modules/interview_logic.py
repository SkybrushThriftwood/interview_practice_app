import streamlit as st
import json
from modules.utils import openai_call, load_prompt, handle_errors, build_prompt
from modules.config import USE_MOCK_API, ACTIVE_QUESTION_TECHNIQUE
from typing import Tuple, Optional
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
    Generates the next interview question using the selected prompt technique.
    """
    # Mock mode (unchanged)
    if USE_MOCK_API:
        index = len(st.session_state.questions)
        return mock_questions[index % len(mock_questions)]

    # Load system instructions (static)
    sys_instructions = load_prompt("system/question_generator.j2")


   # Build the full prompt (instructions + technique content)
    prompt_content = build_prompt(
        category="question",
        technique=ACTIVE_QUESTION_TECHNIQUE,
        job_title=st.session_state.job_title,
        question_type=st.session_state.question_type,
        difficulty=st.session_state.difficulty,
        previous_answers=st.session_state.answers,
    )

    # Merge mode and content into a single string
    prompt_text = f"MODE: generate_question\n{prompt_content}"

    if not prompt_text:
        logger.error("Failed to build question prompt")
        return "Could not generate question. Please try again."

    # Call the model with separated system instructions + developer/user prompt
    question_text = openai_call(sys_instructions=sys_instructions,
        prompt_text=prompt_text)

    return question_text

def evaluate_answer_and_generate_next(user_answer: str) -> Tuple[str, Optional[str]]:
    """
    Evaluates the user's answer and generates the next question using the OpenAI API.

    Args:
        user_answer (str): The answer provided by the user to the current question.

    Returns:
        Tuple[str, str]: feedback and next question
    """
    # Mock API for testing
    if USE_MOCK_API:
        index = len(st.session_state.answers)
        feedback = mock_feedback[index % len(mock_feedback)]
        next_question = generate_next_question()
        return feedback, next_question

    # Append the user answer to session state
    st.session_state.answers.append(user_answer)
    index = st.session_state.current_question_index

    if "feedback_cache" not in st.session_state:
        st.session_state.feedback_cache = {}

    if index not in st.session_state.feedback_cache:
        st.session_state.feedback_cache[index] = {}

    selected_persona = st.session_state["evaluation_style"]

    # Check cache first
    if selected_persona in st.session_state.feedback_cache[index]:
        feedback = st.session_state.feedback_cache[index][selected_persona]
    else:
    # Build prompt (base + persona technique)
        persona_map = {
            "Hiring Manager": "personality_hiring_manager.j2",
            "HR Professional": "personality_hr.j2",
            "Ideal Candidate": "personality_ideal_candidate.j2",
            "Mentor": "personality_mentor.j2",
            "Subject Matter Expert": "personality_sme.j2",
        }

        prompt_text = build_prompt(
            category="evaluation",
            technique=persona_map[selected_persona],
            job_title=st.session_state.job_title,
            question=st.session_state.questions[index],
            answer=user_answer,
            previous_answers=st.session_state.answers[:index+1]
        )

        sys_instructions = load_prompt("system/answer_evaluator.j2")

        feedback, _ = parse_feedback_and_next(
            openai_call(sys_instructions=sys_instructions, prompt_text=prompt_text)
        )

        # Cache the result
        st.session_state.feedback_cache[index][selected_persona] = feedback

    # Generate next question only if it's the last submitted answer
    next_question = None
    if index == len(st.session_state.questions) - 1:
        next_question = generate_next_question()

    return feedback, next_question

def parse_feedback_and_next(result_text: str) -> tuple[str, str]:
    """
    Parses the LLM response into feedback and the next question.
    Expected format: "FEEDBACK: ... NEXT_QUESTION: ..."

    Returns:
        Tuple[str, str]: feedback, next question
    """
    feedback_marker = "FEEDBACK:"
    question_marker = "NEXT_QUESTION:"
    try:
        feedback = result_text.split(feedback_marker)[1].split(question_marker)[0].strip()
        next_question = result_text.split(question_marker)[1].strip()
        return feedback, next_question
    except Exception:
        # Fallback if parsing fails
        return "Feedback could not be parsed.", result_text

def generate_interview_summary() -> str:
    """
    Summarizes the user's performance across all answered questions.
    
    Returns:
        str: A summary highlighting strengths, weaknesses, and actionable suggestions.
    """
    # --- MOCK API for testing ---
    if USE_MOCK_API:
        return "Mock summary: User performed well overall, needs improvement in problem-solving."

    # --- Load system instructions ---
    sys_instructions = load_prompt("system/summary_generator.j2")

    # --- Build developer/user prompt dynamically ---
    questions_and_answers = list(zip(
        st.session_state.questions,
        st.session_state.answers
    ))

    # Render prompt using base + technique
    prompt_text = build_prompt(
        category="summary",
        technique="default",
        questions_and_answers=questions_and_answers
    )

    if not prompt_text:
        logger.error("Failed to build summary prompt")
        return "Could not generate summary."

    # --- Call OpenAI API ---
    result = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
        temperature=0.5
    )

    return result.strip()

def parse_summary(summary_text: str) -> tuple[str, list[str]]:
    """
    Parses the JSON-formatted summary from the model output.

    Args:
        summary_text (str): Raw output from the LLM (expected JSON).

    Returns:
        Tuple[str, list[str]]: 
            - summary: overall summary string
            - recommendations: list of recommendation strings
    """
    try:
        # Attempt to parse JSON directly
        data = json.loads(summary_text)
        summary = data.get("summary", "No summary provided.")
        recommendations = data.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = [str(recommendations)]
        return summary.strip(), [str(r).strip() for r in recommendations]

    except json.JSONDecodeError:
        # Fallback if model output is not valid JSON
        logger.warning("Failed to parse JSON from summary. Returning raw text.")
        return summary_text.strip(), []

    except Exception as e:
        logger.error(f"Unexpected error parsing summary: {e}", exc_info=True)
        return "Summary could not be parsed.", []