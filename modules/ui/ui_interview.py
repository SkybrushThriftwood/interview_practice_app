import streamlit as st
from modules.ui.ui_sidebar import display_sidebar, handle_sidebar_restart
from modules.interview_logic import evaluate_answer_and_generate_next
import logging

logger = logging.getLogger(__name__)

def render_interview_ui():
    # Sidebar
    job_title, question_type, difficulty, should_restart = display_sidebar()
    if should_restart:
        handle_sidebar_restart()

    # Main interview content
    st.header(f"Interview Practice for: {st.session_state.job_title}")
    st.write(f"Question Type: **{st.session_state.question_type}**, Difficulty: **{st.session_state.difficulty}**")

    # Chat container
    chat_container = st.container()
    with chat_container:
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}: {q}**")
            if i < len(st.session_state.answers):
                st.markdown(f"**A{i+1}:** {st.session_state.answers[i]}")
            if i < len(st.session_state.feedbacks):
                st.markdown(f"**Feedback:** {st.session_state.feedbacks[i]}")
        st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)
    st.markdown('<script>document.getElementById("bottom").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)

    # Answer input
    answer_key = f"answer_input_{st.session_state.current_question_index}"
    initial_value = st.session_state.get(answer_key, "")
    user_answer = st.text_area("Your Answer", value=initial_value, key=answer_key, height=100) or ""

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
            st.markdown(f"**Feedback:** {feedback}")
            logger.info(f"Answer for Q{st.session_state.current_question_index}: {user_answer}")
            logger.info(f"Feedback: {feedback}")
            st.rerun()
