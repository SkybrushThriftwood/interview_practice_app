import streamlit as st
from modules.config import EVALUATION_PERSONAS
from modules.ui.ui_sidebar import display_sidebar, handle_sidebar_restart
from modules.interview_logic import (
    evaluate_answer_and_generate_next,
    generate_interview_summary,
    parse_summary
)
import logging

logger = logging.getLogger(__name__)

def render_interview_ui():
    # --- Sidebar ---
    job_title, question_type, difficulty, should_restart = display_sidebar()
    if should_restart:
        handle_sidebar_restart()

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

    # Update session state with selected persona
    st.session_state.evaluation_style = selected_persona

    # --- Chat Container ---
    chat_container = st.container()
    with chat_container:
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}: {q}**")
            if i < len(st.session_state.answers):
                st.markdown(f"**A{i+1}:** {st.session_state.answers[i]}")
            if i < len(st.session_state.feedbacks):
                st.markdown(f"**Feedback:** {st.session_state.feedbacks[i]}")
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

    # --- Check if interview is finished ---
    if st.session_state.get("interview_finished", False):
        st.info("Interview completed. See your summary below.")
        raw_summary = st.session_state.get("raw_summary", "")
        summary_text, recommendations = parse_summary(raw_summary)

        st.subheader("Interview Summary")
        st.text_area("Overall Summary", value=summary_text, height=150)

        st.subheader("Recommendations")
        for i, rec in enumerate(recommendations, start=1):
            st.write(f"{i}. {rec}")

        return  # Stop further answering

    # --- Answer Input ---
    answer_key = f"answer_input_{st.session_state.current_question_index}"
    initial_value = st.session_state.get(answer_key, "")
    user_answer = st.text_area("Your Answer", value=initial_value, key=answer_key, height=100) or ""

    # --- Submit Answer ---
    if st.button("Submit Answer"):
        if not user_answer.strip():
            st.error("Please enter an answer before submitting.")
        else:
            feedback, next_question = evaluate_answer_and_generate_next(user_answer)
            st.session_state.answers.append(user_answer)
            st.session_state.feedbacks.append(feedback)
            st.session_state.current_question_index += 1
            if next_question:
                st.session_state.questions.append(next_question)

            st.markdown(f"**Feedback ({st.session_state.evaluation_style}):** {feedback}")
            logger.info(f"Answer for Q{st.session_state.current_question_index}: {user_answer}")
            logger.info(f"Feedback: {feedback}")
            st.rerun()

    # --- Finish Interview Button ---
    if st.button("Finish Interview"):
        raw_summary = generate_interview_summary()
        st.session_state["interview_finished"] = True
        st.session_state["raw_summary"] = raw_summary
        st.rerun()
