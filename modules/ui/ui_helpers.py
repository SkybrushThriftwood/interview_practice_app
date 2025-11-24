import streamlit as st



def display_job_title_input():
    """Displays the job title input with validation."""
    job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer")
    if st.session_state.get('job_error'):
        st.markdown(
            f"<span style='color: red;'>{st.session_state.job_error}</span>", 
            unsafe_allow_html=True
        )
    st.write("Enter the job title for which you want to practice an interview.")
    return job_title


def display_question_type_dropdown():
    """Displays the question type dropdown."""
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


def display_difficulty_dropdown():
    """Displays the difficulty level dropdown."""
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


