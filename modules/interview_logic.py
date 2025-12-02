import streamlit as st
import json
from modules.utils import openai_call, load_prompt, handle_errors, build_prompt
from modules.config import (
    USE_MOCK_API, 
    ACTIVE_QUESTION_TECHNIQUE, 
    ACTIVE_SUMMARY_TECHNIQUE,
    SYSTEM_PROMPTS, 
    BASE_PROMPTS, 
    PERSONA_MAP
)
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

def restart_interview():
    """
    Restarts the interview by resetting question/answer state.
    Keeps the user in interview mode (started=True).
    Does NOT reset job_title, question_type, or difficulty.
    """
    # Reset interview progress only
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.current_question_index = 0
    
    # Reset sidebar clarification state
    st.session_state.sidebar_needs_clarification = False
    st.session_state.sidebar_clarification_message = ""
    st.session_state.pending_sidebar_job_title = ""
    
    logger.info(f"Clearing feedbacks: {st.session_state.get('feedbacks')}")

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
    st.session_state.questions = []            
    st.session_state.answers = []              
    st.session_state.current_question_index = 0  

def evaluate_answer_and_generate_next(user_answer: str) -> Tuple[str, Optional[str]]:
    """
    Evaluates the user's answer and optionally generates the next question.
    Ensures feedback and next_question are always present.
    """
    if USE_MOCK_API:
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
        previous_answers=st.session_state.answers[:index+1],
        previous_questions=st.session_state.questions,  
        difficulty=st.session_state.difficulty,         
        question_type=st.session_state.question_type,
    )

    logger.info(f"[DEBUG] Evaluation prompt:\n{prompt_text}")
    logger.info(f"[DEBUG] User answer:\n{user_answer}")

    # Structured JSON schema for response
    response_format = {
        "format": {
            "type": "json_schema",
            "name": "evaluation_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "feedback": {"type": "string"},
                    "next_question": {"type": ["string", "null"]}
                },
                "required": ["feedback", "next_question"],
                "additionalProperties": False
            }
        }
    }

    raw_response = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
        temperature=0.4,
        structured_output=response_format
    )
    
    # Always ensure keys exist
    try:
        data = json.loads(raw_response)
        feedback = data.get("feedback", "No feedback returned.")
        next_question = data.get("next_question") or None
    except Exception as e:
        logger.error(f"Failed to parse evaluation JSON: {e}")
        feedback = "Error parsing model response."
        next_question = None

    # If model didn’t propose a next question, optionally generate one:
    if not next_question:
        next_question = generate_next_question()

    return feedback, next_question

@handle_errors(default="Could not generate question. Please try again.")
def generate_next_question() -> str:
    """
    Generates the next interview question using the selected prompt technique.
    Uses structured JSON output for more reliable parsing.
    """
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
                "properties": {
                    "question": {"type": "string", "minLength": 1}
                },
                "required": ["question"],
                "additionalProperties": False
            }
        }
    }

    # --- Call the model ---
    response = openai_call(
        sys_instructions=sys_instructions,
        prompt_text=prompt_text,
        temperature=0.3,
        structured_output=structured_output
    )

    # --- Parse JSON safely ---
    if response:
        try:
            data = json.loads(response)
            return data.get("question", "Could not generate question. Please try again.")
        except Exception as e:
            logger.error(f"Failed to parse question JSON: {e}")
            # fallback to raw response
            return response

    return "Could not generate question. Please try again."

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
    sys_instructions = load_prompt(SYSTEM_PROMPTS["summary_generator"])

    # --- Build developer/user prompt dynamically ---
    questions_and_answers = list(zip(
        st.session_state.questions,
        st.session_state.answers
    ))

    # Render prompt using base + technique
    prompt_text = build_prompt(
        category="summary",
        base_instructions=BASE_PROMPTS["summary"],
        technique=ACTIVE_SUMMARY_TECHNIQUE,
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