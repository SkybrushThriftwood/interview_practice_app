import streamlit as st
from modules.config import EVALUATION_PERSONAS
from modules.ui.ui_sidebar import display_sidebar, handle_sidebar_restart
from modules.interview_logic import (
    evaluate_answer_and_generate_next,
    generate_interview_summary,
    parse_summary,
    generate_next_question
)
import logging

logger = logging.getLogger(__name__)

def render_interview_ui():

    
    # --- Sidebar ---
    job_title, question_type, difficulty, should_restart = display_sidebar()
    if should_restart:
        handle_sidebar_restart()
        logger.info(f"Current feedbacks: {st.session_state.get('feedbacks')}")
    # --- Header ---
    st.header(f"Interview Practice for: {st.session_state.job_title}")
    st.write(f"Question Type: **{st.session_state.question_type}**, Difficulty: **{st.session_state.difficulty}**")

    # --- Evaluation Style Dropdown ---
    if "evaluation_style" not in st.session_state:
        st.session_state.evaluation_style = "Hiring Manager"  # default

    selected_persona = st.selectbox(
        "Choose feedback style:",
        options=list(EVALUATION_PERSONAS.keys()),
        index=list(EVALUATION_PERSONAS.keys()).index(st.session_state.evaluation_style)
    )
    st.info(EVALUATION_PERSONAS[selected_persona], icon="ℹ️")
    st.session_state.evaluation_style = selected_persona

    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "answers" not in st.session_state:
        st.session_state.answers = []
    if "feedbacks" not in st.session_state:
        st.session_state.feedbacks = []
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0

    # --- Generate first question if none exist ---
    if st.session_state.started and len(st.session_state.questions) == 0:
        first_question = generate_next_question()
        st.session_state.questions.append(first_question)
        logger.info(f"First question generated: {first_question!r}")

    # --- Chat Container ---
    chat_container = st.container()
    with chat_container:
        # Render all previous questions + answers + feedback
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}: {q}**")
            if i < len(st.session_state.answers):
                st.markdown(f"**A{i+1}:** {st.session_state.answers[i]}")
            if i < len(st.session_state.feedbacks):
                st.markdown(f"**Feedback:** {st.session_state.feedbacks[i]}")

        # Input for the current question
        current_index = st.session_state.current_question_index
        if current_index < len(st.session_state.questions):
            answer_key = f"answer_{current_index}"
            user_answer = st.text_area(
                f"Your answer for Q{current_index+1}:",
                key=answer_key
            )
            submit_key = f"submit_{current_index}"
            if st.button("Submit", key=submit_key):
                # Evaluate answer and generate next question
                feedback, next_question = evaluate_answer_and_generate_next(user_answer)
                
                # Append answer and feedback
                st.session_state.answers.append(user_answer)
                st.session_state.feedbacks.append(feedback)
                
                # Append next question if returned
                if next_question:
                    st.session_state.questions.append(next_question)
                
                # Move to next question
                st.session_state.current_question_index += 1
                
                # Force UI rerun to show the new question immediately
                st.rerun()

    # --- Scroll to bottom ---
    st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)
    st.markdown("""
        <script>
        setTimeout(function() {
            const bottom = document.getElementById('bottom');
            if (bottom) {
                bottom.scrollIntoView({behavior: "smooth"});
            }
        }, 100);
        </script>
    """, unsafe_allow_html=True)

    # --- Finish Interview ---
    if st.button("Finish Interview"):
        raw_summary = generate_interview_summary()
        st.session_state["interview_finished"] = True
        st.session_state["raw_summary"] = raw_summary
        st.rerun()

    # --- Show summary if finished ---
    if st.session_state.get("interview_finished", False):
        st.info("Interview completed. See your summary below.")
        summary_text, recommendations = parse_summary(st.session_state.get("raw_summary", ""))

        st.subheader("Interview Summary")
        st.text_area("Overall Summary", value=summary_text, height=150)

        st.subheader("Recommendations")
        for i, rec in enumerate(recommendations, start=1):
            st.write(f"{i}. {rec}")
