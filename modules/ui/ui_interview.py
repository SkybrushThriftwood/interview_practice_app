"""
ui_interview.py

Streamlit UI for the Interview Practice App.
Renders interview questions, collects answers, provides feedback, and shows summary.
"""

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


def render_interview_ui() -> None:
    """
    Render the main interview UI in Streamlit.
    """
    # --- Sidebar ---
    job_title, question_type, difficulty, should_restart = display_sidebar()
    if should_restart:
        handle_sidebar_restart()
        logger.info("Sidebar restart triggered. Feedbacks reset.")

    # --- Header ---
    st.header(f"Interview Practice for: {st.session_state.job_title}")
    st.write(
        f"Question Type: **{st.session_state.question_type}**, "
        f"Difficulty: **{st.session_state.difficulty}**"
    )

    # --- Evaluation Style Dropdown ---
    if "evaluation_style" not in st.session_state:
        st.session_state.evaluation_style = "Hiring Manager"

    selected_persona = st.selectbox(
        "Choose feedback style:",
        options=list(EVALUATION_PERSONAS.keys()),
        index=list(EVALUATION_PERSONAS.keys()).index(st.session_state.evaluation_style),
    )
    st.info(EVALUATION_PERSONAS[selected_persona], icon="ℹ️")
    st.session_state.evaluation_style = selected_persona

    # --- Initialize session lists ---
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("answers", [])
    st.session_state.setdefault("feedbacks", [])
    st.session_state.setdefault("current_question_index", 0)

    # --- Generate first question if needed ---
    if st.session_state.get("started", False) and len(st.session_state.questions) == 0:
        first_question = generate_next_question()
        st.session_state.questions.append(first_question)
        logger.info("First question generated.")

    # --- Chat Container ---
    chat_container = st.container()
    with chat_container:

        # Render previous Q/A + feedback
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}: {q}**")
            if i < len(st.session_state.answers):
                st.markdown(f"**A{i+1}:** {st.session_state.answers[i]}")
            if i < len(st.session_state.feedbacks):
                st.markdown(f"**Feedback:** {st.session_state.feedbacks[i]}")

        # Current question input + buttons
        current_index = st.session_state.current_question_index

        if current_index < len(st.session_state.questions):
            answer_key = f"answer_{current_index}"
            user_answer = st.text_area(
                f"Your answer for Q{current_index+1}:",
                key=answer_key
            )

            # --- Buttons ---
            col_submit, spacer, col_finish = st.columns([1, 5, 1])

            with col_submit:
                submit_key = f"submit_{current_index}"
                submit_disabled = len(user_answer.strip()) == 0

                if st.button("Submit Answer", key=submit_key, disabled=submit_disabled):
                    feedback, next_question = evaluate_answer_and_generate_next(user_answer)

                    st.session_state.answers.append(user_answer)
                    st.session_state.feedbacks.append(feedback)

                    if next_question:
                        st.session_state.questions.append(next_question)

                    st.session_state.current_question_index += 1
                    logger.info("Answer submitted and next question generated.")
                    st.rerun()

            with col_finish:
                if st.button("Finish Interview"):
                    raw_summary = generate_interview_summary()
                    st.session_state["interview_finished"] = True
                    st.session_state["raw_summary"] = raw_summary
                    logger.info("Interview finished. Summary generated.")
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

    # --- Summary ---
    if st.session_state.get("interview_finished", False):
        st.info("Interview completed. See your summary below.")

        summary_text, recommendations = parse_summary(
            st.session_state.get("raw_summary", "")
        )

        st.subheader("Interview Summary")
        st.text_area("Overall Summary", value=summary_text, height=150)

        st.subheader("Recommendations")
        for i, rec in enumerate(recommendations, start=1):
            st.write(f"{i}. {rec}")

    # --- Token + Cost tracking ---
    render_token_usage_box()

def render_token_usage_box():
    st.markdown("---")
    st.subheader("Token Usage & Cost (Live)")
    
    input_tokens = st.session_state.get("input_tokens_total", 0)
    output_tokens = st.session_state.get("output_tokens_total", 0)
    cost = st.session_state.get("cost_so_far", 0.0)

    st.markdown(
        f"""
        **Input tokens:** {input_tokens:,}  
        **Output tokens:** {output_tokens:,}  
        **Total cost:** **${cost:.5f}**
        """
    )