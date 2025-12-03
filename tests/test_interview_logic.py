import pytest  # noqa: F401
import streamlit as st
from modules.interview_logic import generate_next_question, evaluate_answer_and_generate_next

def test_generate_next_question():
    question = generate_next_question()
    assert isinstance(question, str)
    assert len(question) > 0

def test_evaluate_answer_and_generate_next():
    # Initialize required session state keys
    st.session_state.questions = ["Sample question?"]
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.current_question_index = 0
    st.session_state.evaluation_style = "Hiring Manager"
    st.session_state.job_title = "Software Engineer"
    st.session_state.difficulty = "Medium"  # <-- NEW
    st.session_state.question_type = "Behavioral"  # <-- maybe required as well

    feedback, next_question = evaluate_answer_and_generate_next("This is my answer")

    assert isinstance(feedback, str)
    assert isinstance(next_question, str) or next_question is None
