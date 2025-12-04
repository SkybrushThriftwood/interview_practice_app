"""
ui_helpers.py

Provides helper functions for rendering input controls in the Streamlit interview UI.
Includes job title input, question type dropdown, and difficulty level dropdown.
"""

import streamlit as st
from modules.config import OPENAI_MODELS

def advanced_settings_ui(use_sidebar: bool = False):
    """
    Displays advanced OpenAI parameters that the user can tune before starting the interview.
    Values are saved in session_state.
    """
    container = st.sidebar.expander("Advanced AI Settings (optional)", expanded=False) \
        if use_sidebar else st.expander("Advanced AI Settings (optional)", expanded=False)
    
    with container:
        # Model selection
        st.session_state.model = st.selectbox(
            "Model",
            options=OPENAI_MODELS,
            index=OPENAI_MODELS.index(st.session_state.get("model", OPENAI_MODELS[0])),
        help="The model used to generate questions and feedback. More powerful models are slower but higher quality."
        )
        
        # Temperature
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("temperature", 0.2),
            step=0.05,
            help="Controls creativity. Lower = safe and predictable answers, higher = more creative and varied answers."
        )

        # Max tokens
        st.session_state.max_tokens_eval = st.number_input(
            "Max Tokens",
            min_value=1,
            max_value=2000,
            value=st.session_state.get("max_tokens_eval", 250),
            step=10,
            help="Maximum length of the AI's response. Bigger = longer answers."
        )

def display_job_title_input() -> str:
    """
    Displays the job title input with validation feedback.

    Returns:
        str: The current value of the job title input.
    """
    job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer")
    if st.session_state.get('job_error'):
        st.markdown(
            f"<span style='color: red;'>{st.session_state.job_error}</span>",
            unsafe_allow_html=True
        )
    st.write("Enter the job title for which you want to practice an interview.")
    return job_title


def display_question_type_dropdown() -> str:
    """
    Displays the question type dropdown with explanatory text.

    Returns:
        str: The selected question type.
    """
    question_type = st.selectbox(
        "Question Type",
        ["Behavioral", "Role-specific", "Technical"]
    )
    st.write("""
    **Behavioral:** Questions about your experience, problem-solving, teamwork.  
    **Role-specific:** Questions tailored to your job role and responsibilities.  
    **Technical:** Questions testing your technical knowledge and skills.
    """)
    return question_type


def display_difficulty_dropdown() -> str:
    """
    Displays the difficulty level dropdown with explanatory text.

    Returns:
        str: The selected difficulty level.
    """
    difficulty = st.selectbox(
        "Difficulty Level",
        ["Easy", "Medium", "Hard"]
    )
    st.write("""
    **Easy:** Basic questions, suitable for beginners.  
    **Medium:** Moderate complexity, some problem-solving required.  
    **Hard:** Advanced questions, challenging scenarios.  
    """)
    return difficulty
